#!/usr/bin/env python3
"""Register a test user via API"""
import requests
import json

print("Attempting to register test user...")

# Try to register a new user
response = requests.post(
    'https://brainops-backend-prod.onrender.com/api/v1/auth/register',
    json={
        'email': 'test@brainops.com',
        'password': 'TestPassword123!',
        'username': 'test'
    },
    timeout=10
)

print(f'Register Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print('✅ Registration successful!')
    print(f'Access Token: {data.get("access_token", "")[:40]}...')
    print(f'User: {json.dumps(data.get("user", {}), indent=2)}')
elif response.status_code == 400:
    print('User already exists (expected if previously registered)')
    print(f'Response: {response.text}')
else:
    print(f'Error Response: {response.text}')

# Now try to login
print("\nAttempting to login...")
login_response = requests.post(
    'https://brainops-backend-prod.onrender.com/api/v1/auth/login',
    json={
        'email': 'test@brainops.com',
        'password': 'TestPassword123!'
    },
    timeout=10
)

print(f'Login Status: {login_response.status_code}')
if login_response.status_code == 200:
    data = login_response.json()
    print('✅ Login successful!')
    print(f'Access Token: {data.get("access_token", "")[:40]}...')
    print(f'User: {json.dumps(data.get("user", {}), indent=2)}')
else:
    print(f'Login failed: {login_response.text}')