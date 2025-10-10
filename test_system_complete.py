#!/usr/bin/env python3
"""
Complete system test after auth fix deployment
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_endpoint(method, path, data=None, headers=None):
    """Test an endpoint and return result"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return False, "Unknown method"
        
        return response.status_code, response.text[:200] if response.text else "Empty"
    except Exception as e:
        return None, str(e)

print("\n" + "="*80)
print("🔍 BrainOps Backend Complete System Test")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Test authentication first
print("\n1️⃣ AUTHENTICATION TEST")
print("-"*40)

auth_data = {
    "email": "test@brainops.com",
    "password": "TestPassword123!"
}

status, response = test_endpoint("POST", "/api/v1/auth/login", auth_data)
access_token = None

if status == 200:
    print(f"✅ Login successful!")
    try:
        token_data = json.loads(response)
        access_token = token_data.get("access_token")
        print(f"   Token: {access_token[:50]}...")
    except:
        print("   ⚠️ Could not parse token")
else:
    print(f"❌ Login failed: {status}")

# Test authenticated endpoint
if access_token:
    headers = {"Authorization": f"Bearer {access_token}"}
    status, response = test_endpoint("GET", "/api/v1/auth/me", headers=headers)
    if status == 200:
        print("✅ Auth verification successful!")
    else:
        print(f"❌ Auth verification failed: {status}")

# Test other endpoints
print("\n2️⃣ CORE ENDPOINTS")
print("-"*40)

endpoints = [
    ("GET", "/api/v1/health", "Health Check"),
    ("GET", "/api/v1/crm/customers?limit=1", "Customers"),
    ("GET", "/api/v1/erp/jobs?limit=1", "Jobs"),
    ("GET", "/api/v1/erp/invoices?limit=1", "Invoices"),
    ("GET", "/api/v1/erp/estimates?limit=1", "Estimates"),
    ("GET", "/api/v1/ai/agents", "AI Agents"),
    ("GET", "/api/v1/revenue/metrics", "Revenue Metrics"),
    ("GET", "/api/v1/products", "Products"),
    ("GET", "/api/v1/inventory", "Inventory")
]

passed = 0
failed = 0

for method, path, name in endpoints:
    status, response = test_endpoint(method, path)
    if status and status < 500:
        print(f"✅ {name}: {status}")
        passed += 1
    else:
        print(f"❌ {name}: {status if status else 'Error'}")
        failed += 1

print("\n3️⃣ SYSTEM SUMMARY")
print("-"*40)

# Check specific counts
status, response = test_endpoint("GET", "/api/v1/health")
if status == 200:
    try:
        health_data = json.loads(response)
        stats = health_data.get("stats", {})
        print(f"📊 Database Stats:")
        print(f"   • Customers: {stats.get('customers', 0):,}")
        print(f"   • Jobs: {stats.get('jobs', 0):,}")
        print(f"   • Invoices: {stats.get('invoices', 0):,}")
        print(f"   • AI Agents: {stats.get('ai_agents', 0):,}")
    except:
        pass

total = passed + failed
success_rate = (passed / total * 100) if total > 0 else 0

print(f"\n📈 Test Results:")
print(f"   ✅ Passed: {passed}/{total}")
print(f"   ❌ Failed: {failed}/{total}")
print(f"   📊 Success Rate: {success_rate:.1f}%")

if success_rate >= 80:
    print("\n✅ SYSTEM IS OPERATIONAL")
elif success_rate >= 60:
    print("\n⚠️ SYSTEM IS PARTIALLY OPERATIONAL")
else:
    print("\n❌ SYSTEM HAS CRITICAL ISSUES")

print("\n" + "="*80)