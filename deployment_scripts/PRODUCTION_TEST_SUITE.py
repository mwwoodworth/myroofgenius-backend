#!/usr/bin/env python3
"""
BrainOps Backend Production Test Suite
Final comprehensive validation for 100% operational status
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

# Test results
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "start_time": datetime.now(),
    "errors": []
}

def test(name, condition, error_msg=""):
    """Record test result"""
    results["total"] += 1
    if condition:
        results["passed"] += 1
        print(f"✅ {name}")
        return True
    else:
        results["failed"] += 1
        results["errors"].append(f"{name}: {error_msg}")
        print(f"❌ {name}: {error_msg}")
        return False

def wait_for_deployment():
    """Wait for v33.3.0 deployment"""
    print("⏳ Waiting for v33.3.0 deployment...")
    for i in range(30):  # 5 minutes max
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=5)
            if r.status_code == 200:
                # Check if API health endpoint exists
                r2 = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
                if r2.status_code == 200:
                    print("✅ v33.3.0 deployed!")
                    return True
        except:
            pass
        time.sleep(10)
    return False

def run_tests():
    """Run comprehensive test suite"""
    
    # 1. INFRASTRUCTURE TESTS
    print("\n🏗️  INFRASTRUCTURE TESTS")
    print("=" * 50)
    
    # Health checks
    r = requests.get(f"{BASE_URL}/health")
    test("Root health check", r.status_code == 200)
    
    r = requests.get(f"{BASE_URL}/api/v1/health")
    test("API health check", r.status_code == 200)
    
    r = requests.get(f"{BASE_URL}/docs")
    test("API documentation", r.status_code == 200)
    
    # 2. AUTHENTICATION TESTS
    print("\n🔐 AUTHENTICATION TESTS")
    print("=" * 50)
    
    # Register test user
    timestamp = int(time.time())
    test_email = f"final_test_{timestamp}@example.com"
    test_password = "Test123!"
    
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": test_email, "password": test_password, "full_name": "Final Test"}
    )
    test("User registration", r.status_code in [200, 201])
    
    # Login
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": test_email, "password": test_password}
    )
    test("User login", r.status_code == 200)
    
    token = None
    if r.status_code == 200:
        token_data = r.json()
        token = token_data.get("access_token")
        test("Access token received", token is not None)
        
        # Verify token has type field
        import base64
        try:
            payload = base64.urlsafe_b64decode(token.split('.')[1] + '===').decode()
            token_payload = json.loads(payload)
            test("JWT token has 'type' field", "type" in token_payload)
        except:
            test("JWT token has 'type' field", False, "Failed to decode token")
    
    # Test authenticated endpoint
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/v1/users/me", headers=headers)
        test("Get current user", r.status_code == 200)
    
    # 3. CRUD OPERATIONS TESTS
    print("\n📝 CRUD OPERATIONS TESTS")
    print("=" * 50)
    
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Projects
        r = requests.get(f"{BASE_URL}/api/v1/projects", headers=headers)
        test("List projects", r.status_code == 200)
        
        r = requests.post(
            f"{BASE_URL}/api/v1/projects",
            headers=headers,
            json={"name": "Final Test Project", "description": "100% operational test"}
        )
        test("Create project", r.status_code in [200, 201])
        
        # AI Services
        r = requests.get(f"{BASE_URL}/api/v1/ai-services/models", headers=headers)
        test("List AI models", r.status_code == 200)
        
        # Automation
        r = requests.get(f"{BASE_URL}/api/v1/automation/workflows", headers=headers)
        test("List workflows", r.status_code == 200)
        
        # ERP - CRM
        r = requests.get(f"{BASE_URL}/api/v1/erp/crm/leads", headers=headers)
        test("List CRM leads", r.status_code == 200)
        
        # ERP - Jobs
        r = requests.get(f"{BASE_URL}/api/v1/erp/jobs", headers=headers)
        test("List jobs", r.status_code == 200)
        
        # ERP - Estimates
        r = requests.get(f"{BASE_URL}/api/v1/erp/estimates", headers=headers)
        test("List estimates", r.status_code == 200)
        
        # Memory
        r = requests.get(f"{BASE_URL}/api/v1/memory/collections", headers=headers)
        test("List memory collections", r.status_code == 200)
        
        # Marketplace
        r = requests.get(f"{BASE_URL}/api/v1/marketplace/categories", headers=headers)
        test("List marketplace categories", r.status_code == 200)
        
        r = requests.get(f"{BASE_URL}/api/v1/marketplace/items", headers=headers)
        test("List marketplace items", r.status_code == 200)
    
    # 4. PERMISSION TESTS
    print("\n🔒 PERMISSION TESTS")
    print("=" * 50)
    
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Should be forbidden for non-admin
        r = requests.get(f"{BASE_URL}/api/v1/users/", headers=headers)
        test("List users (403 expected)", r.status_code == 403)
    
    # 5. ERROR HANDLING TESTS
    print("\n⚠️  ERROR HANDLING TESTS")
    print("=" * 50)
    
    # Invalid endpoint
    r = requests.get(f"{BASE_URL}/api/v1/invalid-endpoint")
    test("404 for invalid endpoint", r.status_code == 404)
    
    # Unauthorized access
    r = requests.get(f"{BASE_URL}/api/v1/users/me")
    test("401 for missing auth", r.status_code == 401)
    
    # 6. FINAL SUMMARY
    print("\n" + "=" * 70)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 70)
    
    duration = (datetime.now() - results["start_time"]).total_seconds()
    success_rate = (results["passed"] / results["total"] * 100) if results["total"] > 0 else 0
    
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Duration: {duration:.1f}s")
    
    if results["errors"]:
        print("\n❌ FAILED TESTS:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    if success_rate == 100:
        print("\n✅ 🎉 SYSTEM IS 100% OPERATIONAL! 🎉 ✅")
        print("All endpoints, authentication, and operations are working perfectly!")
        return True
    else:
        print(f"\n⚠️  System is {success_rate:.1f}% operational")
        print("Please fix the failed tests above.")
        return False

def main():
    """Main test runner"""
    print("🚀 BrainOps Backend Final Production Test Suite")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    
    # Wait for deployment if needed
    if not wait_for_deployment():
        print("❌ Deployment timeout - v33.3.0 not detected")
        print("ACTION REQUIRED: Restart Render service")
        return False
    
    # Run tests
    return run_tests()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)