#!/usr/bin/env python3
"""
Test if the Vercel log endpoint exists and returns 200
"""
import requests

BACKEND_URL = "https://brainops-backend-prod.onrender.com"

print("Testing Vercel log drain endpoints...\n")

# Test 1: Check if endpoint exists
endpoints = [
    "/api/v1/logs/vercel",
    "/api/v1/webhooks/vercel",
    "/api/v1/vercel/logs",
    "/logs/vercel",
    "/webhooks/vercel-logs"
]

for endpoint in endpoints:
    url = f"{BACKEND_URL}{endpoint}"
    print(f"Testing: {url}")
    
    try:
        # Try POST (what Vercel will use)
        response = requests.post(url, json={}, timeout=5)
        print(f"  POST: {response.status_code}")
        
        if response.status_code == 200:
            print(f"  ✅ This endpoint should work! Use: {url}")
            break
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()

# If no endpoint works, we need to create one
print("\nIf none work, you need to either:")
print("1. Deploy the vercel_logs_simple.py route to backend")
print("2. Use an existing webhook endpoint that returns 200")
print("3. Create a simple catch-all webhook")

# Test the actual webhook endpoint
print("\nTesting generic webhook endpoint...")
webhook_url = f"{BACKEND_URL}/api/v1/webhooks/receive"
try:
    response = requests.post(webhook_url, json={"test": "vercel"}, timeout=5)
    print(f"Generic webhook: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ You could use: {webhook_url}")
except:
    print("❌ Generic webhook not available")