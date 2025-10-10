#!/usr/bin/env python3
"""
BrainOps AI OS - Environment Variable Registry Scanner
Version: 1.0.0
Scans all repositories for environment variable usage and populates the registry
"""

import os
import re
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

# Database configuration
DB_CONFIG = {
    'host': 'aws-0-us-east-2.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.yomagoqdmxszqtdwuhab',
    'password': 'Brain0ps2O2S'
}

# Repository paths to scan
REPO_PATHS = [
    '/home/mwwoodworth/code/fastapi-operator-env',
    '/home/mwwoodworth/code/myroofgenius-app',
    '/home/mwwoodworth/code/weathercraft-erp',
    '/home/mwwoodworth/code/brainops-ai-assistant',
    '/home/mwwoodworth/code/brainops-task-os'
]

# Patterns to find environment variable usage
ENV_PATTERNS = {
    'python': [
        r'os\.environ\.get\([\'"]([A-Z_][A-Z0-9_]*)[\'"]',
        r'os\.environ\[[\'"]([A-Z_][A-Z0-9_]*)[\'"]',
        r'os\.getenv\([\'"]([A-Z_][A-Z0-9_]*)[\'"]',
        r'ENV\[[\'"]([A-Z_][A-Z0-9_]*)[\'"]',
        r'settings\.([A-Z_][A-Z0-9_]*)',
    ],
    'javascript': [
        r'process\.env\.([A-Z_][A-Z0-9_]*)',
        r'process\.env\[[\'"]([A-Z_][A-Z0-9_]*)[\'"]',
        r'import\.meta\.env\.([A-Z_][A-Z0-9_]*)',
    ],
    'typescript': [
        r'process\.env\.([A-Z_][A-Z0-9_]*)',
        r'process\.env\[[\'"]([A-Z_][A-Z0-9_]*)[\'"]',
        r'import\.meta\.env\.([A-Z_][A-Z0-9_]*)',
    ],
    'env_file': [
        r'^([A-Z_][A-Z0-9_]*)\s*=',
    ]
}

# File extensions to scan
FILE_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.env': 'env_file',
    '.env.example': 'env_file',
    '.env.local': 'env_file',
    '.env.production': 'env_file',
    '.env.development': 'env_file',
}

# Known sensitive keys that should be encrypted
SENSITIVE_KEYS = {
    'PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'PRIVATE', 'CREDENTIAL',
    'AUTH', 'API_KEY', 'ACCESS_KEY', 'SALT', 'HASH'
}

