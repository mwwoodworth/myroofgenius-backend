#!/usr/bin/env python3
"""Create test users in the database"""
import bcrypt
import uuid
import psycopg2
from datetime import datetime

# Generate password hash
password = "TestPassword123!"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"Password hash: {hashed}")

# Database connection
conn_str = "postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"

# Test users to create
users = [
    {
        "email": "test@brainops.com",
        "username": "test",
        "role": "user"
    },
    {
        "email": "admin@brainops.com",
        "username": "admin",
        "role": "admin"
    },
    {
        "email": "demo@myroofgenius.com",
        "username": "demo",
        "role": "user"
    }
]

try:
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()
    
    for user in users:
        # Check if user exists
        cursor.execute(
            "SELECT id FROM app_users WHERE email = %s",
            (user["email"],)
        )
        
        if cursor.fetchone():
            print(f"User {user['email']} already exists")
        else:
            # Insert user
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO app_users 
                (id, email, username, hashed_password, is_active, is_verified, role, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                user["email"],
                user["username"],
                hashed,
                True,
                True,
                user["role"],
                datetime.utcnow()
            ))
            print(f"Created user: {user['email']}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ Test users created successfully!")
    print("   Email: test@brainops.com")
    print("   Password: TestPassword123!")
    
except Exception as e:
    print(f"Error: {e}")