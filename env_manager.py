"""
Environment Variable Manager - Master tracking in database
All environment variables are documented and tracked in Supabase
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
import asyncpg
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://yomagoqdmxszqtdwuhab.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class EnvironmentManager:
    """
    Master environment variable management system
    Stores all env vars in database for permanent tracking
    """
    
    def __init__(self):
        self.supabase = supabase
        self.cipher = Fernet(os.getenv("FERNET_SECRET", Fernet.generate_key()))
        
        # Initialize database tables
        asyncio.create_task(self._initialize_tables())
        
        # Load and sync environment variables
        asyncio.create_task(self._sync_environment())
    
    async def _initialize_tables(self):
        """Create environment management tables"""
        try:
            conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
            
            # Master environment variables table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS environment_variables (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    key VARCHAR(255) UNIQUE NOT NULL,
                    value TEXT,  -- Encrypted for sensitive values
                    description TEXT,
                    category VARCHAR(100),
                    service VARCHAR(100),  -- Which service uses this
                    is_sensitive BOOLEAN DEFAULT FALSE,
                    is_required BOOLEAN DEFAULT TRUE,
                    default_value TEXT,
                    validation_regex TEXT,
                    last_rotated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_env_key ON environment_variables(key);
                CREATE INDEX IF NOT EXISTS idx_env_service ON environment_variables(service);
                CREATE INDEX IF NOT EXISTS idx_env_category ON environment_variables(category);
            ''')
            
            # Environment sync status
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS env_sync_status (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    service VARCHAR(100),
                    platform VARCHAR(100),  -- render, vercel, local
                    sync_status VARCHAR(50),
                    variables_count INT,
                    missing_variables JSONB,
                    extra_variables JSONB,
                    last_synced TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            # Environment audit log
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS env_audit_log (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    action VARCHAR(50),  -- create, update, delete, rotate
                    key VARCHAR(255),
                    old_value TEXT,
                    new_value TEXT,
                    changed_by VARCHAR(255),
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                );
            ''')
            
            await conn.close()
            logger.info("Environment tables initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize environment tables: {e}")
    
    async def _sync_environment(self):
        """Sync current environment variables to database"""
        try:
            # Read from BrainOps.env file
            env_file_path = "/home/matt-woodworth/Downloads/BrainOps.env"
            env_vars = {}
            
            if os.path.exists(env_file_path):
                with open(env_file_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            env_vars[key] = value.strip('"')
            
            # Define categories for each variable
            categories = {
                "DATABASE": ["DATABASE_URL", "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "REDIS_URL"],
                "AI": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "GEMINI_API_KEY"],
                "PAYMENT": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE"],
                "COMMUNICATION": ["SENDGRID_API_KEY", "TWILIO_ACCOUNT_SID", "SLACK_WEBHOOK_URL"],
                "MONITORING": ["SENTRY_DSN", "PAPERTRAIL_HOST", "RENDER_API_KEY"],
                "INTEGRATION": ["GITHUB_TOKEN", "CLICKUP_API_KEY", "NOTION_API_KEY"],
                "SECURITY": ["JWT_SECRET", "FERNET_SECRET", "NEXTAUTH_SECRET"],
                "CONFIGURATION": ["ENVIRONMENT", "NODE_ENV", "DEBUG", "PORT"]
            }
            
            # Determine sensitivity
            sensitive_patterns = [
                "KEY", "SECRET", "TOKEN", "PASSWORD", "PASS", "AUTH", "CREDENTIAL"
            ]
            
            # Store each variable
            for key, value in env_vars.items():
                # Determine category
                category = "OTHER"
                for cat, patterns in categories.items():
                    if any(pattern in key for pattern in patterns):
                        category = cat
                        break
                
                # Check if sensitive
                is_sensitive = any(pattern in key.upper() for pattern in sensitive_patterns)
                
                # Encrypt sensitive values
                stored_value = self.cipher.encrypt(value.encode()).decode() if is_sensitive else value
                
                # Determine service
                service = "ALL"
                if "NEXT_PUBLIC" in key:
                    service = "FRONTEND"
                elif "RENDER" in key:
                    service = "BACKEND"
                elif "VERCEL" in key:
                    service = "VERCEL"
                
                # Store in database
                await self.store_variable(
                    key=key,
                    value=stored_value,
                    category=category,
                    service=service,
                    is_sensitive=is_sensitive,
                    description=self._get_description(key)
                )
            
            # Log sync
            self.supabase.table("env_sync_status").insert({
                "service": "MASTER",
                "platform": "DATABASE",
                "sync_status": "COMPLETED",
                "variables_count": len(env_vars),
                "missing_variables": [],
                "extra_variables": []
            }).execute()
            
            logger.info(f"Synced {len(env_vars)} environment variables to database")
            
        except Exception as e:
            logger.error(f"Failed to sync environment: {e}")
    
    async def store_variable(
        self,
        key: str,
        value: str,
        category: str = "OTHER",
        service: str = "ALL",
        is_sensitive: bool = False,
        description: str = ""
    ):
        """Store or update an environment variable"""
        try:
            # Check if exists
            existing = self.supabase.table("environment_variables").select("*").eq("key", key).execute()
            
            if existing.data:
                # Update
                self.supabase.table("environment_variables").update({
                    "value": value,
                    "category": category,
                    "service": service,
                    "is_sensitive": is_sensitive,
                    "description": description,
                    "updated_at": datetime.now().isoformat()
                }).eq("key", key).execute()
                
                # Audit log
                self.supabase.table("env_audit_log").insert({
                    "action": "update",
                    "key": key,
                    "old_value": "***" if is_sensitive else existing.data[0]["value"],
                    "new_value": "***" if is_sensitive else value,
                    "changed_by": "system",
                    "reason": "sync"
                }).execute()
            else:
                # Insert
                self.supabase.table("environment_variables").insert({
                    "key": key,
                    "value": value,
                    "category": category,
                    "service": service,
                    "is_sensitive": is_sensitive,
                    "description": description
                }).execute()
                
                # Audit log
                self.supabase.table("env_audit_log").insert({
                    "action": "create",
                    "key": key,
                    "new_value": "***" if is_sensitive else value,
                    "changed_by": "system",
                    "reason": "initial_sync"
                }).execute()
                
        except Exception as e:
            logger.error(f"Failed to store variable {key}: {e}")
    
    def _get_description(self, key: str) -> str:
        """Get description for environment variable"""
        descriptions = {
            "DATABASE_URL": "PostgreSQL database connection string",
            "SUPABASE_URL": "Supabase project URL",
            "SUPABASE_SERVICE_ROLE_KEY": "Supabase service role key for backend operations",
            "REDIS_URL": "Redis connection string for caching",
            "OPENAI_API_KEY": "OpenAI API key for GPT models",
            "ANTHROPIC_API_KEY": "Anthropic API key for Claude models",
            "STRIPE_SECRET_KEY": "Stripe secret key for payment processing",
            "SENDGRID_API_KEY": "SendGrid API key for email sending",
            "TWILIO_ACCOUNT_SID": "Twilio account SID for SMS",
            "SLACK_WEBHOOK_URL": "Slack webhook for notifications",
            "SENTRY_DSN": "Sentry DSN for error tracking",
            "RENDER_API_KEY": "Render.com API key for deployments",
            "GITHUB_TOKEN": "GitHub personal access token",
            "JWT_SECRET": "Secret key for JWT token signing",
            "ENVIRONMENT": "Current environment (production/staging/development)",
            "PORT": "Application port number"
        }
        return descriptions.get(key, "")
    
    async def get_variable(self, key: str, decrypt: bool = True) -> Optional[str]:
        """Get an environment variable from database"""
        try:
            result = self.supabase.table("environment_variables").select("*").eq("key", key).execute()
            
            if result.data:
                var = result.data[0]
                value = var["value"]
                
                # Decrypt if sensitive and requested
                if var["is_sensitive"] and decrypt:
                    try:
                        value = self.cipher.decrypt(value.encode()).decode()
                    except:
                        pass  # Return encrypted if decryption fails
                
                return value
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get variable {key}: {e}")
            return None
    
    async def get_all_variables(self, service: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        """Get all environment variables"""
        try:
            query = self.supabase.table("environment_variables").select("*")
            
            if service:
                query = query.eq("service", service)
            if category:
                query = query.eq("category", category)
            
            result = query.execute()
            
            variables = []
            for var in result.data:
                # Don't decrypt sensitive values for listing
                variables.append({
                    "key": var["key"],
                    "value": "***" if var["is_sensitive"] else var["value"],
                    "category": var["category"],
                    "service": var["service"],
                    "description": var["description"],
                    "is_sensitive": var["is_sensitive"],
                    "last_updated": var["updated_at"]
                })
            
            return variables
            
        except Exception as e:
            logger.error(f"Failed to get variables: {e}")
            return []
    
    async def rotate_secret(self, key: str, new_value: str):
        """Rotate a secret value"""
        try:
            # Get old value for audit
            old = await self.get_variable(key, decrypt=False)
            
            # Encrypt new value if sensitive
            result = self.supabase.table("environment_variables").select("is_sensitive").eq("key", key).execute()
            
            if result.data and result.data[0]["is_sensitive"]:
                new_value = self.cipher.encrypt(new_value.encode()).decode()
            
            # Update
            self.supabase.table("environment_variables").update({
                "value": new_value,
                "last_rotated": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).eq("key", key).execute()
            
            # Audit log
            self.supabase.table("env_audit_log").insert({
                "action": "rotate",
                "key": key,
                "old_value": "***",
                "new_value": "***",
                "changed_by": "system",
                "reason": "security_rotation"
            }).execute()
            
            logger.info(f"Rotated secret for {key}")
            
        except Exception as e:
            logger.error(f"Failed to rotate secret {key}: {e}")
    
    async def check_missing_variables(self, required_vars: List[str]) -> List[str]:
        """Check for missing required variables"""
        try:
            # Get all stored variables
            result = self.supabase.table("environment_variables").select("key").execute()
            stored_keys = {var["key"] for var in result.data}
            
            # Find missing
            missing = [var for var in required_vars if var not in stored_keys]
            
            if missing:
                # Log to sync status
                self.supabase.table("env_sync_status").insert({
                    "service": "CHECK",
                    "platform": "DATABASE",
                    "sync_status": "MISSING_VARIABLES",
                    "variables_count": len(stored_keys),
                    "missing_variables": missing,
                    "extra_variables": []
                }).execute()
            
            return missing
            
        except Exception as e:
            logger.error(f"Failed to check missing variables: {e}")
            return []
    
    async def export_env_file(self, service: str = "ALL") -> str:
        """Export environment variables as .env file content"""
        try:
            variables = await self.get_all_variables(service=service)
            
            env_content = []
            env_content.append(f"# Environment variables for {service}")
            env_content.append(f"# Generated at {datetime.now().isoformat()}")
            env_content.append("")
            
            # Group by category
            categories = {}
            for var in variables:
                cat = var["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(var)
            
            # Write each category
            for category, vars in sorted(categories.items()):
                env_content.append(f"# {category}")
                for var in sorted(vars, key=lambda x: x["key"]):
                    if var["description"]:
                        env_content.append(f"# {var['description']}")
                    
                    # Get actual value for export
                    actual_value = await self.get_variable(var["key"], decrypt=True)
                    env_content.append(f"{var['key']}={actual_value}")
                env_content.append("")
            
            return "\n".join(env_content)
            
        except Exception as e:
            logger.error(f"Failed to export env file: {e}")
            return ""
    
    async def get_status_report(self) -> Dict:
        """Get complete environment status report"""
        try:
            # Get counts
            total = self.supabase.table("environment_variables").select("count", count="exact").execute()
            
            # Get by category
            categories = {}
            for cat in ["DATABASE", "AI", "PAYMENT", "SECURITY", "OTHER"]:
                count = self.supabase.table("environment_variables").select(
                    "count", count="exact"
                ).eq("category", cat).execute()
                categories[cat] = count.count if count else 0
            
            # Get recent changes
            recent = self.supabase.table("env_audit_log").select("*").order(
                "timestamp", desc=True
            ).limit(10).execute()
            
            # Get sync status
            sync = self.supabase.table("env_sync_status").select("*").order(
                "last_synced", desc=True
            ).limit(1).execute()
            
            return {
                "total_variables": total.count if total else 0,
                "by_category": categories,
                "recent_changes": recent.data if recent.data else [],
                "last_sync": sync.data[0] if sync.data else None,
                "status": "healthy"
            }
            
        except Exception as e:
            logger.error(f"Failed to get status report: {e}")
            return {"status": "error", "message": str(e)}

# Global instance
env_manager = None

def get_env_manager() -> EnvironmentManager:
    """Get singleton environment manager"""
    global env_manager
    if env_manager is None:
        env_manager = EnvironmentManager()
    return env_manager