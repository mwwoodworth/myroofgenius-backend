import psycopg2
import os

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

def check_auth_tables():
    """Check if auth-related tables exist"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    tables = ['app_users', 'user_sessions', 'auth_tokens']
    
    for table in tables:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table,))
        exists = cur.fetchone()[0]
        print(f"Table '{table}': {'✅ Exists' if exists else '❌ Missing'}")
    
    # Check if users table exists (might be the actual table name)
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'users'
        )
    """, ('users',))
    exists = cur.fetchone()[0]
    if exists:
        print(f"Table 'users': ✅ Exists (might be the auth table)")
        
        # Check users table structure
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
            LIMIT 10
        """)
        columns = cur.fetchall()
        print("\nUsers table columns:")
        for col_name, col_type in columns:
            print(f"  - {col_name}: {col_type}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_auth_tables()