class EnvVarScanner:
    def __init__(self):
        self.env_vars: Dict[str, Dict] = {}
        self.conn = None
        
    def connect_db(self):
        """Connect to the database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def scan_file(self, file_path: Path, repo_name: str) -> Set[Tuple[str, str]]:
        """Scan a single file for environment variables"""
        env_vars = set()
        
        try:
            ext = file_path.suffix
            if ext not in FILE_EXTENSIONS:
                return env_vars
            
            lang = FILE_EXTENSIONS[ext]
            patterns = ENV_PATTERNS.get(lang, [])
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, str):
                        env_vars.add((match, str(file_path)))
        
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
        
        return env_vars
    
    def scan_repository(self, repo_path: str) -> Dict[str, Set[str]]:
        """Scan a repository for all environment variables"""
        repo_name = os.path.basename(repo_path)
        print(f"\nScanning repository: {repo_name}")
        
        repo_vars = {}
        
        # Skip node_modules, venv, .git, etc.
        skip_dirs = {'.git', 'node_modules', 'venv', '.venv', 'dist', 'build', '__pycache__'}
        
        for root, dirs, files in os.walk(repo_path):
            # Remove skip directories from traversal
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                file_path = Path(root) / file
                env_vars = self.scan_file(file_path, repo_name)
                
                for var_name, source_file in env_vars:
                    if var_name not in repo_vars:
                        repo_vars[var_name] = set()
                    repo_vars[var_name].add(source_file)
        
        return repo_vars
    
    def determine_scope(self, var_name: str, repos_using: Set[str]) -> str:
        """Determine the scope of an environment variable"""
        if len(repos_using) > 2:
            return 'global'
        elif len(repos_using) == 1:
            return 'service'
        else:
            return 'env'
    
    def is_sensitive(self, var_name: str) -> bool:
        """Check if a variable name suggests sensitive data"""
        upper_name = var_name.upper()
        return any(keyword in upper_name for keyword in SENSITIVE_KEYS)
    
    def determine_data_type(self, var_name: str) -> str:
        """Guess the data type based on variable name"""
        upper_name = var_name.upper()
        
        if self.is_sensitive(upper_name):
            return 'secret'
        elif 'URL' in upper_name or 'ENDPOINT' in upper_name:
            return 'url'
        elif 'PORT' in upper_name or 'COUNT' in upper_name or 'SIZE' in upper_name:
            return 'number'
        elif 'ENABLE' in upper_name or 'DISABLE' in upper_name or 'IS_' in upper_name:
            return 'boolean'
        elif 'JSON' in upper_name or 'CONFIG' in upper_name:
            return 'json'
        else:
            return 'string'
    
    def scan_all_repositories(self):
        """Scan all configured repositories"""
        all_vars = {}
        
        for repo_path in REPO_PATHS:
            if not os.path.exists(repo_path):
                print(f"Repository not found: {repo_path}")
                continue
            
            repo_name = os.path.basename(repo_path)
            repo_vars = self.scan_repository(repo_path)
            
            for var_name, sources in repo_vars.items():
                if var_name not in all_vars:
                    all_vars[var_name] = {
                        'repos': set(),
                        'sources': set()
                    }
                all_vars[var_name]['repos'].add(repo_name)
                all_vars[var_name]['sources'].update(sources)
            
            print(f"  Found {len(repo_vars)} unique variables")
        
        return all_vars
    
    def load_existing_values(self):
        """Load existing .env files to get current values"""
        env_values = {}
        
        env_files = [
            '/home/mwwoodworth/code/fastapi-operator-env/.env',
            '/home/mwwoodworth/code/myroofgenius-app/.env.local',
            '/home/mwwoodworth/code/weathercraft-erp/.env.local',
        ]
        
        for env_file in env_files:
            if os.path.exists(env_file):
                print(f"Loading values from {env_file}")
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key and key not in env_values:
                                env_values[key] = value
        
        return env_values
    
    def store_in_registry(self, all_vars: Dict):
        """Store discovered environment variables in the database"""
        if not self.conn:
            print("No database connection")
            return
        
        cursor = self.conn.cursor()
        existing_values = self.load_existing_values()
        
        stored_count = 0
        updated_count = 0
        
        for var_name, info in all_vars.items():
            repos = list(info['repos'])
            sources = list(info['sources'])
            
            scope = self.determine_scope(var_name, info['repos'])
            data_type = self.determine_data_type(var_name)
            is_sensitive = self.is_sensitive(var_name)
            
            # Get current value if available
            current_value = existing_values.get(var_name)
            
            # Prepare the data
            key = var_name
            # Ensure we have either value or encrypted_value (not both null)
            if is_sensitive:
                value = None
                # For now, store sensitive values as encrypted placeholder
                encrypted_value = b'ENCRYPTED_PLACEHOLDER'  # TODO: Implement real encryption
            else:
                value = current_value if current_value else 'PLACEHOLDER'
                encrypted_value = None
            service_name = repos[0] if len(repos) == 1 else None
            description = f"Found in {len(repos)} repositories: {', '.join(repos[:3])}"
            source_ref = json.dumps(sources[:5])  # Store first 5 source files
            
            # Check if already exists
            cursor.execute("""
                SELECT id FROM core.env_registry 
                WHERE key = %s AND scope = %s AND COALESCE(service_name, '') = COALESCE(%s, '')
            """, (key, scope, service_name))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                cursor.execute("""
                    UPDATE core.env_registry 
                    SET last_verified_at = NOW(),
                        last_verified_by = 'scanner',
                        source_ref = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (source_ref, existing[0]))
                updated_count += 1
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO core.env_registry 
                    (key, value, encrypted_value, scope, service_name, description, 
                     data_type, required, source_ref, last_verified_at, last_verified_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), 'scanner')
                """, (key, value, encrypted_value, scope, service_name, description, 
                      data_type, True, source_ref))
                stored_count += 1
        
        self.conn.commit()
        print(f"\nStored {stored_count} new variables, updated {updated_count} existing")
    
    def generate_report(self, all_vars: Dict):
        """Generate a report of discovered environment variables"""
        print("\n" + "="*60)
        print("ENVIRONMENT VARIABLE REGISTRY REPORT")
        print("="*60)
        
        total_vars = len(all_vars)
        print(f"\nTotal unique variables found: {total_vars}")
        
        # Group by repository
        repo_counts = {}
        for var_name, info in all_vars.items():
            for repo in info['repos']:
                if repo not in repo_counts:
                    repo_counts[repo] = 0
                repo_counts[repo] += 1
        
        print("\nVariables per repository:")
        for repo, count in sorted(repo_counts.items()):
            print(f"  {repo}: {count}")
        
        # Identify global variables (used in multiple repos)
        global_vars = {k: v for k, v in all_vars.items() if len(v['repos']) > 1}
        print(f"\nGlobal variables (used in multiple repos): {len(global_vars)}")
        for var_name, info in sorted(global_vars.items())[:10]:
            repos = ', '.join(sorted(info['repos']))
            print(f"  {var_name}: {repos}")
        
        # Identify sensitive variables
        sensitive_vars = [k for k in all_vars.keys() if self.is_sensitive(k)]
        print(f"\nSensitive variables requiring encryption: {len(sensitive_vars)}")
        for var_name in sorted(sensitive_vars)[:10]:
            print(f"  {var_name}")
        
        # Missing values
        existing_values = self.load_existing_values()
        missing_vars = [k for k in all_vars.keys() if k not in existing_values]
        print(f"\nVariables without values in .env files: {len(missing_vars)}")
        for var_name in sorted(missing_vars)[:10]:
            print(f"  {var_name}")
    
    def generate_env_template(self, repo_path: str):
        """Generate .env.template file for a repository"""
        repo_name = os.path.basename(repo_path)
        template_path = Path(repo_path) / '.env.template'
        
        if not self.conn:
            print("No database connection")
            return
        
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get variables for this service
        cursor.execute("""
            SELECT key, description, data_type, required, default_value
            FROM core.env_registry
            WHERE (service_name = %s OR scope = 'global')
            AND deprecated_at IS NULL
            ORDER BY required DESC, key
        """, (repo_name,))
        
        vars = cursor.fetchall()
        
        with open(template_path, 'w') as f:
            f.write("# Environment Variables Template\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Service: {repo_name}\n\n")
            
            # Required variables
            f.write("# REQUIRED VARIABLES\n")
            f.write("# ==================\n\n")
            for var in vars:
                if var['required']:
                    f.write(f"# {var['description'] or 'No description'}\n")
                    f.write(f"# Type: {var['data_type']}\n")
                    f.write(f"{var['key']}=\n\n")
            
            # Optional variables
            f.write("\n# OPTIONAL VARIABLES\n")
            f.write("# ==================\n\n")
            for var in vars:
                if not var['required']:
                    f.write(f"# {var['description'] or 'No description'}\n")
                    f.write(f"# Type: {var['data_type']}\n")
                    if var['default_value']:
                        f.write(f"# Default: {var['default_value']}\n")
                    f.write(f"# {var['key']}=\n\n")
        
        print(f"Generated template: {template_path}")
    
    def run(self):
        """Main execution method"""
        print("BrainOps Environment Variable Registry Scanner")
        print("=" * 50)
        
        # Connect to database
        if not self.connect_db():
            print("Failed to connect to database")
            return
        
        # Scan all repositories
        all_vars = self.scan_all_repositories()
        
        # Generate report
        self.generate_report(all_vars)
        
        # Store in registry
        self.store_in_registry(all_vars)
        
        # Generate templates for each repo
        for repo_path in REPO_PATHS:
            if os.path.exists(repo_path):
                self.generate_env_template(repo_path)
        
        # Close connection
        if self.conn:
            self.conn.close()
        
        print("\nScan complete!")

if __name__ == "__main__":
    scanner = EnvVarScanner()
    scanner.run()