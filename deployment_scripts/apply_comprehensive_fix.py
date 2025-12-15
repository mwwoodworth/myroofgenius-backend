#!/usr/bin/env python3
"""
Apply comprehensive data type fixes to production database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
import sys

# Database connection
DB_PASSWORD = "Mww00dw0rth@2O1S$"
DB_PASSWORD_ENCODED = urllib.parse.quote(DB_PASSWORD)
CONN_STRING = f"postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def apply_fixes():
    """Apply the comprehensive data type fixes"""
    try:
        conn = psycopg2.connect(CONN_STRING)
        cur = conn.cursor()
        
        print("🔧 Applying comprehensive data type fixes...")
        
        # Read the migration SQL
        with open('/home/mwwoodworth/code/fastapi-operator-env/apps/backend/migrations/010_comprehensive_data_type_fix.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration
        cur.execute(migration_sql)
        conn.commit()
        
        print("✅ All fixes applied successfully!")
        
        # Test an insert
        print("\n🧪 Testing insert with fixed schema...")
        try:
            cur.execute("""
                INSERT INTO memory_entries (id, owner_type, owner_id, key, memory_type, version, content, context_json)
                VALUES (gen_random_uuid(), 'global', 'test-fix', 'v3.0.17-test', 'test', 1, '{}'::jsonb, '{}'::jsonb)
                RETURNING id, created_at, updated_at, accessed_at, version, memory_type
            """)
            result = cur.fetchone()
            print(f"✅ Test insert successful!")
            print(f"   - Created at: {result[1]}")
            print(f"   - Version: {result[4]} (type confirmed as integer)")
            
            # Clean up test
            cur.execute("DELETE FROM memory_entries WHERE key = 'v3.0.17-test'")
            conn.commit()
            
        except Exception as e:
            print(f"❌ Test insert failed: {e}")
            conn.rollback()
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_fixes()