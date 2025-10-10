#!/usr/bin/env python3
"""
Extract complete database schema for analysis
"""
import psycopg2
import urllib.parse
import json
from datetime import datetime

# Database connection
DB_PASSWORD = "Mww00dw0rth@2O1S$"
DB_PASSWORD_ENCODED = urllib.parse.quote(DB_PASSWORD)
CONN_STRING = f"postgresql://postgres.yomagoqdmxszqtdwuhab:{DB_PASSWORD_ENCODED}@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def extract_schema():
    """Extract complete database schema"""
    conn = psycopg2.connect(CONN_STRING)
    cur = conn.cursor()
    
    results = []
    
    # 1. Get all tables with row counts
    print("Analyzing tables...")
    cur.execute("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
            n_live_tup as row_count,
            n_dead_tup as dead_rows,
            last_vacuum,
            last_autovacuum
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """)
    
    tables_info = cur.fetchall()
    
    # 2. Get detailed table structure
    cur.execute("""
        WITH table_columns AS (
            SELECT 
                t.table_name,
                string_agg(
                    c.column_name || ' ' || 
                    CASE 
                        WHEN c.data_type = 'character varying' THEN 'VARCHAR(' || c.character_maximum_length || ')'
                        WHEN c.data_type = 'numeric' THEN 'NUMERIC(' || c.numeric_precision || ',' || c.numeric_scale || ')'
                        WHEN c.data_type = 'character' THEN 'CHAR(' || c.character_maximum_length || ')'
                        WHEN c.data_type = 'ARRAY' THEN c.udt_name || '[]'
                        WHEN c.data_type = 'USER-DEFINED' THEN c.udt_name
                        ELSE UPPER(c.data_type)
                    END ||
                    CASE WHEN c.is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
                    CASE WHEN c.column_default IS NOT NULL THEN ' DEFAULT ' || c.column_default ELSE '' END,
                    E',\n    ' ORDER BY c.ordinal_position
                ) as columns_def
            FROM information_schema.tables t
            JOIN information_schema.columns c ON c.table_name = t.table_name
            WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            GROUP BY t.table_name
        ),
        constraints AS (
            SELECT 
                tc.table_name,
                string_agg(
                    CASE tc.constraint_type
                        WHEN 'PRIMARY KEY' THEN 'CONSTRAINT ' || tc.constraint_name || ' PRIMARY KEY (' || string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) || ')'
                        WHEN 'FOREIGN KEY' THEN 'CONSTRAINT ' || tc.constraint_name || ' FOREIGN KEY (' || string_agg(DISTINCT kcu.column_name, ', ') || ') REFERENCES ' || 
                                                ccu.table_name || '(' || string_agg(DISTINCT ccu.column_name, ', ') || ')' ||
                                                CASE 
                                                    WHEN rc.delete_rule != 'NO ACTION' THEN ' ON DELETE ' || rc.delete_rule 
                                                    ELSE '' 
                                                END ||
                                                CASE 
                                                    WHEN rc.update_rule != 'NO ACTION' THEN ' ON UPDATE ' || rc.update_rule 
                                                    ELSE '' 
                                                END
                        WHEN 'UNIQUE' THEN 'CONSTRAINT ' || tc.constraint_name || ' UNIQUE (' || string_agg(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) || ')'
                        WHEN 'CHECK' THEN 'CONSTRAINT ' || tc.constraint_name || ' CHECK ' || cc.check_clause
                    END,
                    E',\n    '
                ) as constraints_def
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            LEFT JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
            LEFT JOIN information_schema.referential_constraints rc 
                ON rc.constraint_name = tc.constraint_name
            LEFT JOIN information_schema.check_constraints cc 
                ON cc.constraint_name = tc.constraint_name
            WHERE tc.table_schema = 'public'
            GROUP BY tc.table_name, tc.constraint_name, tc.constraint_type, ccu.table_name, rc.delete_rule, rc.update_rule, cc.check_clause
        )
        SELECT 
            tc.table_name,
            tc.columns_def,
            string_agg(c.constraints_def, E',\n    ') as constraints_def
        FROM table_columns tc
        LEFT JOIN constraints c ON c.table_name = tc.table_name
        GROUP BY tc.table_name, tc.columns_def
        ORDER BY tc.table_name
    """)
    
    table_definitions = cur.fetchall()
    
    # 3. Analyze issues
    print("\nAnalyzing schema issues...")
    
    issues = {
        "missing_pk": [],
        "missing_indexes": [],
        "missing_fk": [],
        "naming_issues": [],
        "type_issues": [],
        "constraint_issues": [],
        "performance_issues": [],
        "security_issues": []
    }
    
    # Check for tables without primary keys
    cur.execute("""
        SELECT t.table_name
        FROM information_schema.tables t
        LEFT JOIN information_schema.table_constraints tc 
            ON t.table_name = tc.table_name 
            AND tc.constraint_type = 'PRIMARY KEY'
        WHERE t.table_schema = 'public' 
        AND t.table_type = 'BASE TABLE'
        AND tc.constraint_name IS NULL
    """)
    issues["missing_pk"] = [row[0] for row in cur.fetchall()]
    
    # Check for foreign key columns without indexes
    cur.execute("""
        WITH fk_columns AS (
            SELECT 
                kcu.table_name,
                kcu.column_name
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.table_constraints tc 
                ON kcu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND kcu.table_schema = 'public'
        )
        SELECT DISTINCT
            fk.table_name,
            fk.column_name
        FROM fk_columns fk
        LEFT JOIN pg_indexes i 
            ON i.tablename = fk.table_name 
            AND i.indexdef LIKE '%' || fk.column_name || '%'
        WHERE i.indexname IS NULL
    """)
    issues["missing_indexes"] = cur.fetchall()
    
    # Check for inconsistent naming
    cur.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND (
            column_name ~ '[A-Z]' -- Has uppercase
            OR column_name ~ '^[0-9]' -- Starts with number
            OR column_name ~ '[^a-z0-9_]' -- Has special chars
            OR column_name ~ '__' -- Double underscore
        )
    """)
    issues["naming_issues"] = cur.fetchall()
    
    # Check for inappropriate data types
    cur.execute("""
        SELECT table_name, column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND (
            (column_name LIKE '%email%' AND data_type != 'text' AND character_maximum_length > 255)
            OR (column_name LIKE '%phone%' AND character_maximum_length > 50)
            OR (column_name LIKE '%_id' AND data_type NOT IN ('uuid', 'integer', 'bigint'))
            OR (data_type = 'character varying' AND character_maximum_length IS NULL)
            OR (data_type = 'real') -- Should use numeric or double precision
        )
    """)
    issues["type_issues"] = cur.fetchall()
    
    # Check for missing NOT NULL constraints on important columns
    cur.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND is_nullable = 'YES'
        AND (
            column_name IN ('created_at', 'updated_at', 'created_by', 'updated_by')
            OR column_name LIKE '%_type'
            OR column_name LIKE '%_status'
        )
    """)
    issues["constraint_issues"] = cur.fetchall()
    
    # Check for tables without RLS
    cur.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND rowsecurity = false
        AND tablename NOT IN ('alembic_version', 'spatial_ref_sys')
    """)
    issues["security_issues"] = [row[0] for row in cur.fetchall()]
    
    # Generate report
    with open('database_analysis_report.md', 'w') as f:
        f.write("# BrainOps Database Schema Analysis Report\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- Total Tables: {len(table_definitions)}\n")
        f.write(f"- Tables without Primary Keys: {len(issues['missing_pk'])}\n")
        f.write(f"- Missing Foreign Key Indexes: {len(issues['missing_indexes'])}\n")
        f.write(f"- Naming Convention Issues: {len(issues['naming_issues'])}\n")
        f.write(f"- Data Type Issues: {len(issues['type_issues'])}\n")
        f.write(f"- Missing Constraints: {len(issues['constraint_issues'])}\n")
        f.write(f"- Tables without RLS: {len(issues['security_issues'])}\n\n")
        
        f.write("## Table Statistics\n\n")
        f.write("| Table | Size | Rows | Dead Rows | Last Vacuum |\n")
        f.write("|-------|------|------|-----------|-------------|\n")
        for row in tables_info:
            f.write(f"| {row[1]} | {row[2]} | {row[3]:,} | {row[4]:,} | {row[6] or 'Never'} |\n")
        
        f.write("\n## Issues Found\n\n")
        
        if issues["missing_pk"]:
            f.write("### Tables Without Primary Keys\n")
            for table in issues["missing_pk"]:
                f.write(f"- {table}\n")
            f.write("\n")
        
        if issues["missing_indexes"]:
            f.write("### Foreign Key Columns Without Indexes\n")
            for table, column in issues["missing_indexes"]:
                f.write(f"- {table}.{column}\n")
            f.write("\n")
        
        if issues["naming_issues"]:
            f.write("### Naming Convention Violations\n")
            for table, column in issues["naming_issues"]:
                f.write(f"- {table}.{column}\n")
            f.write("\n")
        
        if issues["type_issues"]:
            f.write("### Inappropriate Data Types\n")
            for row in issues["type_issues"]:
                f.write(f"- {row[0]}.{row[1]}: {row[2]}({row[3]})\n")
            f.write("\n")
        
        if issues["constraint_issues"]:
            f.write("### Missing NOT NULL Constraints\n")
            for table, column in issues["constraint_issues"]:
                f.write(f"- {table}.{column}\n")
            f.write("\n")
        
        if issues["security_issues"]:
            f.write("### Tables Without Row Level Security\n")
            for table in issues["security_issues"]:
                f.write(f"- {table}\n")
            f.write("\n")
    
    # Generate migration scripts
    print("\nGenerating migration scripts...")
    with open('schema_fixes.sql', 'w') as f:
        f.write("-- BrainOps Database Schema Fixes\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write("-- Run these migrations to fix all identified issues\n\n")
        
        f.write("BEGIN;\n\n")
        
        # Fix missing primary keys
        if issues["missing_pk"]:
            f.write("-- Add missing primary keys\n")
            for table in issues["missing_pk"]:
                # Check if table has an id column
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    AND column_name IN ('id', 'uuid', table_name || '_id')
                    LIMIT 1
                """, (table,))
                id_col = cur.fetchone()
                if id_col:
                    f.write(f"ALTER TABLE {table} ADD PRIMARY KEY ({id_col[0]});\n")
                else:
                    f.write(f"-- WARNING: Table {table} has no obvious ID column. Add one:\n")
                    f.write(f"-- ALTER TABLE {table} ADD COLUMN id UUID DEFAULT gen_random_uuid() PRIMARY KEY;\n")
            f.write("\n")
        
        # Add missing indexes
        if issues["missing_indexes"]:
            f.write("-- Add indexes for foreign key columns\n")
            for table, column in issues["missing_indexes"]:
                index_name = f"idx_{table}_{column}"
                f.write(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column});\n")
            f.write("\n")
        
        # Fix naming conventions
        if issues["naming_issues"]:
            f.write("-- Fix naming convention issues\n")
            f.write("-- WARNING: Renaming columns requires application code updates\n")
            for table, column in issues["naming_issues"]:
                new_name = column.lower().replace('-', '_').replace(' ', '_')
                f.write(f"-- ALTER TABLE {table} RENAME COLUMN {column} TO {new_name};\n")
            f.write("\n")
        
        # Fix data types
        if issues["type_issues"]:
            f.write("-- Fix inappropriate data types\n")
            for row in issues["type_issues"]:
                table, column, current_type, length = row
                if column.endswith('_id'):
                    f.write(f"-- Consider: ALTER TABLE {table} ALTER COLUMN {column} TYPE UUID USING {column}::uuid;\n")
                elif 'email' in column:
                    f.write(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR(255);\n")
                elif 'phone' in column:
                    f.write(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR(50);\n")
                elif current_type == 'real':
                    f.write(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE DOUBLE PRECISION;\n")
            f.write("\n")
        
        # Add missing constraints
        if issues["constraint_issues"]:
            f.write("-- Add missing NOT NULL constraints\n")
            for table, column in issues["constraint_issues"]:
                f.write(f"UPDATE {table} SET {column} = COALESCE({column}, ")
                if column.endswith('_at'):
                    f.write("CURRENT_TIMESTAMP")
                elif column.endswith('_by'):
                    f.write("'system'")
                else:
                    f.write("'default'")
                f.write(f") WHERE {column} IS NULL;\n")
                f.write(f"ALTER TABLE {table} ALTER COLUMN {column} SET NOT NULL;\n")
            f.write("\n")
        
        # Enable RLS
        if issues["security_issues"]:
            f.write("-- Enable Row Level Security\n")
            for table in issues["security_issues"]:
                f.write(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;\n")
                f.write(f"-- TODO: Add appropriate RLS policies for {table}\n")
            f.write("\n")
        
        f.write("COMMIT;\n")
    
    cur.close()
    conn.close()
    
    print("\n✅ Analysis complete!")
    print("   - Report: database_analysis_report.md")
    print("   - Fixes: schema_fixes.sql")

if __name__ == "__main__":
    extract_schema()