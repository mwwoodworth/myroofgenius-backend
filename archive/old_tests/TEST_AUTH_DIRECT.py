#!/usr/bin/env python3
"""Direct test of authentication"""
import requests
import json

print("Testing authentication endpoints...")

# Test 1: Check auth status
print("\n1. Auth Status Check:")
status_response = requests.get(
    'https://brainops-backend-prod.onrender.com/api/v1/auth/status',
    timeout=5
)
print(f"   Status Code: {status_response.status_code}")
if status_response.status_code == 200:
    print(f"   Response: {json.dumps(status_response.json(), indent=2)}")

# Test 2: Register a completely new user
print("\n2. Register New User:")
import time
unique_email = f"test_{int(time.time())}@brainops.com"
register_response = requests.post(
    'https://brainops-backend-prod.onrender.com/api/v1/auth/register',
    json={
        'email': unique_email,
        'password': 'TestPassword123!',
        'username': f'test_{int(time.time())}'
    },
    timeout=10
)
print(f"   Status Code: {register_response.status_code}")
print(f"   Content Type: {register_response.headers.get('content-type')}")
print(f"   Content Length: {len(register_response.content)}")

if register_response.status_code == 200 and register_response.content:
    try:
        data = register_response.json()
        print("   ✅ Registration successful!")
        print(f"   Access Token: {data.get('access_token', '')[:40]}...")
        print(f"   User: {json.dumps(data.get('user', {}), indent=2)}")
        
        # Test 3: Login with the new user
        print("\n3. Login with New User:")
        login_response = requests.post(
            'https://brainops-backend-prod.onrender.com/api/v1/auth/login',
            json={
                'email': unique_email,
                'password': 'TestPassword123!'
            },
            timeout=10
        )
        print(f"   Status Code: {login_response.status_code}")
        if login_response.status_code == 200 and login_response.content:
            login_data = login_response.json()
            print("   ✅ Login successful!")
            print(f"   Access Token: {login_data.get('access_token', '')[:40]}...")
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON decode error: {e}")
        print(f"   Raw content: {register_response.content}")
else:
    print(f"   ❌ Registration failed")
    print(f"   Raw content: {register_response.content}")

# Test 4: Check what happens with invalid credentials
print("\n4. Invalid Login Test:")
invalid_response = requests.post(
    'https://brainops-backend-prod.onrender.com/api/v1/auth/login',
    json={
        'email': 'doesnotexist@example.com',
        'password': 'wrongpassword'
    },
    timeout=10
)
print(f"   Status Code: {invalid_response.status_code}")
print(f"   Content: {invalid_response.content}")
print(f"   Headers: {dict(invalid_response.headers)}")