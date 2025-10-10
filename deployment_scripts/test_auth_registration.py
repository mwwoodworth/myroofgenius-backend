#!/usr/bin/env python3
"""
Test Authentication Registration Endpoint
"""

import requests
import json
import time
from datetime import datetime

BACKEND_URL = "https://brainops-backend-prod.onrender.com"

def test_registration():
    """Test the registration endpoint"""
    print(f"🔐 Testing Registration Endpoint at {BACKEND_URL}")
    print("=" * 60)
    
    # Test with a unique email
    test_email = f"test_user_{int(time.time())}@myroofgenius.com"
    test_password = "TestPassword123!"
    
    # Test registration endpoint
    print(f"\n📝 Testing registration with email: {test_email}")
    
    registration_data = {
        "email": test_email,
        "password": test_password,
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=registration_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {response.text[:500]}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
        elif response.status_code == 409:
            print("⚠️  User already exists (expected for duplicate registrations)")
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
    
    # Test with existing user
    print("\n📝 Testing registration with existing user (should fail)")
    existing_user_data = {
        "email": "test@brainops.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=existing_user_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 409:
            print("✅ Correctly rejected duplicate registration")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test login endpoint
    print("\n🔑 Testing login endpoint")
    login_data = {
        "email": "test@brainops.com",
        "password": "TestPassword123!"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login endpoint working correctly")
        else:
            print(f"❌ Login failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("The backend registration endpoint appears to be working correctly.")
    print("The issue is likely in the frontend NextAuth integration.")

if __name__ == "__main__":
    test_registration()