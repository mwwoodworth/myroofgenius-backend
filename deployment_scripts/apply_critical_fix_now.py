#!/usr/bin/env python3
"""
Apply critical data type fixes directly to production database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
import sys

# Database connection
DB_PASSWORD = "Mww00dw0rth@2O1S$"
DB_PASSWORD_ENCODED = urllib.parse.quote(DB_PASSWORD)
CONN_STRING = f"postgresql://postgres.yomagoqdmxszqtdwuhab:{DB_PASSWORD_ENCODED}@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def apply_critical_fixes():
    """Apply only the most critical fixes"""
    try:
        conn = psycopg2.connect(CONN_STRING)
        cur = conn.cursor()
        
        print("🔧 Applying CRITICAL data type fixes...")
        
        # 1. Fix timestamp defaults (most critical)
        print("  1. Adding timestamp defaults...")
        try:
            cur.execute("""
                ALTER TABLE memory_entries 
                    ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
                    ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP,
                    ALTER COLUMN accessed_at SET DEFAULT CURRENT_TIMESTAMP
            """)
            conn.commit()
            print("     ✅ Timestamp defaults added")
        except Exception as e:
            print(f"     ⚠️ Timestamp defaults may already exist: {e}")
            conn.rollback()
        
        # 2. Fix NULL timestamps
        print("  2. Fixing NULL timestamps...")
        try:
            cur.execute("""
                UPDATE memory_entries 
                SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
                    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP),
                    accessed_at = COALESCE(accessed_at, CURRENT_TIMESTAMP)
                WHERE created_at IS NULL OR updated_at IS NULL OR accessed_at IS NULL
            """)
            rows_updated = cur.rowcount
            conn.commit()
            print(f"     ✅ Fixed {rows_updated} rows with NULL timestamps")
        except Exception as e:
            print(f"     ❌ Could not fix NULL timestamps: {e}")
            conn.rollback()
        
        # 3. Fix memory_type
        print("  3. Fixing memory_type...")
        try:
            cur.execute("ALTER TABLE memory_entries ALTER COLUMN memory_type SET DEFAULT 'general'")
            cur.execute("UPDATE memory_entries SET memory_type = 'general' WHERE memory_type IS NULL")
            rows_updated = cur.rowcount
            conn.commit()
            print(f"     ✅ Fixed {rows_updated} rows with NULL memory_type")
        except Exception as e:
            print(f"     ⚠️ memory_type fix: {e}")
            conn.rollback()
        
        # 4. Fix JSON columns
        print("  4. Fixing JSON columns...")
        try:
            cur.execute("""
                ALTER TABLE memory_entries 
                    ALTER COLUMN content SET DEFAULT '{}'::jsonb,
                    ALTER COLUMN context_json SET DEFAULT '{}'::jsonb
            """)
            cur.execute("UPDATE memory_entries SET content = '{}'::jsonb WHERE content IS NULL")
            cur.execute("UPDATE memory_entries SET context_json = '{}'::jsonb WHERE context_json IS NULL")
            conn.commit()
            print("     ✅ JSON columns fixed")
        except Exception as e:
            print(f"     ⚠️ JSON fix: {e}")
            conn.rollback()
        
        # 5. Fix version column (MOST CRITICAL)
        print("  5. Fixing version column type...")
        try:
            # First check current type
            cur.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'memory_entries' AND column_name = 'version'
            """)
            current_type = cur.fetchone()[0]
            print(f"     Current version type: {current_type}")
            
            if 'character' in current_type or 'text' in current_type:
                # Clean up data first
                cur.execute("""
                    UPDATE memory_entries 
                    SET version = '1' 
                    WHERE version IS NULL 
                       OR version NOT SIMILAR TO '[0-9]+'
                """)
                print(f"     Cleaned {cur.rowcount} invalid version values")
                
                # Convert numeric strings
                cur.execute("""
                    UPDATE memory_entries 
                    SET version = FLOOR(version::numeric)::text
                    WHERE version SIMILAR TO '[0-9]+(\\.[0-9]+)?'
                """)
                print(f"     Converted {cur.rowcount} decimal versions")
                
                # Now alter column type
                cur.execute("""
                    ALTER TABLE memory_entries 
                        ALTER COLUMN version TYPE INTEGER USING version::integer,
                        ALTER COLUMN version SET DEFAULT 1
                """)
                conn.commit()
                print("     ✅ Version column converted to INTEGER")
            else:
                print("     ✅ Version column already INTEGER")
                
        except Exception as e:
            print(f"     ❌ Version fix failed: {e}")
            conn.rollback()
        
        # Test insert
        print("\n🧪 Testing insert with fixed schema...")
        try:
            cur.execute("""
                INSERT INTO memory_entries (id, owner_type, owner_id, key, memory_type, version, content, context_json)
                VALUES (gen_random_uuid(), 'global', 'critical-fix-test', 'v3.0.18-test', 'test', 1, '{}'::jsonb, '{}'::jsonb)
                RETURNING id, created_at, version
            """)
            result = cur.fetchone()
            print(f"   ✅ Test insert successful!")
            print(f"      ID: {result[0]}")
            print(f"      Created: {result[1]}")
            print(f"      Version: {result[2]} (type: INTEGER)")
            
            # Clean up
            cur.execute("DELETE FROM memory_entries WHERE key = 'v3.0.18-test'")
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Test insert failed: {e}")
            conn.rollback()
        
        cur.close()
        conn.close()
        print("\n✅ Critical fixes applied successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_critical_fixes()