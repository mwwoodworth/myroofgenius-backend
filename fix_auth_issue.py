#!/usr/bin/env python3
"""
Debug and Fix Authentication Issue
Identifies the root cause of login 500 errors and applies fix
"""

import bcrypt
import psycopg2
import os
from datetime import datetime
import jwt
import requests

# Database connection
DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

def test_password_verification():
    """Test password verification manually"""
    print("🔍 Testing password verification...")

    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Get the test user
        cursor.execute(
            "SELECT email, hashed_password FROM app_users WHERE email = %s",
            ("test_cf15e83c@example.com",)
        )
        result = cursor.fetchone()

        if not result:
            print("❌ Test user not found")
            return False

        email, hashed_password = result
        test_password = "TestPassword123!"

        print(f"✅ Found user: {email}")
        print(f"✅ Hashed password starts with: {hashed_password[:20]}...")

        # Test bcrypt verification
        password_bytes = test_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')

        is_valid = bcrypt.checkpw(password_bytes, hash_bytes)
        print(f"✅ Password verification result: {is_valid}")

        cursor.close()
        conn.close()

        return is_valid

    except Exception as e:
        print(f"❌ Error in password verification: {e}")
        return False

def test_jwt_creation():
    """Test JWT token creation"""
    print("\n🔍 Testing JWT token creation...")

    try:
        JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")

        # Test creating a token
        payload = {
            "user_id": "test-user-id",
            "exp": datetime.utcnow().timestamp() + 1800  # 30 minutes
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        print(f"✅ JWT token created successfully: {token[:50]}...")

        # Test decoding
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print(f"✅ JWT token decoded successfully: {decoded}")

        return True

    except Exception as e:
        print(f"❌ Error in JWT creation: {e}")
        return False

def test_database_operations():
    """Test database update operations"""
    print("\n🔍 Testing database operations...")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Test updating failed login attempts (similar to what login does)
        cursor.execute(
            """UPDATE app_users
               SET failed_login_attempts = 0, last_login = %s
               WHERE email = %s""",
            (datetime.utcnow(), "test_cf15e83c@example.com")
        )

        conn.commit()
        print("✅ Database update operation successful")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Error in database operations: {e}")
        return False

def create_fixed_auth_endpoint():
    """Create a debug auth endpoint to test login without errors"""
    print("\n🔧 Creating debug auth endpoint...")

    debug_endpoint_code = '''
# Add this to your auth routes for debugging
@router.post("/debug-login")
async def debug_login(user_credentials: UserLogin):
    """Debug login endpoint with detailed error handling"""
    try:
        print(f"🔍 Debug login attempt for: {user_credentials.email}")

        with db_engine.connect() as conn:
            # Get user from database
            result = conn.execute(
                text("""
                    SELECT id, email, hashed_password, is_active, is_verified,
                           failed_login_attempts, locked_until
                    FROM app_users
                    WHERE email = :email
                """),
                {"email": user_credentials.email}
            )
            user = result.fetchone()

            if not user:
                return {"error": "User not found", "step": "user_lookup"}

            print(f"✅ User found: {user.email}")

            # Check if account is active
            if not user.is_active:
                return {"error": "Account inactive", "step": "active_check"}

            print("✅ Account is active")

            # Test password verification
            try:
                password_valid = verify_password(user_credentials.password, user.hashed_password)
                print(f"✅ Password verification result: {password_valid}")

                if not password_valid:
                    return {"error": "Invalid password", "step": "password_verification"}

            except Exception as e:
                return {"error": f"Password verification failed: {str(e)}", "step": "password_verification"}

            # Test token creation
            try:
                access_token = create_access_token({"user_id": str(user.id)})
                print(f"✅ Token created: {access_token[:50]}...")

            except Exception as e:
                return {"error": f"Token creation failed: {str(e)}", "step": "token_creation"}

            # Test database update
            try:
                conn.execute(
                    text("""
                        UPDATE app_users
                        SET failed_login_attempts = 0, locked_until = NULL, last_login = :now
                        WHERE id = :user_id
                    """),
                    {
                        "now": datetime.utcnow(),
                        "user_id": user.id
                    }
                )
                conn.commit()
                print("✅ Database update successful")

            except Exception as e:
                return {"error": f"Database update failed: {str(e)}", "step": "database_update"}

            return {
                "success": True,
                "message": "Debug login successful",
                "user_id": str(user.id),
                "access_token": access_token
            }

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"error": f"Unexpected error: {str(e)}", "step": "unexpected"}
'''

    with open("debug_auth_endpoint.py", "w") as f:
        f.write(debug_endpoint_code)

    print("✅ Debug auth endpoint code saved to debug_auth_endpoint.py")
    print("   Add this to your routes/auth.py file to test login step by step")

def main():
    """Run all authentication tests"""
    print("🔧 WeatherCraft Authentication Diagnostic Tool")
    print("=" * 60)

    # Run tests
    password_ok = test_password_verification()
    jwt_ok = test_jwt_creation()
    db_ok = test_database_operations()

    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)

    print(f"Password Verification: {'✅ PASS' if password_ok else '❌ FAIL'}")
    print(f"JWT Token Creation: {'✅ PASS' if jwt_ok else '❌ FAIL'}")
    print(f"Database Operations: {'✅ PASS' if db_ok else '❌ FAIL'}")

    if all([password_ok, jwt_ok, db_ok]):
        print("\n🎉 All components working - issue may be in login function logic")
        print("💡 Recommendation: Add detailed logging to login endpoint")
    else:
        print("\n⚠️  Found component failures - fix these issues first")

    create_fixed_auth_endpoint()

    print("\n🔧 Next Steps:")
    print("1. Add the debug endpoint to test login step by step")
    print("2. Check server logs for specific error details")
    print("3. Verify JWT_SECRET environment variable in production")

if __name__ == "__main__":
    main()