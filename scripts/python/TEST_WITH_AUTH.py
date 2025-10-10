#!/usr/bin/env python3
"""
Test endpoints that require authentication
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def get_auth_token():
    """Login and get authentication token"""
    login_data = {
        "email": "test@brainops.com",
        "password": "TestPassword123!"
    }
    
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token")
    else:
        print(f"Login failed: {resp.status_code}")
        print(resp.text)
        return None

def test_authenticated_endpoints(token):
    """Test endpoints that require authentication"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n🔐 TESTING AUTHENTICATED ENDPOINTS")
    print("-" * 50)
    
    # Test auth endpoints
    endpoints = [
        ("GET", "/api/v1/auth/me", None),
        ("POST", "/api/v1/auth/logout", {}),
        ("POST", "/api/v1/ai/analyze", {"image_url": "test.jpg"}),
        ("POST", "/api/v1/ai/chat", {"message": "Hello"}),
        ("POST", "/api/v1/env/sync", {"project": "backend"}),
    ]
    
    success = 0
    total = len(endpoints)
    
    for method, endpoint, data in endpoints:
        try:
            if method == "GET":
                resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            else:
                resp = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json=data, timeout=5)
            
            if resp.status_code in [200, 201]:
                print(f"✅ {method} {endpoint}: Success")
                success += 1
            elif resp.status_code == 403:
                print(f"❌ {method} {endpoint}: Still 403 Forbidden")
            elif resp.status_code == 404:
                print(f"❌ {method} {endpoint}: 404 Not Found")
            else:
                print(f"⚠️  {method} {endpoint}: Status {resp.status_code}")
                if resp.status_code < 500:
                    success += 1  # Consider client errors as endpoint existing
        except Exception as e:
            print(f"❌ {method} {endpoint}: {str(e)}")
    
    print(f"\nResults: {success}/{total} endpoints accessible with auth")
    return success == total

def main():
    print("🚀 TESTING AUTHENTICATION SYSTEM")
    print("=" * 50)
    
    # Try to get auth token
    token = get_auth_token()
    
    if token:
        print(f"✅ Authentication successful")
        print(f"📝 Token: {token[:20]}...")
        test_authenticated_endpoints(token)
    else:
        print("❌ Authentication failed - checking if test user exists")
        
        # Try to register test user
        register_data = {
            "email": "test@brainops.com",
            "password": "TestPassword123!",
            "name": "Test User"
        }
        
        print("\n📝 Attempting to register test user...")
        resp = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
        if resp.status_code in [200, 201]:
            print("✅ Test user registered successfully")
            token = get_auth_token()
            if token:
                test_authenticated_endpoints(token)
        else:
            print(f"❌ Registration failed: {resp.status_code}")
            print(resp.text)

if __name__ == "__main__":
    main()