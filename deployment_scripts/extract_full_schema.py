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
CONN_STRING = f"postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def extract_schema():
    """Extract complete database schema"""
    conn = psycopg2.connect(CONN_STRING)
    cur = conn.cursor()
    
    schema_data = {
        "extraction_date": datetime.now().isoformat(),
        "tables": {},
        "indexes": [],
        "foreign_keys": [],
        "functions": [],
        "triggers": [],
        "policies": [],
        "sequences": [],
        "views": []
    }
    
    # 1. Extract all tables and columns
    print("Extracting tables and columns...")
    cur.execute("""
        SELECT 
            t.table_name,
            t.table_type,
            obj_description(c.oid) as table_comment
        FROM information_schema.tables t
        JOIN pg_class c ON c.relname = t.table_name
        WHERE t.table_schema = 'public' 
        AND t.table_type IN ('BASE TABLE', 'VIEW')
        ORDER BY t.table_name
    """)
    tables = cur.fetchall()
    
    for table_name, table_type, table_comment in tables:
        # Get columns
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default,
                udt_name,
                is_identity,
                identity_generation,
                col_description(pgc.oid, a.attnum) as column_comment
            FROM information_schema.columns c
            JOIN pg_class pgc ON pgc.relname = c.table_name
            JOIN pg_attribute a ON a.attrelid = pgc.oid AND a.attname = c.column_name
            WHERE table_schema = 'public' 
            AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = []
        for col in cur.fetchall():
            columns.append({
                "name": col[0],
                "type": col[1],
                "max_length": col[2],
                "numeric_precision": col[3],
                "numeric_scale": col[4],
                "nullable": col[5] == 'YES',
                "default": col[6],
                "udt_name": col[7],
                "is_identity": col[8] == 'YES',
                "identity_generation": col[9],
                "comment": col[10]
            })
        
        schema_data["tables"][table_name] = {
            "type": table_type,
            "comment": table_comment,
            "columns": columns
        }
    
    # 2. Extract constraints
    print("Extracting constraints...")
    cur.execute("""
        SELECT 
            tc.table_name,
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.update_rule,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        LEFT JOIN information_schema.referential_constraints AS rc
            ON rc.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_type, kcu.ordinal_position
    """)
    
    constraints = {}
    for row in cur.fetchall():
        table = row[0]
        if table not in constraints:
            constraints[table] = []
        constraints[table].append({
            "name": row[1],
            "type": row[2],
            "column": row[3],
            "foreign_table": row[4],
            "foreign_column": row[5],
            "update_rule": row[6],
            "delete_rule": row[7]
        })
    
    # Add constraints to tables
    for table, table_constraints in constraints.items():
        if table in schema_data["tables"]:
            schema_data["tables"][table]["constraints"] = table_constraints
    
    # 3. Extract indexes
    print("Extracting indexes...")
    cur.execute("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname
    """)
    
    for row in cur.fetchall():
        schema_data["indexes"].append({
            "table": row[1],
            "name": row[2],
            "definition": row[3]
        })
    
    # 4. Extract functions
    print("Extracting functions...")
    cur.execute("""
        SELECT 
            p.proname as function_name,
            pg_get_function_arguments(p.oid) as arguments,
            pg_get_functiondef(p.oid) as definition
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
        ORDER BY p.proname
    """)
    
    for row in cur.fetchall():
        schema_data["functions"].append({
            "name": row[0],
            "arguments": row[1],
            "definition": row[2]
        })
    
    # 5. Extract triggers
    print("Extracting triggers...")
    cur.execute("""
        SELECT 
            trigger_name,
            event_manipulation,
            event_object_table,
            action_statement,
            action_orientation,
            action_timing
        FROM information_schema.triggers
        WHERE trigger_schema = 'public'
        ORDER BY event_object_table, trigger_name
    """)
    
    for row in cur.fetchall():
        schema_data["triggers"].append({
            "name": row[0],
            "event": row[1],
            "table": row[2],
            "statement": row[3],
            "orientation": row[4],
            "timing": row[5]
        })
    
    # 6. Extract RLS policies
    print("Extracting RLS policies...")
    cur.execute("""
        SELECT 
            schemaname,
            tablename,
            policyname,
            permissive,
            roles,
            cmd,
            qual,
            with_check
        FROM pg_policies
        WHERE schemaname = 'public'
        ORDER BY tablename, policyname
    """)
    
    for row in cur.fetchall():
        schema_data["policies"].append({
            "table": row[1],
            "name": row[2],
            "permissive": row[3],
            "roles": row[4],
            "command": row[5],
            "using": row[6],
            "with_check": row[7]
        })
    
    # 7. Check RLS status
    print("Checking RLS status...")
    cur.execute("""
        SELECT 
            schemaname,
            tablename,
            rowsecurity
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    
    for row in cur.fetchall():
        table_name = row[1]
        if table_name in schema_data["tables"]:
            schema_data["tables"][table_name]["rls_enabled"] = row[2]
    
    # Save to file
    with open('database_schema_full.json', 'w') as f:
        json.dump(schema_data, f, indent=2, default=str)
    
    # Also generate SQL dump
    print("\nGenerating SQL schema dump...")
    cur.execute("""
        SELECT 
            'CREATE TABLE ' || table_name || ' (' || 
            string_agg(
                column_name || ' ' || 
                CASE 
                    WHEN data_type = 'character varying' THEN 'VARCHAR(' || character_maximum_length || ')'
                    WHEN data_type = 'numeric' THEN 'NUMERIC(' || numeric_precision || ',' || numeric_scale || ')'
                    ELSE UPPER(data_type)
                END ||
                CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
                CASE WHEN column_default IS NOT NULL THEN ' DEFAULT ' || column_default ELSE '' END,
                ', '
                ORDER BY ordinal_position
            ) || ');' as create_statement
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name IN (
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        )
        GROUP BY table_name
        ORDER BY table_name
    """)
    
    with open('schema_dump.sql', 'w') as f:
        f.write("-- BrainOps Database Schema Dump\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n\n")
        
        for row in cur.fetchall():
            f.write(row[0] + "\n\n")
    
    cur.close()
    conn.close()
    
    print(f"\n✅ Schema extracted to database_schema_full.json and schema_dump.sql")
    print(f"   Found {len(schema_data['tables'])} tables")
    print(f"   Found {len(schema_data['indexes'])} indexes")
    print(f"   Found {len(schema_data['functions'])} functions")
    print(f"   Found {len(schema_data['policies'])} RLS policies")

if __name__ == "__main__":
    extract_schema()