#!/usr/bin/env python3
"""
Apply memory schema fixes to production database
Fixes:
1. NOT NULL violations by adding DEFAULT CURRENT_TIMESTAMP
2. Version field integer type mismatch
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
import sys

# Database connection
DB_PASSWORD = "Mww00dw0rth@2O1S$"
DB_PASSWORD_ENCODED = urllib.parse.quote(DB_PASSWORD)
CONN_STRING = f"postgresql://postgres.yomagoqdmxszqtdwuhab:{DB_PASSWORD_ENCODED}@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def apply_schema_fixes():
    """Apply schema fixes to the database"""
    try:
        conn = psycopg2.connect(CONN_STRING)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔧 Applying memory schema fixes...")
        
        # Read the migration SQL
        with open('/home/mwwoodworth/code/fastapi-operator-env/apps/backend/migrations/009_fix_memory_schema_defaults.sql', 'r') as f:
            migration_sql = f.read()
        
        # Execute the migration
        cur.execute(migration_sql)
        conn.commit()
        
        print("✅ Schema fixes applied successfully!")
        
        # Verify the changes
        print("\n🔍 Verifying schema changes...")
        
        # Check memory_entries columns
        cur.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'memory_entries'
            AND column_name IN ('created_at', 'updated_at', 'accessed_at', 'version')
            ORDER BY column_name
        """)
        
        print("\n📊 memory_entries schema:")
        for col in cur.fetchall():
            print(f"  - {col['column_name']}: {col['data_type']} "
                  f"(default: {col['column_default'] or 'none'}, "
                  f"nullable: {col['is_nullable']})")
        
        # Test insert without timestamps
        print("\n🧪 Testing insert without timestamps...")
        try:
            cur.execute("""
                INSERT INTO memory_entries (id, content, owner_type, owner_id, memory_type, version)
                VALUES (gen_random_uuid(), 'Test memory', 'global', 'test-id', 'test', 1)
                RETURNING id, created_at, updated_at, accessed_at, version
            """)
            result = cur.fetchone()
            print(f"✅ Insert successful!")
            print(f"  - ID: {result['id']}")
            print(f"  - Created: {result['created_at']}")
            print(f"  - Updated: {result['updated_at']}")
            print(f"  - Accessed: {result['accessed_at']}")
            print(f"  - Version: {result['version']} (type: {type(result['version']).__name__})")
            
            # Clean up test data
            cur.execute("DELETE FROM memory_entries WHERE id = %s", (result['id'],))
            conn.commit()
            
        except Exception as e:
            print(f"❌ Test insert failed: {e}")
            conn.rollback()
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error applying schema fixes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    apply_schema_fixes()