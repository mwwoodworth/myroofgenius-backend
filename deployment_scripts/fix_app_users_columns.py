#!/usr/bin/env python3
"""
Fix app_users table by adding missing columns
"""

import psycopg2
from psycopg2 import sql

# Database connection
DB_URL = "postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"

def fix_app_users_table():
    """Add missing columns to app_users table"""
    try:
        # Connect to database
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        print("Connected to database successfully")
        
        # Add preferences column if it doesn't exist
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name = 'app_users' 
                               AND column_name = 'preferences') THEN
                    ALTER TABLE app_users ADD COLUMN preferences JSONB DEFAULT '{}';
                    RAISE NOTICE 'Added preferences column';
                END IF;
            END $$;
        """)
        
        # Add permissions column if it doesn't exist
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name = 'app_users' 
                               AND column_name = 'permissions') THEN
                    ALTER TABLE app_users ADD COLUMN permissions JSONB DEFAULT '[]';
                    RAISE NOTICE 'Added permissions column';
                END IF;
            END $$;
        """)
        
        # Add failed_login_attempts column if it doesn't exist
        cur.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name = 'app_users' 
                               AND column_name = 'failed_login_attempts') THEN
                    ALTER TABLE app_users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
                    RAISE NOTICE 'Added failed_login_attempts column';
                END IF;
            END $$;
        """)
        
        conn.commit()
        print("✅ Database schema updated successfully")
        
        # Verify columns exist
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'app_users'
            AND column_name IN ('preferences', 'permissions', 'failed_login_attempts')
            ORDER BY column_name;
        """)
        
        columns = cur.fetchall()
        print("\nColumn verification:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}, nullable={col[2]}, default={col[3]}")
        
        cur.close()
        conn.close()
        
        print("\n✅ All columns verified successfully")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    fix_app_users_table()