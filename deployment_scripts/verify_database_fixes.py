#!/usr/bin/env python3
"""
Verify database fixes and test system functionality
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_endpoint(name, url, method="GET", data=None, headers=None):
    """Test an endpoint and report results"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        success = response.status_code in [200, 201]
        print(f"\n{'✅' if success else '❌'} {name}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200 and len(response.text) < 500:
            try:
                print(f"   Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"   Response: {response.text[:200]}")
        elif not success:
            print(f"   Error: {response.text[:200]}")
        
        return success, response
    except Exception as e:
        print(f"\n❌ {name}")
        print(f"   Error: {str(e)}")
        return False, None

def main():
    print("=" * 60)
    print("🔍 BrainOps Database Fix Verification")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Test 1: Health Check
    test_endpoint("Health Check", f"{BASE_URL}/api/v1/health")
    
    # Test 2: API Documentation
    success, resp = test_endpoint("API Documentation", f"{BASE_URL}/docs")
    if success:
        print("   ✓ Swagger UI is accessible")
    
    # Test 3: Database Sync Status
    test_endpoint("Database Sync Status", f"{BASE_URL}/api/v1/db-sync/status")
    
    # Test 4: Database Issues Check
    test_endpoint("Database Issues", f"{BASE_URL}/api/v1/db-sync/issues")
    
    # Test 5: OpenAPI Spec
    success, resp = test_endpoint("OpenAPI Specification", f"{BASE_URL}/openapi.json")
    if success and resp:
        spec = resp.json()
        print(f"   ✓ Found {len(spec.get('paths', {}))} API endpoints")
    
    # Test 6: Try to create a test user (if auth is working)
    test_data = {
        "email": f"test_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    test_endpoint("User Registration", f"{BASE_URL}/api/v1/auth/register", 
                 method="POST", data=test_data)
    
    # Test 7: Login attempt
    login_data = {
        "email": "test@brainops.com",
        "password": "TestPassword123!"
    }
    test_endpoint("User Login", f"{BASE_URL}/api/v1/auth/login",
                 method="POST", data=login_data)
    
    # Test 8: Memory endpoints (public test endpoint)
    test_endpoint("Memory Test Endpoint", f"{BASE_URL}/api/v1/memory/test")
    
    print("\n" + "=" * 60)
    print("📊 System Status Summary")
    print("=" * 60)
    
    # Check specific issues from logs
    print("\n🔧 Known Issues Status:")
    print("1. memory_sync table - Check if memory_id column was added")
    print("2. Route loading - Many endpoints return 501")
    print("3. DATABASE_URL - Optional for db_sync_service")
    
    print("\n💡 Next Steps:")
    print("1. If endpoints still return 501, check route registration in main.py")
    print("2. Verify memory_sync table has memory_id column in Supabase")
    print("3. Test cross-AI memory sync after fixes")
    
    print("\n📝 To check if memory_sync is fixed, run this SQL:")
    print("SELECT column_name FROM information_schema.columns")
    print("WHERE table_name = 'memory_sync' AND column_name = 'memory_id';")

if __name__ == "__main__":
    main()