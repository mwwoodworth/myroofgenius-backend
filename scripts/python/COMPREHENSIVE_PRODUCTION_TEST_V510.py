#!/usr/bin/env python3
"""
Comprehensive Production Test for BrainOps v5.10
Tests all critical endpoints and features
"""

import httpx
import json
from datetime import datetime
from typing import Dict, Any, List

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_endpoint(client: httpx.Client, method: str, path: str, **kwargs) -> Dict[str, Any]:
    """Test a single endpoint"""
    try:
        response = client.request(method, f"{BASE_URL}{path}", **kwargs)
        return {
            "path": path,
            "status": response.status_code,
            "success": response.status_code < 400,
            "data": response.json() if response.status_code == 200 else None,
            "error": response.text if response.status_code >= 400 else None
        }
    except Exception as e:
        return {
            "path": path,
            "status": 0,
            "success": False,
            "error": str(e)
        }

def run_tests():
    """Run all production tests"""
    print("🧪 COMPREHENSIVE PRODUCTION TEST v5.10")
    print("=" * 50)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 50)
    
    results = []
    
    with httpx.Client(timeout=30.0) as client:
        # 1. Core Health Checks
        print("\n📊 CORE HEALTH CHECKS")
        print("-" * 30)
        
        tests = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/database/status"),
        ]
        
        for method, path in tests:
            result = test_endpoint(client, method, path)
            results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"{status} {path}: {result['status']}")
        
        # 2. Public Endpoints (No Auth Required)
        print("\n🌐 PUBLIC ENDPOINTS")
        print("-" * 30)
        
        public_tests = [
            ("GET", "/api/v1/marketplace/products"),
            ("GET", "/api/v1/aurea/public/status"),
            ("POST", "/api/v1/aurea/public/chat", {"json": {"message": "Hello"}}),
        ]
        
        for test in public_tests:
            if len(test) == 2:
                method, path = test
                result = test_endpoint(client, method, path)
            else:
                method, path, kwargs = test
                result = test_endpoint(client, method, path, **kwargs)
            results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"{status} {path}: {result['status']}")
        
        # 3. Business Features
        print("\n💼 BUSINESS FEATURES")
        print("-" * 30)
        
        business_tests = [
            ("GET", "/api/v1/automations"),
            ("GET", "/api/v1/agents"),
            ("GET", "/api/v1/centerpoint/status"),
            ("POST", "/api/v1/marketplace/cart/add", {"params": {"product_id": 1}}),
            ("POST", "/api/v1/leads", {"json": {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "source": "api_test"
            }}),
        ]
        
        for test in business_tests:
            if len(test) == 2:
                method, path = test
                result = test_endpoint(client, method, path)
            else:
                method, path, kwargs = test
                result = test_endpoint(client, method, path, **kwargs)
            results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"{status} {path}: {result['status']}")
        
        # 4. Payment Features
        print("\n💳 PAYMENT FEATURES")
        print("-" * 30)
        
        payment_tests = [
            ("POST", "/api/v1/payments/create-intent", {"params": {"amount_cents": 10000}}),
            ("POST", "/api/v1/subscriptions/create", {"json": {
                "customer_email": "test@example.com",
                "plan": "premium",
                "price_cents": 9999
            }}),
        ]
        
        for test in payment_tests:
            method, path, kwargs = test
            result = test_endpoint(client, method, path, **kwargs)
            results.append(result)
            status = "✅" if result["success"] else "❌"
            print(f"{status} {path}: {result['status']}")
    
    # Summary
    print("\n📈 TEST SUMMARY")
    print("=" * 50)
    
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Check critical features
    print("\n🎯 CRITICAL FEATURES STATUS")
    print("-" * 30)
    
    health_check = any(r["path"] == "/api/v1/health" and r["success"] for r in results)
    db_connected = any(r["path"] == "/api/v1/database/status" and r["success"] for r in results)
    public_api = any(r["path"] == "/api/v1/aurea/public/status" and r["success"] for r in results)
    marketplace = any(r["path"] == "/api/v1/marketplace/products" and r["success"] for r in results)
    
    print(f"{'✅' if health_check else '❌'} Health Check API")
    print(f"{'✅' if db_connected else '❌'} Database Connection")
    print(f"{'✅' if public_api else '❌'} Public API Access")
    print(f"{'✅' if marketplace else '❌'} Marketplace Features")
    
    # Final verdict
    print("\n🏁 FINAL VERDICT")
    print("=" * 50)
    
    if success_rate >= 90:
        print("✅ PRODUCTION SYSTEM FULLY OPERATIONAL")
        print(f"🎉 v5.10 deployment successful with {success_rate:.1f}% success rate")
    elif success_rate >= 70:
        print("⚠️ SYSTEM OPERATIONAL WITH ISSUES")
        print(f"Some features may be degraded ({success_rate:.1f}% success rate)")
    else:
        print("❌ CRITICAL SYSTEM ISSUES")
        print(f"Multiple failures detected ({success_rate:.1f}% success rate)")
    
    # Show any errors
    errors = [r for r in results if not r["success"]]
    if errors:
        print("\n⚠️ FAILED ENDPOINTS:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error['path']}: {error.get('error', 'Unknown error')[:100]}")
    
    return success_rate

if __name__ == "__main__":
    success_rate = run_tests()
    exit(0 if success_rate >= 90 else 1)
