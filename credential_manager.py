"""
Unified Credential Management System
Loads all credentials from database and makes them available to the application
NO MORE .env FILES - Database is the single source of truth
"""

import asyncpg
import os
import logging
from typing import Dict, Optional
import json

logger = logging.getLogger(__name__)

class CredentialManager:
    """Manages all system credentials from database"""

    def __init__(self, db_pool: asyncpg.Pool = None):
        self.db_pool = db_pool
        self.credentials: Dict[str, str] = {}
        self.initialized = False

    async def initialize(self):
        """Load all credentials from database into memory and environment"""
        if not self.db_pool:
            raise Exception("Database pool required for CredentialManager")

        try:
            async with self.db_pool.acquire() as conn:
                # Load all credentials from master_credentials table
                rows = await conn.fetch("""
                    SELECT key, value, category, service, is_sensitive, notes
                    FROM master_credentials
                    WHERE is_valid = true
                    ORDER BY category, key
                """)

                loaded_count = 0
                sensitive_count = 0

                for row in rows:
                    key = row['key']
                    value = row['value']
                    is_sensitive = row['is_sensitive']

                    # Store in memory
                    self.credentials[key] = value

                    # Set as environment variable for compatibility
                    os.environ[key] = value

                    loaded_count += 1
                    if is_sensitive:
                        sensitive_count += 1
                        logger.info(f"✅ Loaded sensitive credential: {key}")
                    else:
                        logger.info(f"✅ Loaded credential: {key} = {value[:20]}...")

                self.initialized = True
                logger.info(f"🔐 Credential Manager initialized: {loaded_count} credentials loaded ({sensitive_count} sensitive)")

                return {
                    "total_loaded": loaded_count,
                    "sensitive": sensitive_count,
                    "non_sensitive": loaded_count - sensitive_count
                }

        except Exception as e:
            logger.error(f"❌ Failed to initialize CredentialManager: {e}")
            raise

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get credential by key"""
        if not self.initialized:
            logger.warning("⚠️ CredentialManager not initialized, using environment variables")
            return os.environ.get(key, default)

        return self.credentials.get(key, default)

    def get_required(self, key: str) -> str:
        """Get required credential, raise error if missing"""
        value = self.get(key)
        if value is None:
            raise ValueError(f"Required credential '{key}' not found in database or environment")
        return value

    def get_all(self, category: Optional[str] = None) -> Dict[str, str]:
        """Get all credentials, optionally filtered by category"""
        if not self.initialized:
            logger.warning("⚠️ CredentialManager not initialized")
            return {}

        if category:
            # TODO: Add category filtering
            return self.credentials
        return self.credentials

    async def store(self, key: str, value: str, category: str = 'GENERAL',
                   service: str = 'SYSTEM', is_sensitive: bool = True, notes: str = ''):
        """Store new credential in database"""
        if not self.db_pool:
            raise Exception("Database pool required")

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO master_credentials (key, value, category, service, is_sensitive, notes)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value,
                    category = EXCLUDED.category,
                    service = EXCLUDED.service,
                    is_sensitive = EXCLUDED.is_sensitive,
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
            """, key, value, category, service, is_sensitive, notes)

            # Update in-memory cache
            self.credentials[key] = value
            os.environ[key] = value

            logger.info(f"✅ Stored credential: {key}")

    async def rotate(self, key: str, new_value: str):
        """Rotate credential to new value"""
        if not self.db_pool:
            raise Exception("Database pool required")

        async with self.db_pool.acquire() as conn:
            # Update value and set last_rotated
            await conn.execute("""
                UPDATE master_credentials
                SET value = $1,
                    last_rotated = NOW(),
                    last_validated = NOW(),
                    updated_at = NOW()
                WHERE key = $2
            """, new_value, key)

            # Update in-memory cache
            self.credentials[key] = new_value
            os.environ[key] = new_value

            logger.info(f"🔄 Rotated credential: {key}")

    async def validate_all(self):
        """Validate all credentials are accessible"""
        if not self.initialized:
            await self.initialize()

        critical_creds = [
            'DATABASE_PASSWORD',
            'DATABASE_URL',
            'SUPABASE_URL',
            'SUPABASE_ANON_KEY',
            'BACKEND_URL'
        ]

        missing = []
        for cred in critical_creds:
            if cred not in self.credentials:
                missing.append(cred)

        if missing:
            logger.error(f"❌ Missing critical credentials: {missing}")
            return {"valid": False, "missing": missing}
        else:
            logger.info(f"✅ All critical credentials present")
            return {"valid": True, "missing": []}

    def get_database_url(self) -> str:
        """Get database connection URL"""
        return self.get_required('DATABASE_URL')

    def get_backend_url(self) -> str:
        """Get backend API URL"""
        return self.get_required('BACKEND_URL')

    def get_ai_key(self, provider: str) -> Optional[str]:
        """Get AI provider API key"""
        key_map = {
            'anthropic': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'gemini': 'GEMINI_API_KEY'
        }
        key_name = key_map.get(provider.lower())
        if key_name:
            return self.get(key_name)
        return None

    def get_deployment_creds(self, service: str) -> Dict[str, str]:
        """Get deployment credentials for service"""
        if service.lower() == 'docker':
            return {
                'username': self.get('DOCKER_USERNAME'),
                'token': self.get('DOCKER_PAT')
            }
        elif service.lower() == 'render':
            return {
                'api_key': self.get('RENDER_API_KEY'),
                'service_id': self.get('RENDER_SERVICE_ID'),
                'deploy_hook': self.get('RENDER_DEPLOY_HOOK')
            }
        elif service.lower() == 'vercel':
            return {
                'token': self.get('VERCEL_TOKEN')
            }
        return {}

    async def health_check(self) -> Dict:
        """Check credential system health"""
        if not self.initialized:
            return {"status": "not_initialized"}

        validation = await self.validate_all()

        return {
            "status": "healthy" if validation["valid"] else "degraded",
            "initialized": self.initialized,
            "total_credentials": len(self.credentials),
            "validation": validation,
            "timestamp": "NOW()"
        }


# Global instance
_credential_manager: Optional[CredentialManager] = None

def get_credential_manager() -> CredentialManager:
    """Get global credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        raise Exception("CredentialManager not initialized. Call initialize_credential_manager() first")
    return _credential_manager

async def initialize_credential_manager(db_pool: asyncpg.Pool):
    """Initialize global credential manager"""
    global _credential_manager
    _credential_manager = CredentialManager(db_pool)
    await _credential_manager.initialize()
    return _credential_manager


# Convenience functions
def get_credential(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get credential from global manager"""
    try:
        manager = get_credential_manager()
        return manager.get(key, default)
    except Exception as e:
        logger.warning(f"Error getting credential {key}: {e}")
        # Fallback to environment variable
        return os.environ.get(key, default)

def get_required_credential(key: str) -> str:
    """Get required credential from global manager"""
    try:
        manager = get_credential_manager()
        return manager.get_required(key)
    except Exception as e:
        logger.warning(f"Error getting required credential {key}: {e}")
        # Fallback to environment variable
        value = os.environ.get(key)
        if value is None:
            raise ValueError(f"Required credential '{key}' not found")
        return value
