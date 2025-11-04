#!/usr/bin/env python3
"""
Test Backend Health and Endpoints in Detail
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://brainops-backend-prod.onrender.com"

def test_backend_health():
    """Test backend health and key endpoints"""
    print(f"🏥 Testing Backend Health at {BACKEND_URL}")
    print("=" * 60)
    
    # Test health endpoint
    print("\n1️⃣ Testing Health Endpoint")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Version: {data.get('version', 'Unknown')}")
            print(f"Status: {data.get('status', 'Unknown')}")
            print(f"Routes Loaded: {data.get('routes_loaded', 'Unknown')}")
            print(f"Total Endpoints: {data.get('total_endpoints', 'Unknown')}")
            print(f"Operational Percentage: {data.get('operational_percentage', 'Unknown')}%")
        else:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test auth endpoints
    print("\n2️⃣ Testing Auth Endpoints")
    auth_endpoints = [
        ("GET", "/api/v1/auth", "Auth Base"),
        ("GET", "/api/v1/auth/users", "Users List"),
        ("POST", "/api/v1/auth/login", "Login"),
        ("POST", "/api/v1/auth/register", "Register"),
        ("POST", "/api/v1/auth/refresh", "Refresh Token"),
        ("POST", "/api/v1/auth/logout", "Logout")
    ]
    
    for method, endpoint, name in auth_endpoints:
        try:
            url = f"{BACKEND_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                # For POST endpoints, we'll just check if they exist (OPTIONS request)
                response = requests.options(url, timeout=5)
            
            print(f"  - {name}: {'✅' if response.status_code < 500 else '❌'} (Status: {response.status_code})")
            
        except Exception as e:
            print(f"  - {name}: ❌ Error: {str(e)}")
    
    # Test specific registration with detailed error info
    print("\n3️⃣ Testing Registration with Detailed Error Info")
    test_data = {
        "email": "detailed_test@myroofgenius.com",
        "password": "TestPassword123!",
        "full_name": "Detailed Test"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Response Text: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Check if there's a different registration endpoint
    print("\n4️⃣ Checking Alternative Registration Endpoints")
    alt_endpoints = [
        "/api/v1/users/register",
        "/api/v1/users/signup",
        "/api/v1/auth/signup",
        "/api/v1/register"
    ]
    
    for endpoint in alt_endpoints:
        try:
            url = f"{BACKEND_URL}{endpoint}"
            response = requests.options(url, timeout=3)
            if response.status_code < 500:
                print(f"  - {endpoint}: Found! (Status: {response.status_code})")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("The backend registration endpoint is returning 500 errors.")
    print("This needs to be fixed on the backend before frontend auth can work.")

if __name__ == "__main__":
    test_backend_health()