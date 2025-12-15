#!/usr/bin/env python3
"""
Master Environment Credentials Manager
Centralizes all environment variables, validates them, and syncs with database/Notion
"""

import os
import json
import psycopg2
from datetime import datetime
from typing import Dict, Any, List, Optional
import hashlib
import requests
from pathlib import Path

class MasterCredentialsManager:
    """Complete credentials management system"""

    def __init__(self):
        self.env_vars = {}
        self.db_conn = None
        self.notion_token = "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"  # Correct token
        self.errors = []
        self.warnings = []

    def connect_db(self):
        """Connect to production database"""
        try:
            self.db_conn = psycopg2.connect(
                host="aws-0-us-east-2.pooler.supabase.com",
                port="6543",
                database="postgres",
                user="postgres.yomagoqdmxszqtdwuhab",
                password="<DB_PASSWORD_REDACTED>",
                sslmode="require"
            )
            return True
        except Exception as e:
            self.errors.append(f"Database connection failed: {e}")
            return False

    def load_env_file(self, filepath: str):
        """Load environment variables from file"""
        env_vars = {}
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value.strip('"').strip("'")
            self.env_vars = env_vars
            return True
        except Exception as e:
            self.errors.append(f"Failed to load env file: {e}")
            return False

    def validate_credentials(self) -> Dict[str, Any]:
        """Validate all credentials and identify issues"""
        validation = {
            "total": len(self.env_vars),
            "valid": 0,
            "invalid": 0,
            "placeholders": 0,
            "security_issues": [],
            "missing_critical": [],
            "version_mismatches": [],
            "corrections_needed": []
        }

        # Critical variables that must be valid
        critical_vars = [
            "DATABASE_URL", "JWT_SECRET_KEY", "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "NOTION_TOKEN"
        ]

        # Check each variable
        for key, value in self.env_vars.items():
            # Check for placeholders
            if "YOUR_" in value and "_HERE" in value:
                validation["placeholders"] += 1
                validation["invalid"] += 1
                if key in critical_vars:
                    validation["missing_critical"].append(key)

            # Check for empty or default values
            elif value in ["", "null", "undefined", "(if you have it)"]:
                validation["invalid"] += 1
                if key in critical_vars:
                    validation["missing_critical"].append(key)

            # Validate specific credentials
            elif key == "NOTION_TOKEN" and value != self.notion_token:
                validation["corrections_needed"].append({
                    "key": "NOTION_TOKEN",
                    "current": value[:20] + "...",
                    "correct": self.notion_token[:20] + "...",
                    "action": "UPDATE"
                })
                validation["invalid"] += 1

            elif key == "APP_VERSION" and value != "v30.4.0":
                validation["version_mismatches"].append({
                    "key": "APP_VERSION",
                    "render": value,
                    "deployed": "v30.4.0"
                })

            # Check for exposed sensitive data
            elif key in ["EMAIL_PASSWORD", "SMTP_PASSWORD"] and value == "Mww00dw0rth@2O1S$":
                validation["security_issues"].append({
                    "key": key,
                    "issue": "Using sudo password for email",
                    "risk": "HIGH",
                    "recommendation": "Use app-specific password"
                })

            else:
                validation["valid"] += 1

        return validation

    def create_credentials_table(self):
        """Create master credentials table in database"""
        if not self.db_conn:
            return False

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS master_credentials (
            id SERIAL PRIMARY KEY,
            key VARCHAR(255) UNIQUE NOT NULL,
            value TEXT,
            category VARCHAR(100),
            service VARCHAR(100),
            is_sensitive BOOLEAN DEFAULT true,
            is_valid BOOLEAN DEFAULT true,
            last_validated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_rotated TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS credential_audit_log (
            id SERIAL PRIMARY KEY,
            credential_key VARCHAR(255),
            action VARCHAR(50),
            old_value_hash VARCHAR(64),
            new_value_hash VARCHAR(64),
            changed_by VARCHAR(100),
            change_reason TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        try:
            cur = self.db_conn.cursor()
            cur.execute(create_table_sql)
            self.db_conn.commit()
            return True
        except Exception as e:
            self.errors.append(f"Failed to create credentials table: {e}")
            return False

    def categorize_credential(self, key: str) -> tuple:
        """Categorize credential by service and type"""
        categories = {
            "DATABASE": ["DATABASE_URL", "DB_", "SUPABASE_", "POSTGRES_"],
            "AI": ["OPENAI_", "ANTHROPIC_", "GEMINI_", "CLAUDE_", "PERPLEXITY_"],
            "AUTHENTICATION": ["JWT_", "AUTH_", "SECRET_", "PASSWORD"],
            "INTEGRATION": ["NOTION_", "SLACK_", "GITHUB_", "STRIPE_", "CLICKUP_"],
            "MONITORING": ["SENTRY_", "PAPERTRAIL_", "LOG_"],
            "DEPLOYMENT": ["RENDER_", "VERCEL_", "DOCKER_"],
            "COMMUNICATION": ["EMAIL_", "SMTP_", "TWILIO_", "SENDGRID_"],
            "FEATURE_FLAGS": ["ENABLE_", "NEXT_PUBLIC_"]
        }

        for category, patterns in categories.items():
            for pattern in patterns:
                if pattern in key:
                    # Determine service
                    service = key.split('_')[0] if '_' in key else "GENERAL"
                    return category, service

        return "GENERAL", "SYSTEM"

    def sync_to_database(self):
        """Sync all credentials to database"""
        if not self.db_conn:
            return False

        synced = 0
        failed = 0

        for key, value in self.env_vars.items():
            category, service = self.categorize_credential(key)
            is_sensitive = any(word in key.upper() for word in
                             ["KEY", "SECRET", "PASSWORD", "TOKEN"])

            # Hash sensitive values for audit log
            value_hash = hashlib.sha256(value.encode()).hexdigest() if is_sensitive else None

            try:
                cur = self.db_conn.cursor()

                # Upsert credential
                cur.execute("""
                    INSERT INTO master_credentials (key, value, category, service, is_sensitive)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET value = EXCLUDED.value,
                        category = EXCLUDED.category,
                        service = EXCLUDED.service,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (key, value, category, service, is_sensitive))

                # Log the change
                cur.execute("""
                    INSERT INTO credential_audit_log
                    (credential_key, action, new_value_hash, changed_by, change_reason)
                    VALUES (%s, %s, %s, %s, %s)
                """, (key, "SYNC", value_hash, "MasterCredentialsManager", "Bulk sync from Render"))

                synced += 1

            except Exception as e:
                failed += 1
                self.errors.append(f"Failed to sync {key}: {e}")

        self.db_conn.commit()
        return {"synced": synced, "failed": failed}

    def sync_to_notion(self):
        """Sync credentials documentation to Notion"""
        headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        # Create a page with all credentials documentation
        page_data = {
            "parent": {"type": "workspace"},
            "properties": {
                "title": {
                    "title": [{
                        "text": {
                            "content": f"Master Credentials - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    }]
                }
            },
            "children": []
        }

        # Group by category
        categories = {}
        for key, value in self.env_vars.items():
            cat, _ = self.categorize_credential(key)
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "key": key,
                "configured": "YOUR_" not in value and value != "",
                "service": self.categorize_credential(key)[1]
            })

        # Add sections for each category
        for category, creds in categories.items():
            page_data["children"].append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": category}}]
                }
            })

            # Add table of credentials
            table_rows = []
            for cred in creds:
                status = "✅" if cred["configured"] else "❌"
                table_rows.append(f"| {cred['key']} | {cred['service']} | {status} |")

            if table_rows:
                page_data["children"].append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "text": {
                                "content": "| Key | Service | Status |\n|---|---|---|\n" + "\n".join(table_rows)
                            }
                        }]
                    }
                })

        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=page_data
            )
            if response.status_code == 200:
                return True
            else:
                self.errors.append(f"Notion sync failed: {response.text}")
                return False
        except Exception as e:
            self.errors.append(f"Notion sync error: {e}")
            return False

    def generate_report(self) -> str:
        """Generate comprehensive credentials report"""
        validation = self.validate_credentials()

        report = f"""
# MASTER CREDENTIALS REPORT
Generated: {datetime.now()}

## Summary
- Total Variables: {validation['total']}
- Valid: {validation['valid']}
- Invalid: {validation['invalid']}
- Placeholders: {validation['placeholders']}

## Critical Issues
"""

        if validation['missing_critical']:
            report += "\n### Missing Critical Variables:\n"
            for var in validation['missing_critical']:
                report += f"- ❌ {var}\n"

        if validation['security_issues']:
            report += "\n### Security Issues:\n"
            for issue in validation['security_issues']:
                report += f"- ⚠️ {issue['key']}: {issue['issue']} (Risk: {issue['risk']})\n"

        if validation['corrections_needed']:
            report += "\n### Corrections Needed:\n"
            for correction in validation['corrections_needed']:
                report += f"- 🔧 {correction['key']}: Change from {correction['current']} to {correction['correct']}\n"

        if validation['version_mismatches']:
            report += "\n### Version Mismatches:\n"
            for mismatch in validation['version_mismatches']:
                report += f"- 📦 {mismatch['key']}: Render shows {mismatch['render']}, Deployed is {mismatch['deployed']}\n"

        report += f"\n## Errors Encountered:\n"
        for error in self.errors:
            report += f"- {error}\n"

        return report

    def fix_critical_issues(self):
        """Automatically fix critical configuration issues"""
        fixes_applied = []

        # Fix Notion token
        if self.env_vars.get("NOTION_TOKEN") != self.notion_token:
            self.env_vars["NOTION_TOKEN"] = self.notion_token
            fixes_applied.append("Updated NOTION_TOKEN to correct value")

        # Fix version
        if self.env_vars.get("APP_VERSION") != "v30.4.0":
            self.env_vars["APP_VERSION"] = "v30.4.0"
            self.env_vars["VERSION"] = "v30.4.0"
            fixes_applied.append("Updated APP_VERSION to v30.4.0")

        # Add missing critical variables with correct values
        critical_fixes = {
            "NOTION_TOKEN": self.notion_token,
            "DATABASE_URL": "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres",
            "SUPABASE_DB_PASSWORD": "<DB_PASSWORD_REDACTED>",
            "JWT_SECRET_KEY": "brainops-jwt-secret-2025-production",
            "ENVIRONMENT": "production"
        }

        for key, value in critical_fixes.items():
            if key not in self.env_vars or "YOUR_" in self.env_vars.get(key, ""):
                self.env_vars[key] = value
                fixes_applied.append(f"Set {key} to correct value")

        return fixes_applied

def main():
    """Run the complete credentials management process"""
    manager = MasterCredentialsManager()

    print("=" * 80)
    print("🔐 MASTER CREDENTIALS MANAGER")
    print("=" * 80)

    # Load environment file
    env_file = "/home/matt-woodworth/Downloads/BrainOps (2).env"
    if Path(env_file).exists():
        print(f"✅ Loading environment from {env_file}")
        manager.load_env_file(env_file)
    else:
        print(f"❌ Environment file not found: {env_file}")
        return

    # Connect to database
    print("🗄️ Connecting to database...")
    if manager.connect_db():
        print("✅ Database connected")

        # Create tables
        print("📊 Creating credentials tables...")
        if manager.create_credentials_table():
            print("✅ Tables created/verified")

        # Sync to database
        print("🔄 Syncing to database...")
        sync_result = manager.sync_to_database()
        print(f"✅ Synced {sync_result['synced']} credentials, {sync_result['failed']} failed")

    # Validate credentials
    print("\n🔍 Validating credentials...")
    validation = manager.validate_credentials()

    # Apply fixes
    print("\n🔧 Applying critical fixes...")
    fixes = manager.fix_critical_issues()
    for fix in fixes:
        print(f"  ✅ {fix}")

    # Sync to Notion
    print("\n📝 Syncing to Notion...")
    if manager.sync_to_notion():
        print("✅ Notion documentation updated")

    # Generate report
    print("\n📄 Generating report...")
    report = manager.generate_report()

    # Save report
    report_file = "/home/matt-woodworth/fastapi-operator-env/credentials_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"✅ Report saved to {report_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total Variables: {validation['total']}")
    print(f"Valid: {validation['valid']} ({validation['valid']*100//validation['total']}%)")
    print(f"Issues Found: {validation['invalid']}")
    print(f"Critical Missing: {len(validation['missing_critical'])}")
    print(f"Security Issues: {len(validation['security_issues'])}")
    print(f"Fixes Applied: {len(fixes)}")

    if manager.errors:
        print(f"\n⚠️ {len(manager.errors)} errors encountered - check report for details")

    print("\n✅ Credentials management complete!")

if __name__ == "__main__":
    main()