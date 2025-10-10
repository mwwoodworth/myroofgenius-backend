#!/usr/bin/env python3
"""
Create users with proper bcrypt hashing to match the backend
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse
from datetime import datetime
import uuid

# Try to use passlib for bcrypt hashing
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    USE_BCRYPT = True
except ImportError:
    print("⚠️  passlib not available, will update users without hashing")
    USE_BCRYPT = False

# Database connection
DB_PASSWORD = "Mww00dw0rth@2O1S$"
DB_PASSWORD_ENCODED = urllib.parse.quote(DB_PASSWORD)
CONN_STRING = f"postgresql://postgres.yomagoqdmxszqtdwuhab:{DB_PASSWORD_ENCODED}@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def create_users_with_bcrypt():
    """Create users with proper bcrypt hashing"""
    try:
        conn = psycopg2.connect(CONN_STRING)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test users
        test_users = [
            ('admin@brainops.com', 'AdminPassword123!'),
            ('test@brainops.com', 'TestPassword123!'),
            ('demo@myroofgenius.com', 'DemoPassword123!')
        ]
        
        print("🔧 Creating users with bcrypt hashing:")
        
        for email, password in test_users:
            if USE_BCRYPT:
                # Hash password with bcrypt
                hashed_pw = pwd_context.hash(password)
                
                # Update existing user or create new
                cur.execute("SELECT id FROM public.users WHERE email = %s", (email,))
                existing = cur.fetchone()
                
                if existing:
                    cur.execute("""
                        UPDATE public.users 
                        SET password_hash = %s
                        WHERE email = %s
                    """, (hashed_pw, email))
                    print(f"   ✅ Updated {email} with bcrypt hash")
                else:
                    user_id = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO public.users (id, email, password_hash, created_at)
                        VALUES (%s, %s, %s, %s)
                    """, (user_id, email, hashed_pw, datetime.utcnow()))
                    print(f"   ✅ Created {email} with bcrypt hash")
                
                conn.commit()
                
                # Verify the hash
                cur.execute("SELECT password_hash FROM public.users WHERE email = %s", (email,))
                stored_hash = cur.fetchone()['password_hash']
                is_valid = pwd_context.verify(password, stored_hash)
                print(f"      Verification: {'✅ PASS' if is_valid else '❌ FAIL'}")
            else:
                print(f"   ⚠️  Cannot hash password for {email} - passlib not available")
        
        # Show final state
        print("\n📊 Final user state:")
        cur.execute("""
            SELECT email, 
                   LENGTH(password_hash) as hash_length,
                   LEFT(password_hash, 10) as hash_prefix
            FROM public.users
            WHERE email IN ('admin@brainops.com', 'test@brainops.com', 'demo@myroofgenius.com')
        """)
        users = cur.fetchall()
        for user in users:
            print(f"   - {user['email']}: length={user['hash_length']}, prefix={user['hash_prefix']}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_users_with_bcrypt()