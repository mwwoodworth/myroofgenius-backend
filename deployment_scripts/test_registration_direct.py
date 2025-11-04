#!/usr/bin/env python3
"""
Test registration directly with the API
"""

import requests
import time
import json

API_URL = "https://brainops-backend-prod.onrender.com"

def test_registration():
    """Test user registration"""
    print("Testing registration endpoint...")
    
    # Generate unique email
    test_email = f"test_user_{int(time.time())}@example.com"
    
    data = {
        "email": test_email,
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }
    
    try:
        resp = requests.post(
            f"{API_URL}/api/v1/auth/register",
            json=data,
            timeout=10
        )
        
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        
        if resp.status_code in [200, 201]:
            print("✅ Registration successful!")
            result = resp.json()
            print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
            print(f"User: {json.dumps(result.get('user', {}), indent=2)}")
        else:
            print("❌ Registration failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_registration()