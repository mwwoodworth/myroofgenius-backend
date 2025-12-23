#!/usr/bin/env python3
"""
Complete System Audit and Documentation
Thoroughly reviews all systems and creates permanent documentation
"""

import asyncio
import asyncpg
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any

DATABASE_URL = os.getenv("DATABASE_URL", "")

class SystemAuditor:
    def __init__(self):
        self.db_pool = None
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "database": {},
            "render": {},
            "vercel": {},
            "systems": {},
            "recommendations": []
        }

    async def initialize(self):
        """Initialize database connection"""
        self.db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        print("✅ Database connection initialized")

    async def audit_database_schema(self):
        """Complete database schema audit"""
        print("\n📊 AUDITING DATABASE SCHEMA...")
        async with self.db_pool.acquire() as conn:
            # Get all tables grouped by prefix
            tables = await conn.fetch("""
                SELECT
                    table_name,
                    CASE
                        WHEN table_name LIKE 'cns_%' THEN 'CNS System'
                        WHEN table_name LIKE 'ai_%' THEN 'AI System'
                        WHEN table_name LIKE 'crm_%' THEN 'CRM System'
                        WHEN table_name LIKE 'hr_%' THEN 'HR System'
                        WHEN table_name LIKE 'inventory_%' THEN 'Inventory'
                        WHEN table_name LIKE 'equipment_%' THEN 'Equipment'
                        WHEN table_name LIKE 'job_%' THEN 'Jobs'
                        WHEN table_name LIKE 'customer_%' THEN 'Customers'
                        WHEN table_name LIKE 'invoice_%' THEN 'Invoicing'
                        WHEN table_name LIKE 'estimate_%' THEN 'Estimates'
                        WHEN table_name LIKE 'workflow_%' THEN 'Workflows'
                        WHEN table_name LIKE 'tenant_%' THEN 'Multi-tenant'
                        WHEN table_name LIKE 'auth_%' THEN 'Authentication'
                        WHEN table_name LIKE 'test_%' THEN 'Test/Temp'
                        WHEN table_name LIKE 'temp_%' THEN 'Test/Temp'
                        WHEN table_name LIKE '_prisma%' THEN 'Prisma/Migration'
                        ELSE 'Core/Other'
                    END as category,
                    pg_size_pretty(pg_total_relation_size('"'||table_name||'"')) as size
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY category, table_name
            """)

            # Group tables by category
            categorized = {}
            for row in tables:
                category = row['category']
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append({
                    "name": row['table_name'],
                    "size": row['size']
                })

            # Check for duplicates
            duplicates = await conn.fetch("""
                WITH table_patterns AS (
                    SELECT
                        regexp_replace(table_name, '[0-9]+', '') as base_name,
                        array_agg(table_name ORDER BY table_name) as tables,
                        count(*) as count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    GROUP BY regexp_replace(table_name, '[0-9]+', '')
                    HAVING count(*) > 1
                )
                SELECT * FROM table_patterns
                ORDER BY count DESC
                LIMIT 20
            """)

            # Check for CNS tables
            cns_tables = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'cns_%'
            """)

            # Check for pgvector extension
            extensions = await conn.fetch("""
                SELECT extname, extversion
                FROM pg_extension
            """)

            self.audit_results['database'] = {
                "total_tables": len(tables),
                "categorized": categorized,
                "duplicates": [dict(d) for d in duplicates],
                "cns_tables_exist": len(cns_tables) > 0,
                "cns_tables": [t['table_name'] for t in cns_tables],
                "extensions": [dict(e) for e in extensions],
                "has_pgvector": any(e['extname'] == 'vector' for e in extensions)
            }

            print(f"  Total tables: {len(tables)}")
            print(f"  Categories: {len(categorized)}")
            print(f"  Duplicate patterns: {len(duplicates)}")
            print(f"  CNS tables exist: {len(cns_tables) > 0}")
            print(f"  pgvector installed: {self.audit_results['database']['has_pgvector']}")

    async def check_render_status(self):
        """Check Render deployment status and environment"""
        print("\n🚀 CHECKING RENDER STATUS...")

        # Check current deployment
        api_key = os.getenv("RENDER_API_KEY", "")
        service_id = os.getenv("RENDER_SERVICE_ID", "srv-d1tfs4idbo4c73di6k00")

        try:
            # Get deployment status
            response = requests.get(
                f"https://api.render.com/v1/services/{service_id}/deploys?limit=1",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            deploy_data = response.json()[0]['deploy']

            # Get service details
            service_response = requests.get(
                f"https://api.render.com/v1/services/{service_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            service_data = service_response.json()

            # Check live endpoints
            base_url = "https://brainops-backend-prod.onrender.com"
            endpoints_to_check = [
                "/api/v1/health",
                "/api/v1/customers",
                "/api/v1/cns/status",
                "/api/v1/ai/agents"
            ]

            endpoint_status = {}
            for endpoint in endpoints_to_check:
                try:
                    resp = requests.get(f"{base_url}{endpoint}", timeout=5)
                    endpoint_status[endpoint] = resp.status_code
                except:
                    endpoint_status[endpoint] = "error"

            self.audit_results['render'] = {
                "status": deploy_data['status'],
                "version": deploy_data['image']['ref'],
                "created_at": deploy_data['createdAt'],
                "service_name": service_data.get('name', 'Unknown'),
                "endpoint_status": endpoint_status,
                "cns_available": endpoint_status.get('/api/v1/cns/status') == 200
            }

            print(f"  Status: {deploy_data['status']}")
            print(f"  Version: {deploy_data['image']['ref']}")
            print(f"  CNS endpoints: {'✅ Available' if self.audit_results['render']['cns_available'] else '❌ Not available'}")

        except Exception as e:
            print(f"  Error checking Render: {e}")
            self.audit_results['render']['error'] = str(e)

    async def check_vercel_deployments(self):
        """Check Vercel deployments"""
        print("\n🌐 CHECKING VERCEL DEPLOYMENTS...")

        vercel_token = os.getenv("VERCEL_TOKEN", "")

        try:
            # List all projects
            response = requests.get(
                "https://api.vercel.com/v9/projects",
                headers={"Authorization": f"Bearer {vercel_token}"}
            )

            if response.status_code == 200:
                projects = response.json().get('projects', [])

                vercel_info = []
                for project in projects[:5]:  # Check top 5 projects
                    # Get latest deployment
                    deploy_resp = requests.get(
                        f"https://api.vercel.com/v6/deployments?projectId={project['id']}&limit=1",
                        headers={"Authorization": f"Bearer {vercel_token}"}
                    )

                    if deploy_resp.status_code == 200:
                        deployments = deploy_resp.json().get('deployments', [])
                        latest = deployments[0] if deployments else None

                        vercel_info.append({
                            "name": project['name'],
                            "id": project['id'],
                            "latest_deployment": {
                                "url": latest.get('url') if latest else None,
                                "state": latest.get('state') if latest else None,
                                "created": latest.get('created') if latest else None
                            } if latest else None
                        })

                self.audit_results['vercel'] = {
                    "total_projects": len(projects),
                    "projects": vercel_info
                }

                print(f"  Total projects: {len(projects)}")
                for proj in vercel_info:
                    status = proj['latest_deployment']['state'] if proj['latest_deployment'] else 'No deployment'
                    print(f"  {proj['name']}: {status}")

        except Exception as e:
            print(f"  Error checking Vercel: {e}")
            self.audit_results['vercel']['error'] = str(e)

    async def create_master_documentation(self):
        """Create master documentation in database"""
        print("\n📝 CREATING MASTER DOCUMENTATION...")

        async with self.db_pool.acquire() as conn:
            # Create master documentation table if not exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_documentation (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    category VARCHAR(100) NOT NULL,
                    subcategory VARCHAR(100),
                    key VARCHAR(200) NOT NULL,
                    value JSONB NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    version INTEGER DEFAULT 1,
                    UNIQUE(category, subcategory, key)
                )
            """)

            # Document all findings
            documentation_entries = [
                # System Overview
                ("system", "overview", "architecture", {
                    "backend": "FastAPI on Render",
                    "frontend": "Next.js on Vercel",
                    "database": "PostgreSQL on Supabase",
                    "version": "v134.0.1"
                }, "Overall system architecture"),

                # Database Info
                ("database", "statistics", "table_count", {
                    "total": self.audit_results['database']['total_tables'],
                    "by_category": {k: len(v) for k, v in self.audit_results['database']['categorized'].items()}
                }, "Database table statistics"),

                ("database", "issues", "duplicates", {
                    "count": len(self.audit_results['database']['duplicates']),
                    "patterns": self.audit_results['database']['duplicates'][:10]
                }, "Duplicate table patterns"),

                ("database", "cns", "status", {
                    "tables_exist": self.audit_results['database']['cns_tables_exist'],
                    "pgvector_installed": self.audit_results['database']['has_pgvector'],
                    "tables": self.audit_results['database']['cns_tables']
                }, "CNS system database status"),

                # Credentials
                ("credentials", "database", "supabase", {
                    "host": "aws-0-us-east-2.pooler.supabase.com",
                    "user": "postgres.yomagoqdmxszqtdwuhab",
                    "password": "<DB_PASSWORD_REDACTED>",
                    "database": "postgres",
                    "port": 5432
                }, "Supabase database credentials"),

                ("credentials", "docker", "hub", {
                    "username": "mwwoodworth",
                    "repository": "mwwoodworth/brainops-backend",
                    "pat": "dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho"
                }, "Docker Hub credentials"),

                ("credentials", "render", "api", {
                    "api_key": "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx",
                    "service_id": "srv-d1tfs4idbo4c73di6k00",
                    "url": "https://brainops-backend-prod.onrender.com"
                }, "Render deployment credentials"),

                ("credentials", "vercel", "api", {
                    "token": "vCDh2d4AgYXPAs0089MvQcHs",
                    "scope": "matts-projects-fe7d7976"
                }, "Vercel deployment credentials"),

                # Deployment Status
                ("deployment", "render", "current", self.audit_results.get('render', {}), "Current Render deployment status"),
                ("deployment", "vercel", "projects", self.audit_results.get('vercel', {}), "Vercel projects status"),

                # Recommendations
                ("recommendations", "cns", "next_steps", {
                    "priority": "high",
                    "tasks": [
                        "Create CNS database tables",
                        "Install pgvector extension",
                        "Add OpenAI/Anthropic API keys to Render",
                        "Deploy v135.0.0 with CNS fixes",
                        "Build frontend interface"
                    ]
                }, "CNS implementation next steps"),

                ("recommendations", "database", "cleanup", {
                    "priority": "medium",
                    "duplicate_patterns": len(self.audit_results['database']['duplicates']),
                    "test_tables": len([t for t in self.audit_results['database']['categorized'].get('Test/Temp', [])]),
                    "action": "Review and consolidate duplicate tables"
                }, "Database cleanup recommendations")
            ]

            # Insert or update documentation
            for category, subcategory, key, value, description in documentation_entries:
                await conn.execute("""
                    INSERT INTO system_documentation (category, subcategory, key, value, description)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (category, subcategory, key)
                    DO UPDATE SET
                        value = $4,
                        description = $5,
                        updated_at = NOW(),
                        version = system_documentation.version + 1
                """, category, subcategory, key, json.dumps(value), description)

            print(f"  Created {len(documentation_entries)} documentation entries")

            # Create index for fast lookups
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_system_doc_category
                ON system_documentation(category, subcategory)
            """)

            return True

    async def generate_action_plan(self):
        """Generate comprehensive action plan"""
        print("\n🎯 GENERATING ACTION PLAN...")

        actions = []

        # CNS Implementation
        if not self.audit_results['database']['cns_tables_exist']:
            actions.append({
                "priority": 1,
                "system": "CNS",
                "task": "Create CNS database schema",
                "effort": "1 hour",
                "impact": "Enables persistent memory system"
            })

        if not self.audit_results['database']['has_pgvector']:
            actions.append({
                "priority": 1,
                "system": "CNS",
                "task": "Install pgvector extension",
                "effort": "30 minutes",
                "impact": "Enables semantic search"
            })

        # Database Cleanup
        if len(self.audit_results['database']['duplicates']) > 10:
            actions.append({
                "priority": 2,
                "system": "Database",
                "task": "Consolidate duplicate tables",
                "effort": "2-3 hours",
                "impact": "Reduces complexity and improves performance"
            })

        # System Integration
        if not self.audit_results['render'].get('cns_available'):
            actions.append({
                "priority": 1,
                "system": "Backend",
                "task": "Deploy CNS to production",
                "effort": "1 hour",
                "impact": "Activates central nervous system"
            })

        self.audit_results['action_plan'] = actions

        print(f"  Generated {len(actions)} action items")
        for action in actions[:5]:
            print(f"  P{action['priority']}: {action['task']} ({action['effort']})")

    async def run_complete_audit(self):
        """Run complete system audit"""
        print("=" * 60)
        print("🔍 COMPLETE SYSTEM AUDIT STARTING...")
        print("=" * 60)

        await self.initialize()

        # Run all audits
        await self.audit_database_schema()
        await self.check_render_status()
        await self.check_vercel_deployments()
        await self.generate_action_plan()
        await self.create_master_documentation()

        # Save results to file
        with open('/home/matt-woodworth/myroofgenius-backend/system_audit_results.json', 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)

        print("\n" + "=" * 60)
        print("✅ AUDIT COMPLETE")
        print("=" * 60)

        # Summary
        print("\n📊 SUMMARY:")
        print(f"  Database tables: {self.audit_results['database']['total_tables']}")
        print(f"  Duplicate patterns: {len(self.audit_results['database']['duplicates'])}")
        print(f"  CNS ready: {self.audit_results['database']['cns_tables_exist']}")
        print(f"  Action items: {len(self.audit_results['action_plan'])}")
        print(f"\n  Results saved to: system_audit_results.json")
        print(f"  Documentation stored in: system_documentation table")

        await self.db_pool.close()

if __name__ == "__main__":
    auditor = SystemAuditor()
    asyncio.run(auditor.run_complete_audit())