#!/usr/bin/env python3
"""
Complete Live System Test - v4.25
Tests all production endpoints and functionality
"""

import requests
import json
from datetime import datetime
import sys

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_endpoint(name, method, path, data=None, headers=None):
    """Test an endpoint and return result"""
    url = f"{BASE_URL}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.request(method, url, json=data, headers=headers)
        
        status = "✅" if response.status_code in [200, 201] else "❌"
        print(f"{status} {name}: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and len(data) > 0:
                    # Show first few keys
                    keys = list(data.keys())[:5]
                    print(f"    Response keys: {keys}")
            except:
                pass
        elif response.status_code != 200:
            try:
                error = response.json()
                print(f"    Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"    Response: {response.text[:100]}")
        
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🔍 LIVE SYSTEM TEST - v4.25")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print()
    
    results = []
    
    # Core Health
    print("📊 CORE SYSTEM:")
    results.append(test_endpoint("Health Check", "GET", "/api/v1/health"))
    results.append(test_endpoint("Version", "GET", "/api/v1/version"))
    print()
    
    # Revenue System
    print("💰 REVENUE SYSTEM:")
    results.append(test_endpoint("Revenue Status", "GET", "/api/v1/revenue/status"))
    results.append(test_endpoint("Revenue Config", "GET", "/api/v1/revenue/config"))
    results.append(test_endpoint("Revenue Stats", "GET", "/api/v1/revenue/stats"))
    results.append(test_endpoint("Revenue Metrics", "GET", "/api/v1/revenue/metrics"))
    
    # Test checkout (should fail without proper data)
    checkout_data = {
        "price_id": "price_test",
        "customer_email": "test@example.com",
        "success_url": "https://myroofgenius.com/success",
        "cancel_url": "https://myroofgenius.com/cancel"
    }
    results.append(test_endpoint("Checkout Session", "POST", "/api/v1/revenue/checkout/session", checkout_data))
    print()
    
    # Environment Master
    print("🔧 ENVIRONMENT SYSTEM:")
    results.append(test_endpoint("Env Health", "GET", "/api/v1/env/health"))
    results.append(test_endpoint("Env All", "GET", "/api/v1/env/all"))
    results.append(test_endpoint("Env Stats", "GET", "/api/v1/env/stats"))
    print()
    
    # Products
    print("📦 PRODUCTS:")
    results.append(test_endpoint("Products List", "GET", "/api/v1/products"))
    results.append(test_endpoint("Products Public", "GET", "/api/v1/products/public"))
    results.append(test_endpoint("Marketplace Products", "GET", "/api/v1/marketplace/products"))
    print()
    
    # AI Systems
    print("🤖 AI SYSTEMS:")
    results.append(test_endpoint("AI Status", "GET", "/api/v1/ai/status"))
    results.append(test_endpoint("AUREA Status", "GET", "/api/v1/aurea/status"))
    results.append(test_endpoint("AUREA Health", "GET", "/api/v1/aurea/health"))
    print()
    
    # Automation
    print("⚙️ AUTOMATION:")
    results.append(test_endpoint("Automation Status", "GET", "/api/v1/automations/status"))
    results.append(test_endpoint("Automation Rules", "GET", "/api/v1/automations/rules"))
    print()
    
    # Estimates
    print("💵 ESTIMATES:")
    results.append(test_endpoint("Quick Price", "GET", "/api/v1/estimates/quick-price/2000"))
    results.append(test_endpoint("Estimate Calc", "POST", "/api/v1/estimates/calculate", {
        "square_feet": 2000,
        "material": "asphalt_shingle",
        "complexity": "standard"
    }))
    print()
    
    # Memory System
    print("🧠 MEMORY:")
    results.append(test_endpoint("Memory Recent", "GET", "/api/v1/memory/recent"))
    results.append(test_endpoint("Memory Stats", "GET", "/api/v1/memory/stats"))
    print()
    
    # Task OS
    print("📋 TASK OS:")
    results.append(test_endpoint("Tasks List", "GET", "/api/v1/tasks"))
    results.append(test_endpoint("Tasks Stats", "GET", "/api/v1/tasks/stats"))
    print()
    
    # Analytics
    print("📈 ANALYTICS:")
    results.append(test_endpoint("Analytics Overview", "GET", "/api/v1/analytics/overview"))
    results.append(test_endpoint("Analytics Revenue", "GET", "/api/v1/analytics/revenue"))
    print()
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY:")
    passed = sum(1 for r in results if r)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Passed: {passed}/{total} ({percentage:.1f}%)")
    
    if percentage == 100:
        print("🎉 ALL TESTS PASSED! System is fully operational!")
    elif percentage >= 80:
        print("✅ System is mostly operational with minor issues")
    elif percentage >= 60:
        print("⚠️ System has significant issues that need attention")
    else:
        print("❌ System has critical failures")
    
    print("=" * 60)
    
    # Check specific critical systems
    print()
    print("🎯 CRITICAL SYSTEMS STATUS:")
    
    # Revenue
    response = requests.get(f"{BASE_URL}/api/v1/revenue/status")
    if response.status_code == 200:
        data = response.json()
        if data.get('stripe_configured'):
            print("✅ Stripe is configured and ready")
        else:
            print("❌ Stripe is not configured")
    
    # Environment sync
    response = requests.get(f"{BASE_URL}/api/v1/env/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Environment Master: {data.get('active_variables', 0)} variables loaded")
    else:
        print("❌ Environment Master is not accessible")
    
    # Products
    response = requests.get(f"{BASE_URL}/api/v1/products")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict) and 'products' in data:
            print(f"✅ Products: {len(data['products'])} products available")
        elif isinstance(data, list):
            print(f"✅ Products: {len(data)} products available")
    
    print("=" * 60)
    
    return 0 if percentage >= 70 else 1

if __name__ == "__main__":
    sys.exit(main())