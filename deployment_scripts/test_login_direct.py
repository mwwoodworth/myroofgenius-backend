#!/usr/bin/env python3
"""
Test login directly with the API
"""

import requests
import json

API_URL = "https://brainops-backend-prod.onrender.com"

def test_login():
    """Test user login"""
    print("Testing login endpoint...")
    
    data = {
        "email": "test@brainops.com",
        "password": "TestPassword123!"
    }
    
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/auth/login",
            json=data,
            timeout=10
        )
        
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            print("✅ Login successful!")
            result = resp.json()
            print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
            print(f"User: {json.dumps(result.get('user', {}), indent=2)}")
        else:
            print("❌ Login failed")
            print(f"Response: {resp.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_login()