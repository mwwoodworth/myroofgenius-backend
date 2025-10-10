#!/usr/bin/env python3
"""Test login endpoint for v3.1.230"""
import requests
import json

url = 'https://brainops-backend-prod.onrender.com/api/v1/auth/login'
data = {'email': 'test@brainops.com', 'password': 'TestPassword123!'}

print("Testing login endpoint...")
response = requests.post(url, json=data, timeout=10)
print(f"Status: {response.status_code}")

if response.status_code == 500:
    print("\nStill getting 500 error!")
    print("Response headers:")
    for key, value in response.headers.items():
        if key.lower() in ['x-process-time', 'cf-ray', 'rndr-id']:
            print(f"  {key}: {value}")
    
    # The response body is empty for 500 errors
    if response.text:
        print(f"\nResponse body: {response.text}")
    else:
        print("\nResponse body is empty (typical for 500 errors)")
elif response.status_code == 200:
    print("\nSUCCESS! Login is working!")
    data = response.json()
    print(f"Access token: {data.get('access_token', '')[:40]}...")
    print(f"User email: {data.get('user', {}).get('email', '')}")
else:
    print(f"\nUnexpected status: {response.status_code}")
    print(f"Response: {response.text}")