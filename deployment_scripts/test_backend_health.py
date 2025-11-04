#!/usr/bin/env python3

import requests
import json

# Backend API URL
backend_url = "https://brainops-backend-prod.onrender.com"

print("Testing BrainOps Backend API...\n")

# 1. Test health endpoint
print("1. Testing health endpoint...")
try:
    response = requests.get(f"{backend_url}/api/v1/health", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ API is healthy!")
        print(f"   Version: {data.get('version', 'unknown')}")
        print(f"   Status: {data.get('status', 'unknown')}")
        print(f"   Routes loaded: {data.get('routes_loaded', 0)}")
    else:
        print(f"   ❌ Health check failed: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Test memory endpoints
print("\n2. Testing memory endpoints...")
endpoints = [
    "/api/v1/memory/recent",
    "/api/v1/memory/insights",
    "/api/v1/memory/task-completion",
    "/api/v1/memory/error-log"
]

for endpoint in endpoints:
    try:
        response = requests.get(f"{backend_url}{endpoint}", timeout=5)
        print(f"   {endpoint}: {response.status_code} {'✅' if response.status_code in [200, 401, 403] else '❌'}")
    except Exception as e:
        print(f"   {endpoint}: ❌ Error - {e}")

# 3. Test AUREA status
print("\n3. Testing AUREA status...")
try:
    response = requests.get(f"{backend_url}/api/v1/aurea/status", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ AUREA is active: {data.get('active', False)}")
    else:
        print(f"   ❌ AUREA status check failed")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ Backend API test complete!")