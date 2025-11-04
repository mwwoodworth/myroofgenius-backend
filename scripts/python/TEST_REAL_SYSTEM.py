#!/usr/bin/env python3
"""
Test the REAL working system
No fake endpoints, only what actually works
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data['status']}")
            print(f"✅ Version: {data['version']}")
            print(f"✅ Loaded routers: {data['loaded_routers']}")
            print(f"✅ Real features: {', '.join(data.get('real_features', []))}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_revenue():
    """Test revenue endpoints"""
    print("\n💰 Testing Revenue System...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/revenue/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Revenue status: {data['status']}")
            print(f"✅ Stripe configured: {data['stripe_configured']}")
            print(f"✅ Automation enabled: {data['automation_enabled']}")
            return True
        else:
            print(f"❌ Revenue status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Revenue test error: {str(e)}")
        return False

def test_estimates():
    """Test estimates endpoints"""
    print("\n📋 Testing Estimates System...")
    
    # Test quick price
    try:
        response = requests.get(f"{BASE_URL}/api/v1/estimates/quick-price/2000?roof_type=shingle")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Quick price for 2000 sqft shingle roof:")
            print(f"   Materials: ${data['materials']:.2f}")
            print(f"   Labor: ${data['labor']:.2f}")
            print(f"   Total: ${data['total']:.2f}")
        else:
            print(f"❌ Quick price failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Quick price error: {str(e)}")
        return False
    
    # Test create estimate
    try:
        estimate_data = {
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "address": "123 Main St",
            "roof_size_sqft": 2000,
            "roof_type": "shingle",
            "items": [
                {
                    "description": "Shingle removal",
                    "quantity": 2000,
                    "unit_price": 0.50,
                    "total": 1000.00
                },
                {
                    "description": "New shingles",
                    "quantity": 2000,
                    "unit_price": 3.50,
                    "total": 7000.00
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/estimates/create",
            json=estimate_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Created estimate ID: {data['id']}")
            print(f"   Customer: {data['customer_name']}")
            print(f"   Total: ${data['total']:.2f}")
            return True
        else:
            print(f"❌ Create estimate failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Create estimate error: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🔍 TESTING REAL WORKING SYSTEM")
    print(f"📍 Backend: {BASE_URL}")
    print(f"📅 Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    results = []
    
    # Test all real endpoints
    results.append(("Health", test_health()))
    results.append(("Revenue", test_revenue()))
    results.append(("Estimates", test_estimates()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}: {'PASSED' if result else 'FAILED'}")
    
    print(f"\n🎯 Total: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - SYSTEM IS WORKING!")
    else:
        print("⚠️ Some tests failed - needs investigation")

if __name__ == "__main__":
    main()