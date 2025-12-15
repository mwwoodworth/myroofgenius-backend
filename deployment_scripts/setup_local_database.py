#!/usr/bin/env python3
"""
Set up local database with schema and test users
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
from datetime import datetime
import uuid

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fastapi-operator-env', 'apps', 'backend'))

# Local database connection
LOCAL_DB_URL = "postgresql://postgres:<DB_PASSWORD_REDACTED>@localhost:54322/postgres"

# Production database connection (from .env)
PROD_DB_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require"

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_auth_schema(conn):
    """Create auth schema if it doesn't exist"""
    with conn.cursor() as cur:
        # First check if auth schema exists (it should in Supabase)
        cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'auth'
        """)
        
        if not cur.fetchone():
            # Only create if it doesn't exist
            cur.execute("CREATE SCHEMA IF NOT EXISTS auth;")
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auth.users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                encrypted_password VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                instance_id UUID,
                aud VARCHAR(255),
                role VARCHAR(255),
                email_confirmed_at TIMESTAMP WITH TIME ZONE,
                invited_at TIMESTAMP WITH TIME ZONE,
                confirmation_token VARCHAR(255),
                confirmation_sent_at TIMESTAMP WITH TIME ZONE,
                recovery_token VARCHAR(255),
                recovery_sent_at TIMESTAMP WITH TIME ZONE,
                email_change_token_new VARCHAR(255),
                email_change VARCHAR(255),
                email_change_sent_at TIMESTAMP WITH TIME ZONE,
                last_sign_in_at TIMESTAMP WITH TIME ZONE,
                raw_app_meta_data JSONB,
                raw_user_meta_data JSONB,
                is_super_admin BOOLEAN,
                phone VARCHAR(255),
                phone_confirmed_at TIMESTAMP WITH TIME ZONE,
                phone_change VARCHAR(255),
                phone_change_token VARCHAR(255),
                phone_change_sent_at TIMESTAMP WITH TIME ZONE,
                confirmed_at TIMESTAMP WITH TIME ZONE,
                email_change_token_current VARCHAR(255),
                email_change_confirm_status SMALLINT,
                banned_until TIMESTAMP WITH TIME ZONE,
                reauthentication_token VARCHAR(255),
                reauthentication_sent_at TIMESTAMP WITH TIME ZONE,
                is_sso_user BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP WITH TIME ZONE
            );
            
            -- Create public schema tables
            CREATE SCHEMA IF NOT EXISTS public;
            
            CREATE TABLE IF NOT EXISTS public.users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                password_hash VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE,
                is_superuser BOOLEAN DEFAULT FALSE,
                role VARCHAR(50) DEFAULT 'user'
            );
        """)
        conn.commit()
        print("✅ Auth schema and tables created")

def create_test_users(conn):
    """Create test users"""
    users = [
        {
            "email": "admin@brainops.com",
            "password": "AdminPassword123!",
            "name": "Admin User",
            "is_superuser": True,
            "role": "admin"
        },
        {
            "email": "test@brainops.com",
            "password": "TestPassword123!",
            "name": "Test User",
            "is_superuser": False,
            "role": "user"
        },
        {
            "email": "demo@myroofgenius.com",
            "password": "DemoPassword123!",
            "name": "Demo User",
            "is_superuser": False,
            "role": "user"
        }
    ]
    
    with conn.cursor() as cur:
        for user in users:
            user_id = str(uuid.uuid4())
            password_hash = hash_password(user["password"])
            
            # Insert into auth.users (Supabase auth)
            cur.execute("""
                INSERT INTO auth.users (
                    id, email, encrypted_password, 
                    email_confirmed_at, confirmed_at,
                    raw_user_meta_data, aud, role
                ) VALUES (%s, %s, %s, NOW(), NOW(), %s, 'authenticated', 'authenticated')
                ON CONFLICT (email) DO NOTHING
            """, (
                user_id, 
                user["email"], 
                password_hash,
                '{"name": "' + user["name"] + '"}'
            ))
            
            # Insert into public.users (our app's user table)
            cur.execute("""
                INSERT INTO public.users (
                    id, email, name, password_hash, 
                    is_superuser, role
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, (
                user_id,
                user["email"],
                user["name"],
                password_hash,
                user["is_superuser"],
                user["role"]
            ))
            
            print(f"✅ Created user: {user['email']}")
        
        conn.commit()

def sync_schema_from_production(local_conn, prod_conn):
    """Sync schema from production to local"""
    with prod_conn.cursor() as prod_cur:
        # Get all tables from production
        prod_cur.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """)
        
        tables = prod_cur.fetchall()
        print(f"Found {len(tables)} tables in production")
        
        # For now, just list them
        for schema, table in tables:
            print(f"  - {schema}.{table}")

def main():
    """Main setup function"""
    print("Setting up local database...")
    
    # Connect to local database
    try:
        local_conn = psycopg2.connect(LOCAL_DB_URL)
        print("✅ Connected to local database")
    except Exception as e:
        print(f"❌ Failed to connect to local database: {e}")
        print("Make sure Docker Supabase is running")
        return
    
    # Create schema and tables
    create_auth_schema(local_conn)
    
    # Create test users
    create_test_users(local_conn)
    
    # Optional: Sync from production
    try:
        print("\nConnecting to production database...")
        prod_conn = psycopg2.connect(PROD_DB_URL)
        print("✅ Connected to production database")
        
        sync_schema_from_production(local_conn, prod_conn)
        prod_conn.close()
    except Exception as e:
        print(f"⚠️ Could not connect to production: {e}")
        print("Continuing with local setup only")
    
    local_conn.close()
    print("\n✅ Local database setup complete!")

if __name__ == "__main__":
    main()