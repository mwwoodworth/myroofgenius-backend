#!/usr/bin/env python3
"""
Comprehensive Database Schema Analysis and Fix Generator
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
from datetime import datetime
import json

# Database connection
DB_PASSWORD = "Mww00dw0rth@2O1S$"
DB_PASSWORD_ENCODED = urllib.parse.quote(DB_PASSWORD)
CONN_STRING = f"postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def analyze_schema():
    """Perform comprehensive schema analysis"""
    conn = psycopg2.connect(CONN_STRING, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    analysis = {
        "timestamp": datetime.now().isoformat(),
        "tables": {},
        "issues": {
            "critical": [],
            "major": [],
            "minor": [],
            "performance": [],
            "security": []
        }
    }
    
    print("=== BrainOps Database Schema Analysis ===\n")
    
    # 1. Get all tables
    print("1. Extracting table information...")
    cur.execute("""
        SELECT 
            t.table_name,
            obj_description(c.oid) as table_comment,
            pg_size_pretty(pg_total_relation_size(c.oid)) as size,
            reltuples::bigint as estimated_rows,
            pg_stat_get_live_tuples(c.oid) as live_rows,
            pg_stat_get_dead_tuples(c.oid) as dead_rows,
            r.rolname as owner
        FROM information_schema.tables t
        JOIN pg_class c ON c.relname = t.table_name AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        JOIN pg_roles r ON r.oid = c.relowner
        WHERE t.table_schema = 'public' 
        AND t.table_type = 'BASE TABLE'
        ORDER BY pg_total_relation_size(c.oid) DESC
    """)
    
    tables = cur.fetchall()
    print(f"   Found {len(tables)} tables\n")
    
    # 2. Analyze each table
    for table in tables:
        table_name = table['table_name']
        print(f"2. Analyzing table: {table_name}")
        
        analysis['tables'][table_name] = {
            "info": dict(table),
            "columns": [],
            "constraints": [],
            "indexes": [],
            "issues": []
        }
        
        # Get columns
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                udt_name,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default,
                is_identity,
                col_description(pgc.oid, a.attnum) as column_comment
            FROM information_schema.columns c
            JOIN pg_class pgc ON pgc.relname = c.table_name
            JOIN pg_attribute a ON a.attrelid = pgc.oid AND a.attname = c.column_name
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cur.fetchall()
        analysis['tables'][table_name]['columns'] = columns
        
        # Check column issues
        for col in columns:
            # Check for VARCHAR without length
            if col['data_type'] == 'character varying' and col['character_maximum_length'] is None:
                issue = f"{table_name}.{col['column_name']}: VARCHAR without length limit"
                analysis['issues']['major'].append(issue)
                analysis['tables'][table_name]['issues'].append(issue)
            
            # Check for missing NOT NULL on important columns
            if col['is_nullable'] == 'YES' and any(suffix in col['column_name'] for suffix in ['_id', '_type', '_status', 'created_at', 'updated_at']):
                issue = f"{table_name}.{col['column_name']}: Should be NOT NULL"
                analysis['issues']['minor'].append(issue)
                analysis['tables'][table_name]['issues'].append(issue)
            
            # Check for missing defaults on timestamps
            if col['column_name'] in ['created_at', 'updated_at', 'deleted_at'] and not col['column_default']:
                issue = f"{table_name}.{col['column_name']}: Missing DEFAULT CURRENT_TIMESTAMP"
                analysis['issues']['major'].append(issue)
                analysis['tables'][table_name]['issues'].append(issue)
        
        # Get constraints
        cur.execute("""
            SELECT 
                con.conname as constraint_name,
                con.contype as constraint_type,
                pg_get_constraintdef(con.oid) as definition
            FROM pg_constraint con
            JOIN pg_class c ON c.oid = con.conrelid
            WHERE c.relname = %s
            AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        """, (table_name,))
        
        constraints = cur.fetchall()
        analysis['tables'][table_name]['constraints'] = constraints
        
        # Check for missing primary key
        has_pk = any(c['constraint_type'] == 'p' for c in constraints)
        if not has_pk:
            issue = f"{table_name}: Missing PRIMARY KEY"
            analysis['issues']['critical'].append(issue)
            analysis['tables'][table_name]['issues'].append(issue)
        
        # Get indexes
        cur.execute("""
            SELECT 
                i.indexname,
                i.indexdef,
                s.idx_scan,
                s.idx_tup_read,
                s.idx_tup_fetch
            FROM pg_indexes i
            LEFT JOIN pg_stat_user_indexes s ON s.indexrelname = i.indexname
            WHERE i.schemaname = 'public' AND i.tablename = %s
        """, (table_name,))
        
        indexes = cur.fetchall()
        analysis['tables'][table_name]['indexes'] = indexes
        
        # Check for unused indexes
        for idx in indexes:
            if idx['idx_scan'] == 0 and not idx['indexname'].endswith('_pkey'):
                issue = f"{table_name}.{idx['indexname']}: Unused index (0 scans)"
                analysis['issues']['performance'].append(issue)
                analysis['tables'][table_name]['issues'].append(issue)
    
    # 3. Check for orphaned foreign keys
    print("\n3. Checking foreign key integrity...")
    cur.execute("""
        SELECT 
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
    """)
    
    foreign_keys = cur.fetchall()
    
    # Check FK indexes
    for fk in foreign_keys:
        cur.execute("""
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename = %s 
            AND indexdef LIKE %s
        """, (fk['table_name'], f"%({fk['column_name']})%"))
        
        if not cur.fetchone():
            issue = f"{fk['table_name']}.{fk['column_name']}: Foreign key without index"
            analysis['issues']['performance'].append(issue)
    
    # 4. Check RLS
    print("4. Checking Row Level Security...")
    cur.execute("""
        SELECT 
            tablename,
            rowsecurity
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename NOT IN ('spatial_ref_sys', 'alembic_version')
    """)
    
    for row in cur.fetchall():
        if not row['rowsecurity']:
            issue = f"{row['tablename']}: Row Level Security disabled"
            analysis['issues']['security'].append(issue)
    
    # 5. Generate fixes
    print("\n5. Generating migration scripts...")
    generate_fixes(analysis, cur)
    
    # 6. Save analysis
    with open('schema_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    # 7. Generate report
    generate_report(analysis)
    
    cur.close()
    conn.close()
    
    print("\n✅ Analysis complete!")
    print("   Files generated:")
    print("   - schema_analysis.json")
    print("   - schema_analysis_report.md")
    print("   - schema_fixes_migration.sql")
    print("   - schema_optimal_structure.sql")

def generate_fixes(analysis, cur):
    """Generate SQL migration to fix all issues"""
    with open('schema_fixes_migration.sql', 'w') as f:
        f.write("-- BrainOps Database Schema Fixes\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write("-- This migration fixes all identified issues\n\n")
        f.write("BEGIN;\n\n")
        f.write("-- Create migration tracking table if not exists\n")
        f.write("""CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);\n\n""")
        
        # Critical fixes
        if analysis['issues']['critical']:
            f.write("-- ========== CRITICAL FIXES ==========\n\n")
            for issue in analysis['issues']['critical']:
                if "Missing PRIMARY KEY" in issue:
                    table = issue.split(':')[0]
                    # Check if table has id column
                    id_cols = [c for c in analysis['tables'][table]['columns'] if c['column_name'] in ['id', 'uuid', f"{table}_id"]]
                    if id_cols:
                        f.write(f"-- Fix: {issue}\n")
                        f.write(f"ALTER TABLE {table} ADD PRIMARY KEY ({id_cols[0]['column_name']});\n\n")
                    else:
                        f.write(f"-- Fix: {issue}\n")
                        f.write(f"ALTER TABLE {table} ADD COLUMN id UUID DEFAULT gen_random_uuid() PRIMARY KEY;\n\n")
        
        # Major fixes
        if analysis['issues']['major']:
            f.write("-- ========== MAJOR FIXES ==========\n\n")
            for issue in analysis['issues']['major']:
                if "VARCHAR without length" in issue:
                    parts = issue.split('.')
                    table = parts[0]
                    column = parts[1].split(':')[0]
                    f.write(f"-- Fix: {issue}\n")
                    f.write(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TEXT;\n\n")
                elif "Missing DEFAULT CURRENT_TIMESTAMP" in issue:
                    parts = issue.split('.')
                    table = parts[0]
                    column = parts[1].split(':')[0]
                    f.write(f"-- Fix: {issue}\n")
                    f.write(f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT CURRENT_TIMESTAMP;\n")
                    f.write(f"UPDATE {table} SET {column} = CURRENT_TIMESTAMP WHERE {column} IS NULL;\n\n")
        
        # Performance fixes
        if analysis['issues']['performance']:
            f.write("-- ========== PERFORMANCE FIXES ==========\n\n")
            fk_indexes_added = set()
            for issue in analysis['issues']['performance']:
                if "Foreign key without index" in issue:
                    parts = issue.split('.')
                    table = parts[0]
                    column = parts[1].split(':')[0]
                    index_name = f"idx_{table}_{column}"
                    if index_name not in fk_indexes_added:
                        f.write(f"-- Fix: {issue}\n")
                        f.write(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column});\n\n")
                        fk_indexes_added.add(index_name)
                elif "Unused index" in issue:
                    parts = issue.split('.')
                    table = parts[0]
                    index = parts[1].split(':')[0]
                    f.write(f"-- Fix: {issue}\n")
                    f.write(f"-- DROP INDEX IF EXISTS {index}; -- Uncomment after review\n\n")
        
        # Add update triggers
        f.write("-- ========== ADD UPDATE TRIGGERS ==========\n\n")
        f.write("""-- Create update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';\n\n""")
        
        for table_name in analysis['tables']:
            columns = [c['column_name'] for c in analysis['tables'][table_name]['columns']]
            if 'updated_at' in columns:
                f.write(f"DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {table_name};\n")
                f.write(f"CREATE TRIGGER update_{table_name}_updated_at BEFORE UPDATE ON {table_name} FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();\n")
        
        f.write("\n-- Record migration\n")
        f.write("INSERT INTO schema_migrations (migration_name) VALUES ('brainops_schema_fixes_001') ON CONFLICT DO NOTHING;\n\n")
        f.write("COMMIT;\n")
    
    # Generate optimal schema
    with open('schema_optimal_structure.sql', 'w') as f:
        f.write("-- BrainOps Optimal Database Schema\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write("-- This represents the ideal schema structure\n\n")
        
        for table_name in sorted(analysis['tables'].keys()):
            table = analysis['tables'][table_name]
            f.write(f"\n-- Table: {table_name}\n")
            f.write(f"CREATE TABLE {table_name} (\n")
            
            col_defs = []
            for col in table['columns']:
                col_def = f"    {col['column_name']} "
                
                # Optimal type
                if col['data_type'] == 'character varying':
                    if 'email' in col['column_name']:
                        col_def += "VARCHAR(255)"
                    elif 'phone' in col['column_name']:
                        col_def += "VARCHAR(50)"
                    elif col['character_maximum_length']:
                        col_def += f"VARCHAR({col['character_maximum_length']})"
                    else:
                        col_def += "TEXT"
                elif col['data_type'] == 'USER-DEFINED':
                    col_def += col['udt_name'].upper()
                else:
                    col_def += col['data_type'].upper()
                
                # NOT NULL
                if col['is_nullable'] == 'NO' or any(suffix in col['column_name'] for suffix in ['_id', '_type', '_status', 'created_at', 'updated_at']):
                    col_def += " NOT NULL"
                
                # Defaults
                if col['column_name'] in ['created_at', 'updated_at']:
                    col_def += " DEFAULT CURRENT_TIMESTAMP"
                elif col['column_name'] == 'deleted_at':
                    col_def += " DEFAULT NULL"
                elif col['column_default']:
                    col_def += f" DEFAULT {col['column_default']}"
                
                col_defs.append(col_def)
            
            f.write(",\n".join(col_defs))
            
            # Add constraints
            constraints = [c for c in table['constraints'] if c['constraint_type'] != 'c']  # Exclude check constraints for now
            if constraints:
                f.write(",\n")
                con_defs = []
                for con in constraints:
                    con_defs.append(f"    {con['definition']}")
                f.write(",\n".join(con_defs))
            
            f.write("\n);\n")
            
            # Add indexes
            if table['indexes']:
                f.write(f"\n-- Indexes for {table_name}\n")
                for idx in table['indexes']:
                    if not idx['indexname'].endswith('_pkey'):
                        f.write(f"{idx['indexdef']};\n")

def generate_report(analysis):
    """Generate detailed markdown report"""
    with open('schema_analysis_report.md', 'w') as f:
        f.write("# BrainOps Database Schema Analysis Report\n\n")
        f.write(f"**Generated:** {analysis['timestamp']}\n\n")
        
        # Summary
        f.write("## Executive Summary\n\n")
        total_issues = sum(len(issues) for issues in analysis['issues'].values())
        f.write(f"- **Total Tables:** {len(analysis['tables'])}\n")
        f.write(f"- **Total Issues Found:** {total_issues}\n")
        f.write(f"  - Critical: {len(analysis['issues']['critical'])}\n")
        f.write(f"  - Major: {len(analysis['issues']['major'])}\n")
        f.write(f"  - Minor: {len(analysis['issues']['minor'])}\n")
        f.write(f"  - Performance: {len(analysis['issues']['performance'])}\n")
        f.write(f"  - Security: {len(analysis['issues']['security'])}\n\n")
        
        # Issues by severity
        f.write("## Issues by Severity\n\n")
        
        if analysis['issues']['critical']:
            f.write("### 🔴 Critical Issues\n")
            f.write("These must be fixed immediately:\n\n")
            for issue in analysis['issues']['critical']:
                f.write(f"- {issue}\n")
            f.write("\n")
        
        if analysis['issues']['major']:
            f.write("### 🟠 Major Issues\n")
            f.write("These should be fixed soon:\n\n")
            for issue in analysis['issues']['major']:
                f.write(f"- {issue}\n")
            f.write("\n")
        
        if analysis['issues']['performance']:
            f.write("### ⚡ Performance Issues\n")
            for issue in analysis['issues']['performance']:
                f.write(f"- {issue}\n")
            f.write("\n")
        
        if analysis['issues']['security']:
            f.write("### 🔒 Security Issues\n")
            for issue in analysis['issues']['security']:
                f.write(f"- {issue}\n")
            f.write("\n")
        
        # Table details
        f.write("## Table Analysis\n\n")
        
        for table_name in sorted(analysis['tables'].keys()):
            table = analysis['tables'][table_name]
            f.write(f"### {table_name}\n")
            f.write(f"- **Size:** {table['info']['size']}\n")
            f.write(f"- **Rows:** {table['info']['live_rows']:,}\n")
            f.write(f"- **Dead Rows:** {table['info']['dead_rows']:,}\n")
            
            if table['issues']:
                f.write(f"- **Issues:** {len(table['issues'])}\n")
                for issue in table['issues']:
                    f.write(f"  - {issue}\n")
            
            f.write("\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        f.write("1. **Immediate Actions:**\n")
        f.write("   - Run `schema_fixes_migration.sql` to fix all critical and major issues\n")
        f.write("   - Enable Row Level Security on all user-facing tables\n")
        f.write("   - Add missing indexes on foreign key columns\n\n")
        
        f.write("2. **Best Practices:**\n")
        f.write("   - Always use UUID for ID columns in new tables\n")
        f.write("   - Add `created_at` and `updated_at` timestamps to all tables\n")
        f.write("   - Use TEXT instead of VARCHAR without length\n")
        f.write("   - Create indexes on all foreign key columns\n")
        f.write("   - Enable RLS and create appropriate policies\n\n")
        
        f.write("3. **Performance Optimization:**\n")
        f.write("   - Review and drop unused indexes\n")
        f.write("   - Consider partitioning large tables\n")
        f.write("   - Add indexes for common query patterns\n")
        f.write("   - Regular VACUUM and ANALYZE\n\n")

if __name__ == "__main__":
    analyze_schema()