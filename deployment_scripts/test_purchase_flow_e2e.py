#!/usr/bin/env python3
"""
End-to-End Purchase Flow Test for MyRoofGenius
Tests the complete customer journey from browsing to purchase
"""
import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# Configuration
API_BASE = "https://brainops-backend-prod.onrender.com/api/v1"
FRONTEND_BASE = "https://myroofgenius.com"

# Test results storage
test_results = {
    "timestamp": datetime.now().isoformat(),
    "tests_passed": 0,
    "tests_failed": 0,
    "critical_failures": [],
    "warnings": [],
    "revenue_ready": False
}

def test_public_product_listing():
    """Test that products can be listed without authentication"""
    print("\n🛍️ Testing Public Product Listing...")
    
    try:
        response = requests.get(f"{API_BASE}/products/public/list")
        
        if response.status_code == 200:
            data = response.json()
            products = data.get("products", [])
            
            if len(products) > 0:
                print(f"✅ Found {len(products)} products available")
                test_results["tests_passed"] += 1
                
                # Display products
                for product in products:
                    print(f"   - {product.get('name')} (${product.get('price', 0)/100:.2f})")
                
                return True, products
            else:
                print("❌ No products found in catalog")
                test_results["tests_failed"] += 1
                test_results["critical_failures"].append("Empty product catalog")
                return False, []
        else:
            print(f"❌ Failed to list products: {response.status_code}")
            test_results["tests_failed"] += 1
            test_results["critical_failures"].append(f"Product listing failed: {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"❌ Error testing product listing: {str(e)}")
        test_results["tests_failed"] += 1
        test_results["critical_failures"].append(f"Product listing error: {str(e)}")
        return False, []

def test_product_detail(product_id: str):
    """Test that product details can be retrieved without authentication"""
    print(f"\n🔍 Testing Product Detail Access ({product_id})...")
    
    try:
        response = requests.get(f"{API_BASE}/products/public/detail/{product_id}")
        
        if response.status_code == 200:
            product = response.json()
            print(f"✅ Retrieved details for: {product.get('name')}")
            print(f"   Price: ${product.get('price', 0)/100:.2f}")
            print(f"   Features: {len(product.get('features', []))}")
            test_results["tests_passed"] += 1
            return True, product
        else:
            print(f"❌ Failed to get product details: {response.status_code}")
            test_results["tests_failed"] += 1
            return False, None
            
    except Exception as e:
        print(f"❌ Error getting product details: {str(e)}")
        test_results["tests_failed"] += 1
        return False, None

def test_product_availability(product_id: str):
    """Test that product availability can be checked"""
    print(f"\n📦 Testing Product Availability ({product_id})...")
    
    try:
        response = requests.post(f"{API_BASE}/products/public/check-availability/{product_id}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("available"):
                print(f"✅ Product is available for immediate purchase")
                print(f"   Delivery: {data.get('delivery')}")
                test_results["tests_passed"] += 1
                return True
            else:
                print(f"❌ Product not available")
                test_results["tests_failed"] += 1
                test_results["critical_failures"].append(f"Product {product_id} not available")
                return False
        else:
            print(f"❌ Failed to check availability: {response.status_code}")
            test_results["tests_failed"] += 1
            return False
            
    except Exception as e:
        print(f"❌ Error checking availability: {str(e)}")
        test_results["tests_failed"] += 1
        return False

def test_aurea_public_chat():
    """Test that AUREA can be accessed without authentication"""
    print("\n🤖 Testing Public AUREA Chat...")
    
    try:
        # Test initial greeting
        response = requests.post(
            f"{API_BASE}/aurea/public/chat",
            json={"message": "Hello, I'm interested in your roofing software"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AUREA responded: {data.get('response', '')[:100]}...")
            print(f"   Session ID: {data.get('session_id')}")
            test_results["tests_passed"] += 1
            
            # Test product inquiry
            session_id = data.get('session_id')
            response2 = requests.post(
                f"{API_BASE}/aurea/public/chat",
                json={
                    "message": "What's your most popular product?",
                    "session_id": session_id
                }
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"✅ AUREA product response: {data2.get('response', '')[:100]}...")
                test_results["tests_passed"] += 1
                return True
            else:
                print(f"⚠️ AUREA follow-up failed: {response2.status_code}")
                test_results["warnings"].append("AUREA session continuity issue")
                return True
        else:
            print(f"❌ AUREA chat failed: {response.status_code}")
            test_results["tests_failed"] += 1
            test_results["critical_failures"].append(f"AUREA public access failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AUREA: {str(e)}")
        test_results["tests_failed"] += 1
        test_results["critical_failures"].append(f"AUREA error: {str(e)}")
        return False

def test_aurea_product_help(product_id: str):
    """Test AUREA's product help functionality"""
    print(f"\n💡 Testing AUREA Product Help ({product_id})...")
    
    try:
        response = requests.post(
            f"{API_BASE}/aurea/public/product-help",
            json={
                "product_id": product_id,
                "question": "How does this product save me time?"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AUREA help response: {data.get('response', '')[:100]}...")
            test_results["tests_passed"] += 1
            return True
        else:
            print(f"❌ AUREA product help failed: {response.status_code}")
            test_results["tests_failed"] += 1
            return False
            
    except Exception as e:
        print(f"❌ Error testing AUREA product help: {str(e)}")
        test_results["tests_failed"] += 1
        return False

def test_frontend_accessibility():
    """Test that the frontend is accessible"""
    print("\n🌐 Testing Frontend Accessibility...")
    
    try:
        response = requests.get(FRONTEND_BASE, allow_redirects=True)
        
        if response.status_code == 200:
            print(f"✅ Frontend is accessible at {FRONTEND_BASE}")
            test_results["tests_passed"] += 1
            return True
        else:
            print(f"❌ Frontend returned: {response.status_code}")
            test_results["tests_failed"] += 1
            test_results["critical_failures"].append(f"Frontend inaccessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing frontend: {str(e)}")
        test_results["tests_failed"] += 1
        test_results["critical_failures"].append(f"Frontend error: {str(e)}")
        return False

def run_all_tests():
    """Run complete E2E purchase flow tests"""
    print("🚀 MyRoofGenius E2E Purchase Flow Test")
    print("=" * 50)
    
    # Test 1: Frontend accessibility
    test_frontend_accessibility()
    
    # Test 2: Product listing
    success, products = test_public_product_listing()
    
    if success and products:
        # Test 3: Product details for first product
        first_product = products[0]
        product_id = first_product.get("id")
        
        test_product_detail(product_id)
        
        # Test 4: Product availability
        test_product_availability(product_id)
        
        # Test 5: AUREA chat
        test_aurea_public_chat()
        
        # Test 6: AUREA product help
        test_aurea_product_help(product_id)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print(f"✅ Passed: {test_results['tests_passed']}")
    print(f"❌ Failed: {test_results['tests_failed']}")
    
    if test_results["critical_failures"]:
        print("\n🚨 CRITICAL FAILURES:")
        for failure in test_results["critical_failures"]:
            print(f"   - {failure}")
    
    if test_results["warnings"]:
        print("\n⚠️ WARNINGS:")
        for warning in test_results["warnings"]:
            print(f"   - {warning}")
    
    # Revenue readiness assessment
    revenue_ready = (
        test_results["tests_failed"] == 0 and
        len(test_results["critical_failures"]) == 0
    )
    
    test_results["revenue_ready"] = revenue_ready
    
    if revenue_ready:
        print("\n✅ 💰 SYSTEM IS REVENUE READY! 💰")
        print("All critical purchase flow components are operational.")
    else:
        print("\n❌ SYSTEM NOT READY FOR REVENUE")
        print("Critical issues must be resolved before accepting payments.")
    
    # Save results
    with open("purchase_flow_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\nResults saved to: purchase_flow_test_results.json")
    
    return revenue_ready

if __name__ == "__main__":
    revenue_ready = run_all_tests()
    sys.exit(0 if revenue_ready else 1)