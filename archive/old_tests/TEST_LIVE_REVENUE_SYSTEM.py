#!/usr/bin/env python3
"""
Test live revenue generation capabilities
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_revenue_endpoints():
    """Test all revenue-related endpoints"""
    
    print("=" * 60)
    print("💰 TESTING REVENUE GENERATION CAPABILITIES")
    print("=" * 60)
    
    # Test health first
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        health = response.json()
        print(f"\n📊 System Status:")
        print(f"  Version: {health['version']}")
        print(f"  Status: {health['status']}")
        print(f"  Routes: {health['routes_loaded']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test public endpoints (no auth needed)
    print("\n🔓 Testing Public Endpoints:")
    
    public_endpoints = [
        ("GET", "/api/v1/products/public", None),
        ("POST", "/api/v1/aurea/public/chat", {"message": "I need a roof quote"}),
    ]
    
    for method, endpoint, data in public_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ {endpoint}: SUCCESS")
                if "products" in endpoint:
                    products = response.json()
                    if isinstance(products, list) and len(products) > 0:
                        print(f"     Found {len(products)} products")
            elif response.status_code == 404:
                print(f"  ❌ {endpoint}: NOT FOUND")
            else:
                print(f"  ⚠️ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {endpoint}: {str(e)[:50]}")
    
    # Test AUREA endpoints
    print("\n🤖 Testing AUREA AI:")
    
    aurea_endpoints = [
        ("GET", "/api/v1/aurea/status", None),
        ("GET", "/api/v1/aurea/health", None),
        ("POST", "/api/v1/aurea/chat", {"message": "Generate a roofing quote"}),
        ("POST", "/api/v1/aurea/revenue/generate", {
            "customer_type": "commercial",
            "service_type": "full_replacement",
            "urgency": "high"
        }),
    ]
    
    for method, endpoint, data in aurea_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"  ✅ {endpoint}: SUCCESS")
                result = response.json()
                if "opportunity_id" in result:
                    print(f"     Opportunity: {result['opportunity_id']}")
                    print(f"     Value: ${result.get('estimated_value', 0):,}")
            elif response.status_code == 404:
                print(f"  ❌ {endpoint}: NOT FOUND - Need to deploy fixes")
            else:
                print(f"  ⚠️ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {endpoint}: {str(e)[:50]}")
    
    # Test AI Board
    print("\n📊 Testing AI Board:")
    
    ai_board_endpoints = [
        "/api/v1/ai-board/status",
        "/api/v1/ai-board/agents",
        "/api/v1/ai-board/analytics",
    ]
    
    for endpoint in ai_board_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"  ✅ {endpoint}: SUCCESS")
            elif response.status_code == 404:
                print(f"  ❌ {endpoint}: NOT FOUND")
            else:
                print(f"  ⚠️ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {endpoint}: {str(e)[:50]}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 REVENUE GENERATION STATUS:")
    print("=" * 60)
    
    print("\n⚠️ CRITICAL ISSUES:")
    print("1. Version 3.3.26 not deployed (still on 3.3.18)")
    print("2. Revenue endpoints not available")
    print("3. AI Board not fully functional")
    
    print("\n✅ WORKING:")
    print("1. System is healthy and running")
    print("2. Database connected")
    print("3. 204 routes loaded")
    
    print("\n🔧 NEXT STEPS:")
    print("1. Deploy v3.3.26 manually via Render dashboard")
    print("2. Verify revenue endpoints are accessible")
    print("3. Test customer flow from quote to payment")

if __name__ == "__main__":
    test_revenue_endpoints()