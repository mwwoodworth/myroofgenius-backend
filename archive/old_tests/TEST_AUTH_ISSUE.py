#!/usr/bin/env python3
"""
Test authentication issue directly
"""
import requests
import json

BACKEND_URL = "https://brainops-backend-prod.onrender.com"

print("🔍 TESTING AUTHENTICATION ISSUE")
print("=" * 50)

# Test 1: Check if auth endpoint exists
print("\n1. Checking if auth endpoint exists:")
try:
    response = requests.options(f"{BACKEND_URL}/api/v1/auth/login", timeout=5)
    print(f"   OPTIONS request status: {response.status_code}")
    if 'allow' in response.headers:
        print(f"   Allowed methods: {response.headers['allow']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Try login with different content types
print("\n2. Testing login with different approaches:")

# Test 2a: Standard JSON
print("\n   a) Standard JSON:")
try:
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"email": "test@brainops.com", "password": "TestPassword123!"},
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    print(f"      Status: {response.status_code}")
    if response.status_code != 200:
        print(f"      Headers: {dict(response.headers)}")
        print(f"      Response: {response.text[:500]}")
except Exception as e:
    print(f"      ❌ Error: {e}")

# Test 2b: Form data (OAuth2 style)
print("\n   b) Form data (OAuth2):")
try:
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        data={
            "username": "test@brainops.com",
            "password": "TestPassword123!"
        },
        timeout=10
    )
    print(f"      Status: {response.status_code}")
    if response.status_code != 200:
        print(f"      Response: {response.text[:500]}")
except Exception as e:
    print(f"      ❌ Error: {e}")

# Test 3: Check other auth endpoints
print("\n3. Checking other auth endpoints:")
endpoints = [
    ("/api/v1/auth/register", "POST"),
    ("/api/v1/auth/refresh", "POST"),
    ("/api/v1/auth/logout", "POST"),
    ("/api/v1/auth-debug/status", "GET"),
]

for endpoint, method in endpoints:
    try:
        if method == "GET":
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
        else:
            response = requests.post(f"{BACKEND_URL}{endpoint}", json={}, timeout=5)
        print(f"   {endpoint}: {response.status_code}")
    except Exception as e:
        print(f"   {endpoint}: ❌ Error - {e}")

# Test 4: Check if it's a database issue
print("\n4. Testing database connection:")
try:
    response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   Database status: {data.get('database', 'unknown')}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("🔍 ANALYSIS COMPLETE")