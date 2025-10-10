#!/usr/bin/env python3
"""
Create test users directly in production database
CAUTION: This will create users in the production database
"""
import requests
import json
import sys

BASE_URL = "https://brainops-backend-prod.onrender.com"

def register_user(email: str, password: str, name: str):
    """Register a new user via API"""
    print(f"\nRegistering {email}...")
    
    data = {
        "email": email,
        "password": password,
        "name": name
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Successfully registered {email}")
            return True
        elif response.status_code == 400:
            error = response.json()
            if "already registered" in error.get("message", ""):
                print(f"ℹ️ {email} is already registered")
                return True
            else:
                print(f"❌ Failed: {error}")
                return False
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Create all test users"""
    users = [
        ("admin@brainops.com", "AdminPassword123!", "Admin User"),
        ("test@brainops.com", "TestPassword123!", "Test User"),
        ("demo@myroofgenius.com", "DemoPassword123!", "Demo User"),
    ]
    
    print("Creating test users in production...")
    print("⚠️ WARNING: This will create real users in the production database!")
    
    response = input("Continue? (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled")
        return
    
    success_count = 0
    for email, password, name in users:
        if register_user(email, password, name):
            success_count += 1
    
    print(f"\n✅ Created/verified {success_count}/{len(users)} users")
    
    # Test login with one of them
    print("\n🔧 Testing login with test@brainops.com...")
    test_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "test@brainops.com", "password": "TestPassword123!"}
    )
    
    if test_response.status_code == 200:
        print("✅ Login successful!")
        token = test_response.json().get("access_token")
        print(f"Token preview: {token[:20]}...")
    else:
        print(f"❌ Login failed: {test_response.text}")

if __name__ == "__main__":
    main()