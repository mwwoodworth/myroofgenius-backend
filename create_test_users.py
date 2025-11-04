#!/usr/bin/env python3
"""
Create test users for authentication testing
"""

import psycopg2
import bcrypt
import uuid
from datetime import datetime

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_test_users():
    """Create test users in the database"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Test users to create
    users = [
        {
            'email': 'admin@brainops.com',
            'password': 'AdminPassword123!',
            'full_name': 'System Administrator',
            'role': 'admin'
        },
        {
            'email': 'test@brainops.com',
            'password': 'TestPassword123!',
            'full_name': 'Test User',
            'role': 'user'
        },
        {
            'email': 'demo@myroofgenius.com',
            'password': 'DemoPassword123!',
            'full_name': 'Demo Account',
            'role': 'user'
        }
    ]
    
    print("Creating test users...")
    
    for user_data in users:
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user_data['password'])
        
        try:
            # Check if user already exists
            cur.execute(
                "SELECT id FROM app_users WHERE email = %s",
                (user_data['email'],)
            )
            existing = cur.fetchone()
            
            if existing:
                print(f"  ⚠️ User {user_data['email']} already exists, updating password...")
                # Update existing user
                cur.execute("""
                    UPDATE app_users 
                    SET hashed_password = %s, 
                        is_active = true, 
                        is_verified = true,
                        failed_login_attempts = 0,
                        locked_until = NULL,
                        updated_at = %s
                    WHERE email = %s
                """, (hashed_password, datetime.utcnow(), user_data['email']))
            else:
                # Create new user
                cur.execute("""
                    INSERT INTO app_users (
                        id, email, hashed_password, full_name, role, 
                        is_active, is_verified, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, true, true, %s, %s
                    )
                """, (
                    user_id,
                    user_data['email'],
                    hashed_password,
                    user_data['full_name'],
                    user_data['role'],
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                print(f"  ✅ Created user: {user_data['email']}")
            
            conn.commit()
            
        except Exception as e:
            print(f"  ❌ Error creating user {user_data['email']}: {e}")
            conn.rollback()
    
    # Display summary
    cur.execute("SELECT COUNT(*) FROM app_users WHERE is_active = true")
    active_count = cur.fetchone()[0]
    
    print(f"\n📊 Summary:")
    print(f"  Total active users: {active_count}")
    print(f"\n🔑 Test Credentials:")
    for user in users:
        print(f"  • {user['email']} / {user['password']}")
    
    cur.close()
    conn.close()
    
    print("\n✅ Test users ready!")

if __name__ == "__main__":
    create_test_users()