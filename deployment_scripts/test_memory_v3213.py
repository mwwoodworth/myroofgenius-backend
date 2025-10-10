#!/usr/bin/env python3
import requests
import json
import time

# Register a new user
register_url = 'https://brainops-backend-prod.onrender.com/api/v1/auth/register'
register_data = {
    'email': f'test_v3213_{int(time.time())}@example.com',
    'password': 'TestPassword123!',
    'full_name': 'Test User v3.1.213'
}

response = requests.post(register_url, json=register_data)
if response.status_code == 200:
    token = response.json()['access_token']
    print('Registration successful')
    
    # Test memory create
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'title': 'Test Memory v3.1.213',
        'content': 'Testing memory with final service',
        'memory_type': 'test',
        'role': 'system'
    }
    
    response = requests.post(
        'https://brainops-backend-prod.onrender.com/api/v1/memory/create',
        headers=headers,
        json=data
    )
    
    print(f'Memory Create Status: {response.status_code}')
    if response.status_code != 200:
        print(f'Error Response: {response.text}')
    else:
        print('Success!')
        memory = response.json()
        print(f'Memory ID: {memory.get("id")}')
        print(f'Memory Title: {memory.get("title")}')
else:
    print(f'Registration failed: {response.status_code} - {response.text}')