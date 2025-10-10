#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "https://brainops-backend-prod.onrender.com"
STRIPE_BASE = f"{BASE_URL}/api/v1/stripe-automation"

print("\n🧪 TESTING STRIPE AUTOMATION SYSTEM\n")

# Test health
try:
    response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
    if response.status_code == 200:
        print("✅ API is responding")
        data = response.json()
        print(f"   Version: {data.get('version')}")
except Exception as e:
    print(f"❌ API error: {e}")

# Test Stripe endpoints
endpoints = [
    "/health",
    "/analytics/revenue",
    "/analytics/subscriptions",
    "/automation/rules"
]

print("\nTesting Stripe endpoints:")
for endpoint in endpoints:
    try:
        response = requests.get(f"{STRIPE_BASE}{endpoint}", timeout=5)
        if response.status_code == 200:
            print(f"✅ {endpoint} - Working")
        else:
            print(f"❌ {endpoint} - Status {response.status_code}")
    except Exception as e:
        print(f"❌ {endpoint} - Error: {e}")

print("\n📝 Webhook URL for Stripe Dashboard:")
print(f"   {BASE_URL}/api/v1/stripe-automation/webhooks/stripe")
