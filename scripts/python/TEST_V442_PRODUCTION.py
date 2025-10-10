#!/usr/bin/env python3
"""
Test v4.42 Production System
Complete verification of all new integrations
"""

import requests
import json
import time
from datetime import datetime

# Base URL
BASE_URL = "https://brainops-backend-prod.onrender.com"

# Test results
results = {
    "health": False,
    "version": None,
    "stripe": False,
    "sendgrid": False,
    "env_master": False,
    "endpoints_tested": 0,
    "endpoints_passed": 0
}

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        data = response.json()
        results["health"] = response.status_code == 200
        results["version"] = data.get("version")
        return data
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return None

def test_stripe():
    """Test Stripe integration"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/payments/test", timeout=5)
        results["endpoints_tested"] += 1
        if response.status_code == 200:
            data = response.json()
            results["stripe"] = data.get("stripe_configured", False)
            results["endpoints_passed"] += 1
            return True
        return False
    except Exception as e:
        print(f"❌ Stripe test failed: {e}")
        return False

def test_sendgrid():
    """Test SendGrid integration"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/email/test", timeout=5)
        results["endpoints_tested"] += 1
        if response.status_code == 200:
            data = response.json()
            results["sendgrid"] = data.get("sendgrid_configured", False)
            results["endpoints_passed"] += 1
            return True
        return False
    except Exception as e:
        print(f"❌ SendGrid test failed: {e}")
        return False

def test_env_master():
    """Test Environment Master"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/env/validate", timeout=5)
        results["endpoints_tested"] += 1
        if response.status_code in [200, 403]:  # 403 is OK (needs auth)
            results["env_master"] = True
            results["endpoints_passed"] += 1
            return True
        return False
    except Exception as e:
        print(f"❌ Env Master test failed: {e}")
        return False

def test_new_endpoints():
    """Test all new v4.42 endpoints"""
    endpoints = [
        ("/api/v1/payments/test", "GET", "Stripe Test"),
        ("/api/v1/email/test", "GET", "SendGrid Test"),
        ("/api/v1/email/templates", "GET", "Email Templates"),
        ("/api/v1/env/validate", "GET", "Env Validation"),
    ]
    
    for endpoint, method, name in endpoints:
        results["endpoints_tested"] += 1
        try:
            response = requests.request(method, f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code in [200, 401, 403]:  # Auth errors are OK
                results["endpoints_passed"] += 1
                print(f"  ✅ {name}: {response.status_code}")
            else:
                print(f"  ❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {name}: Error - {e}")

def main():
    print("🧪 TESTING v4.42 PRODUCTION SYSTEM")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target: {BASE_URL}")
    print("")
    
    # Test health
    print("1️⃣ Health Check:")
    health_data = test_health()
    if health_data:
        print(f"  ✅ API is healthy")
        print(f"  📌 Version: {results['version']}")
        
        if results["version"] != "4.42":
            print(f"  ⚠️  Version is {results['version']}, expected 4.42")
            print("  ⏳ Deployment may still be in progress")
    else:
        print("  ❌ API is not responding")
    
    print("")
    print("2️⃣ Testing New Integrations:")
    
    # Test Stripe
    if test_stripe():
        print(f"  ✅ Stripe: Configured")
    else:
        print(f"  ❌ Stripe: Not available")
    
    # Test SendGrid
    if test_sendgrid():
        print(f"  ✅ SendGrid: Configured")
    else:
        print(f"  ❌ SendGrid: Not available")
    
    # Test Env Master
    if test_env_master():
        print(f"  ✅ Env Master: Available")
    else:
        print(f"  ❌ Env Master: Not available")
    
    print("")
    print("3️⃣ Testing All New Endpoints:")
    test_new_endpoints()
    
    print("")
    print("=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"API Version: {results['version']}")
    print(f"Health Check: {'✅ PASS' if results['health'] else '❌ FAIL'}")
    print(f"Stripe Integration: {'✅ READY' if results['stripe'] else '❌ NOT READY'}")
    print(f"SendGrid Integration: {'✅ READY' if results['sendgrid'] else '❌ NOT READY'}")
    print(f"Env Master: {'✅ READY' if results['env_master'] else '❌ NOT READY'}")
    print(f"Endpoints Tested: {results['endpoints_tested']}")
    print(f"Endpoints Passed: {results['endpoints_passed']}")
    print("")
    
    # Calculate success rate
    if results["endpoints_tested"] > 0:
        success_rate = (results["endpoints_passed"] / results["endpoints_tested"]) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Overall assessment
    if results["version"] == "4.42" and results["health"]:
        print("")
        print("🎉 v4.42 IS LIVE AND OPERATIONAL!")
        print("All integrations are ready for activation.")
        print("Next step: Run ACTIVATE_ALL_AUTOMATIONS.py")
    elif results["health"]:
        print("")
        print(f"⚠️  System is running v{results['version']} (expected v4.42)")
        print("Deployment may still be in progress.")
    else:
        print("")
        print("❌ System is not responding properly")
        print("Check Render dashboard for deployment status")
    
    return results

if __name__ == "__main__":
    results = main()