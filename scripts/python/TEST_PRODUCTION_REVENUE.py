#!/usr/bin/env python3
"""
Complete Production Test Suite for Revenue System
Tests all revenue-generating endpoints
"""

import requests
import json
import time
from datetime import datetime, timezone
import stripe

# Configuration
BASE_URL = "https://brainops-backend-prod.onrender.com"
STRIPE_KEY = "sk_test_51PXs5fRw7K3sXkUXCHhxVqbRGKmNL8yBjNpHLxd4D5jRYaGLwmW"

# Initialize Stripe
stripe.api_key = STRIPE_KEY

def test_health():
    """Test API health"""
    print("🔍 Testing API Health...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        data = response.json()
        print(f"  ✅ API Version: {data.get('version', 'unknown')}")
        print(f"  ✅ Status: {data.get('status', 'unknown')}")
        print(f"  ✅ Loaded Routers: {data.get('loaded_routers', 0)}")
        return True
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return False

def test_revenue_dashboard():
    """Test revenue dashboard endpoint"""
    print("\n💰 Testing Revenue Dashboard...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/revenue/dashboard")
        if response.status_code == 200:
            data = response.json()
            metrics = data.get('metrics', {})
            print(f"  ✅ Total Revenue: ${metrics.get('total_revenue', 0):,.2f}")
            print(f"  ✅ Monthly Revenue: ${metrics.get('monthly_revenue', 0):,.2f}")
            print(f"  ✅ MRR: ${metrics.get('mrr', 0):,.2f}")
            print(f"  ✅ Growth Rate: {metrics.get('growth_rate', 0)}%")
            return True
        else:
            print(f"  ⚠️ Dashboard returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Dashboard test failed: {e}")
        return False

def test_marketplace_products():
    """Test marketplace products endpoint"""
    print("\n🛒 Testing Marketplace Products...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/marketplace/products")
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            print(f"  ✅ Products available: {len(products)}")
            for product in products[:3]:
                print(f"    • {product.get('name', 'Unknown')} - ${product.get('price', 0)}")
            return True
        else:
            print(f"  ⚠️ Marketplace returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Marketplace test failed: {e}")
        return False

def test_checkout_session():
    """Test creating a checkout session"""
    print("\n💳 Testing Checkout Session Creation...")
    try:
        payload = {
            "product_id": "shingle_001",
            "quantity": 10,
            "customer_email": "test@myroofgenius.com",
            "customer_name": "Test Customer"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/revenue/checkout/session",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Checkout URL: {data.get('checkout_url', 'N/A')[:50]}...")
            print(f"  ✅ Session ID: {data.get('session_id', 'N/A')}")
            return True
        else:
            print(f"  ⚠️ Checkout returned: {response.status_code}")
            try:
                print(f"    Response: {response.json()}")
            except:
                pass
            return False
    except Exception as e:
        print(f"  ❌ Checkout test failed: {e}")
        return False

def test_payment_intent():
    """Test creating a payment intent"""
    print("\n💸 Testing Payment Intent Creation...")
    try:
        payload = {
            "amount": 10000,  # $100.00
            "currency": "usd",
            "description": "Test roofing service payment"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/revenue/payment/intent",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Payment Intent ID: {data.get('payment_intent_id', 'N/A')}")
            print(f"  ✅ Amount: ${data.get('amount', 0) / 100:.2f}")
            print(f"  ✅ Client Secret: {data.get('client_secret', 'N/A')[:20]}...")
            return True
        else:
            print(f"  ⚠️ Payment intent returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Payment intent test failed: {e}")
        return False

def test_analytics():
    """Test analytics endpoint"""
    print("\n📊 Testing Analytics...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/analytics/overview")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Total Revenue: ${data.get('total_revenue', 0):,.2f}")
            print(f"  ✅ Conversion Rate: {data.get('conversion_rate', 0)}%")
            print(f"  ✅ Cart Abandonment: {data.get('cart_abandonment_rate', 0)}%")
            return True
        else:
            print(f"  ⚠️ Analytics returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Analytics test failed: {e}")
        return False

def test_memory_system():
    """Test memory system for AI persistence"""
    print("\n🧠 Testing Memory System...")
    try:
        # Test storing memory
        memory_payload = {
            "content": "Customer requested quote for full roof replacement",
            "memory_type": "customer_interaction",
            "tags": ["quote", "roof_replacement"],
            "importance": 0.8
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/memory/store",
            json=memory_payload
        )
        
        if response.status_code == 200:
            print(f"  ✅ Memory stored successfully")
        else:
            print(f"  ⚠️ Memory store returned: {response.status_code}")
        
        # Test retrieving memories
        response = requests.get(f"{BASE_URL}/api/v1/memory/recent?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Recent memories retrieved: {data.get('count', 0)}")
            return True
        else:
            print(f"  ⚠️ Memory retrieval returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Memory test failed: {e}")
        return False

def test_stripe_integration():
    """Test direct Stripe integration"""
    print("\n🏦 Testing Stripe Integration...")
    try:
        # List recent charges
        charges = stripe.Charge.list(limit=3)
        print(f"  ✅ Recent charges: {len(charges.data)}")
        
        # Check for active subscriptions
        subscriptions = stripe.Subscription.list(limit=3, status="active")
        print(f"  ✅ Active subscriptions: {len(subscriptions.data)}")
        
        # Check balance
        balance = stripe.Balance.retrieve()
        available = sum(b.amount for b in balance.available) / 100
        pending = sum(b.amount for b in balance.pending) / 100
        print(f"  ✅ Available balance: ${available:,.2f}")
        print(f"  ✅ Pending balance: ${pending:,.2f}")
        
        return True
    except Exception as e:
        print(f"  ❌ Stripe test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 MYROOFGENIUS PRODUCTION REVENUE SYSTEM TEST")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    results = {
        "Health Check": test_health(),
        "Revenue Dashboard": test_revenue_dashboard(),
        "Marketplace Products": test_marketplace_products(),
        "Checkout Session": test_checkout_session(),
        "Payment Intent": test_payment_intent(),
        "Analytics": test_analytics(),
        "Memory System": test_memory_system(),
        "Stripe Integration": test_stripe_integration()
    }
    
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 60)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is 100% PRODUCTION READY!")
        print("💰 Ready to generate REAL REVENUE!")
    elif passed >= total * 0.8:
        print("\n✅ System is mostly operational. Some features need attention.")
    else:
        print("\n⚠️ System needs immediate attention. Critical features failing.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()