#!/usr/bin/env python3
"""Check users table structure"""
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
conn_str = "postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"

try:
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get column information
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    
    print("Users table columns:")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row['column_name']:20} {row['data_type']:20} {row['is_nullable']}")
    
    # Check if our test users exist
    print("\nTest users:")
    print("-" * 60)
    cursor.execute("""
        SELECT id, email 
        FROM users 
        WHERE email IN ('test@brainops.com', 'admin@brainops.com', 'demo@myroofgenius.com')
    """)
    
    for user in cursor.fetchall():
        print(f"ID: {user['id']}, Email: {user['email']}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")