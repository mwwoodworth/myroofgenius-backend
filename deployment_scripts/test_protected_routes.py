#!/usr/bin/env python3
"""
Test protected routes with fixed authentication
"""

import requests
import json

API_URL = "https://brainops-backend-prod.onrender.com"

def test_login_and_protected_routes():
    """Test login and then access protected routes"""
    
    # Step 1: Login
    print("1. Testing login...")
    login_data = {
        "email": "test@brainops.com",
        "password": "TestPassword123!"
    }
    
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/auth/login",
            json=login_data,
            timeout=10
        )
        
        if resp.status_code == 200:
            print("✅ Login successful!")
            tokens = resp.json()
            access_token = tokens.get('access_token')
            print(f"Access Token: {access_token[:50]}...")
        else:
            print(f"❌ Login failed: {resp.status_code}")
            print(resp.text)
            return
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return
    
    # Step 2: Test protected routes
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    protected_routes = [
        ("/api/v1/users/me", "User Profile"),
        ("/api/v1/aurea/chat", "AUREA Chat"),
        ("/api/v1/memory/create", "Memory Create"),
        ("/api/v1/memory/recent", "Memory Recent"),
        ("/api/v1/tasks", "Tasks List"),
        ("/api/v1/projects", "Projects List")
    ]
    
    print("\n2. Testing protected routes...")
    for route, name in protected_routes:
        try:
            if route == "/api/v1/aurea/chat":
                # AUREA chat needs a POST with message
                resp = requests.post(
                    f"{API_URL}{route}",
                    headers=headers,
                    json={"message": "Hello AUREA"},
                    timeout=10
                )
            elif route == "/api/v1/memory/create":
                # Memory create needs POST with data
                resp = requests.post(
                    f"{API_URL}{route}",
                    headers=headers,
                    json={
                        "title": "Test Memory",
                        "content": "Testing protected route",
                        "role": "user"
                    },
                    timeout=10
                )
            else:
                # Regular GET request
                resp = requests.get(
                    f"{API_URL}{route}",
                    headers=headers,
                    timeout=10
                )
            
            if resp.status_code == 200:
                print(f"✅ {name}: Success")
            elif resp.status_code == 401:
                print(f"❌ {name}: Unauthorized (auth issue)")
            elif resp.status_code == 404:
                print(f"⚠️  {name}: Not Found (route missing)")
            elif resp.status_code == 500:
                print(f"❌ {name}: Server Error (needs fix)")
                print(f"   Error: {resp.text[:200]}")
            else:
                print(f"❌ {name}: Status {resp.status_code}")
                
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")

if __name__ == "__main__":
    test_login_and_protected_routes()