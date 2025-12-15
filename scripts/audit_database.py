#!/usr/bin/env python3
"""
Comprehensive Database Audit Script
Analyzes all 676+ tables and generates detailed report
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
# from tabulate import tabulate  # Optional, not required

# Database connection - use pooler for better reliability
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres")

class DatabaseAuditor:
    def __init__(self):
        self.conn = psycopg2.connect(DB_URL)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "schemas": {},
            "critical_tables": {},
            "issues": [],
            "recommendations": []
        }

    def audit_schemas(self):
        """Audit all schemas"""
        self.cursor.execute("""
            SELECT
                schemaname,
                COUNT(*) as table_count,
                SUM(CASE WHEN tablename LIKE '%test%' OR tablename LIKE '%tmp%' OR tablename LIKE '%backup%' THEN 1 ELSE 0 END) as temp_tables
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            GROUP BY schemaname
            ORDER BY table_count DESC
        """)

        schemas = self.cursor.fetchall()
        total_tables = sum(s['table_count'] for s in schemas)
        temp_tables = sum(s['temp_tables'] for s in schemas)

        self.report['summary']['total_schemas'] = len(schemas)
        self.report['summary']['total_tables'] = total_tables
        self.report['summary']['temp_tables'] = temp_tables
        self.report['schemas'] = {s['schemaname']: dict(s) for s in schemas}

        print(f"\n📊 Database Schema Summary:")
        print(f"  • Total Schemas: {len(schemas)}")
        print(f"  • Total Tables: {total_tables}")
        print(f"  • Temporary/Test Tables: {temp_tables}")

        if temp_tables > 10:
            self.report['issues'].append(f"High number of temporary tables ({temp_tables})")
            self.report['recommendations'].append("Clean up test/temporary tables")

    def audit_critical_tables(self):
        """Audit critical business tables"""
        critical_tables = [
            'customers', 'jobs', 'invoices', 'estimates', 'employees',
            'crews', 'timesheets', 'materials', 'equipment', 'ai_agents',
            'blog_posts', 'users', 'subscriptions', 'payments'
        ]

        self.cursor.execute("""
            SELECT
                relname as table_name,
                n_live_tup as row_count,
                n_dead_tup as dead_rows,
                pg_size_pretty(pg_total_relation_size('public.'||relname)) as total_size,
                last_vacuum,
                last_analyze
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            AND relname = ANY(%s)
            ORDER BY n_live_tup DESC
        """, (critical_tables,))

        tables = self.cursor.fetchall()

        print(f"\n🔑 Critical Tables Status:")
        for table in tables:
            self.report['critical_tables'][table['table_name']] = dict(table)

            # Check for issues
            if table['dead_rows'] > table['row_count'] * 0.2:
                self.report['issues'].append(f"Table {table['table_name']} has high dead row ratio")
                self.report['recommendations'].append(f"VACUUM {table['table_name']}")

            print(f"  • {table['table_name']:15} {table['row_count']:8,} rows | {table['total_size']:>10}")

    def audit_indexes(self):
        """Audit database indexes"""
        self.cursor.execute("""
            SELECT
                s.schemaname,
                t.tablename,
                s.indexrelname as indexname,
                pg_size_pretty(pg_relation_size(s.indexrelid)) as index_size,
                s.idx_scan as index_scans,
                s.idx_tup_read as tuples_read
            FROM pg_stat_user_indexes s
            JOIN pg_tables t ON s.schemaname = t.schemaname AND s.relname = t.tablename
            WHERE s.schemaname = 'public'
            ORDER BY s.idx_scan DESC
            LIMIT 20
        """)

        indexes = self.cursor.fetchall()

        # Find unused indexes
        unused = [idx for idx in indexes if idx['index_scans'] == 0]
        if unused:
            self.report['issues'].append(f"Found {len(unused)} unused indexes")
            self.report['recommendations'].append("Consider dropping unused indexes")

        print(f"\n🔍 Index Usage (Top 20):")
        for idx in indexes[:5]:
            print(f"  • {idx['indexname'][:40]:40} Scans: {idx['index_scans']:,}")

    def audit_connections(self):
        """Audit active connections"""
        self.cursor.execute("""
            SELECT
                state,
                COUNT(*) as connection_count,
                MAX(NOW() - state_change) as longest_duration
            FROM pg_stat_activity
            WHERE datname = current_database()
            GROUP BY state
        """)

        connections = self.cursor.fetchall()

        total_connections = sum(c['connection_count'] for c in connections)
        self.report['summary']['active_connections'] = total_connections

        print(f"\n🔌 Database Connections:")
        for conn in connections:
            print(f"  • {conn['state'] or 'idle':10} {conn['connection_count']:3} connections")

        if total_connections > 90:
            self.report['issues'].append(f"High connection count ({total_connections})")
            self.report['recommendations'].append("Review connection pooling settings")

    def audit_data_integrity(self):
        """Check data integrity issues"""
        print(f"\n✅ Data Integrity Checks:")

        # Check for orphaned jobs
        self.cursor.execute("""
            SELECT COUNT(*) as orphaned_jobs
            FROM jobs j
            LEFT JOIN customers c ON j.customer_id = c.id
            WHERE c.id IS NULL
        """)
        orphaned = self.cursor.fetchone()
        if orphaned['orphaned_jobs'] > 0:
            self.report['issues'].append(f"{orphaned['orphaned_jobs']} orphaned jobs without customers")
            print(f"  ⚠️  Found {orphaned['orphaned_jobs']} orphaned jobs")
        else:
            print(f"  ✓ No orphaned jobs")

        # Check for duplicate emails
        self.cursor.execute("""
            SELECT email, COUNT(*) as count
            FROM customers
            WHERE email IS NOT NULL
            GROUP BY email
            HAVING COUNT(*) > 1
            LIMIT 5
        """)
        duplicates = self.cursor.fetchall()
        if duplicates:
            self.report['issues'].append(f"Found duplicate customer emails")
            print(f"  ⚠️  Found {len(duplicates)} duplicate emails")
        else:
            print(f"  ✓ No duplicate customer emails")

    def generate_summary(self):
        """Generate audit summary"""
        print(f"\n" + "="*60)
        print(f"📋 AUDIT SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"="*60)

        print(f"\n📈 Key Metrics:")
        print(f"  • Total Tables: {self.report['summary'].get('total_tables', 0)}")
        print(f"  • Critical Tables: {len(self.report['critical_tables'])}")
        print(f"  • Active Connections: {self.report['summary'].get('active_connections', 0)}")

        if self.report['issues']:
            print(f"\n⚠️  Issues Found ({len(self.report['issues'])}):")
            for issue in self.report['issues'][:5]:
                print(f"  • {issue}")

        if self.report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in self.report['recommendations'][:5]:
                print(f"  • {rec}")

        # Save report to file
        report_file = f"database_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.report, f, indent=2, default=str)
        print(f"\n📄 Full report saved to: {report_file}")

    def run_audit(self):
        """Run complete audit"""
        print("\n🔍 Starting Database Audit...")
        print("="*60)

        try:
            self.audit_schemas()
            self.audit_critical_tables()
            self.audit_indexes()
            self.audit_connections()
            self.audit_data_integrity()
            self.generate_summary()

            # Update database with audit results
            self.cursor.execute("""
                INSERT INTO system_audits (
                    audit_type,
                    total_tables,
                    issues_found,
                    report_data,
                    created_at
                ) VALUES (
                    'database_audit',
                    %s,
                    %s,
                    %s,
                    NOW()
                )
                ON CONFLICT DO NOTHING
            """, (
                self.report['summary']['total_tables'],
                len(self.report['issues']),
                json.dumps(self.report)
            ))
            self.conn.commit()

        except Exception as e:
            print(f"\n❌ Audit error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cursor.close()
            self.conn.close()

if __name__ == "__main__":
    auditor = DatabaseAuditor()
    auditor.run_audit()