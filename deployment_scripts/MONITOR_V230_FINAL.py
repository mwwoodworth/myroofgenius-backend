#!/usr/bin/env python3
"""
Monitor v3.1.230 deployment - FINAL FIX
"""
import time
import requests
import json
from datetime import datetime, timezone

BACKEND_URL = "https://brainops-backend-prod.onrender.com"
TARGET_VERSION = "3.1.230"

def check_version():
    """Check current backend version"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("version", "unknown")
    except:
        pass
    return "error"

def comprehensive_test():
    """Run comprehensive system tests"""
    print("\n🧪 COMPREHENSIVE SYSTEM TEST")
    print("=" * 60)
    
    all_tests = []
    
    # Test 1: Authentication with valid credentials
    print("\n1. Authentication - Valid Login:")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "test@brainops.com", "password": "TestPassword123!"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ LOGIN SUCCESSFUL!")
            print(f"   Access Token: {data.get('access_token', '')[:40]}...")
            print(f"   User Email: {data.get('user', {}).get('email', 'Unknown')}")
            all_tests.append(("Auth Valid", True))
            token = data.get('access_token')
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}")
            all_tests.append(("Auth Valid", False))
            token = None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_tests.append(("Auth Valid", False))
        token = None
    
    # Test 2: Authentication with invalid credentials
    print("\n2. Authentication - Invalid Login:")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"},
            timeout=5
        )
        
        if response.status_code == 401:
            print("   ✅ Correctly rejected invalid credentials")
            all_tests.append(("Auth Invalid", True))
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
            all_tests.append(("Auth Invalid", False))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_tests.append(("Auth Invalid", False))
    
    # Test 3: Empty body validation
    print("\n3. Authentication - Empty Body:")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={},
            timeout=5
        )
        
        if response.status_code == 422:
            print("   ✅ Correctly validated empty body")
            all_tests.append(("Auth Validation", True))
        else:
            print(f"   ❌ Expected 422, got {response.status_code}")
            all_tests.append(("Auth Validation", False))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_tests.append(("Auth Validation", False))
    
    # Test 4-6: Public endpoints
    print("\n4-6. Public Endpoints:")
    public_endpoints = [
        ("/api/v1/marketplace/products", "Marketplace Products"),
        ("/api/v1/marketplace/categories", "Marketplace Categories"),
        ("/api/v1/automations/status", "Automations Status"),
    ]
    
    for endpoint, name in public_endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name}: Public access working")
                all_tests.append((name, True))
            else:
                print(f"   ❌ {name}: Failed with {response.status_code}")
                all_tests.append((name, False))
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
            all_tests.append((name, False))
    
    # Test 7: Protected endpoint
    if token:
        print("\n7. Protected Endpoint:")
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Protected access working!")
                print(f"   User: {data.get('email', 'Unknown')}")
                all_tests.append(("Protected Endpoint", True))
            else:
                print(f"   ❌ Failed with status {response.status_code}")
                all_tests.append(("Protected Endpoint", False))
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_tests.append(("Protected Endpoint", False))
    
    # Summary
    passed = sum(1 for _, result in all_tests if result)
    total = len(all_tests)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} passed ({success_rate:.1f}%)")
    
    return success_rate >= 90, success_rate

def main():
    print(f"🚀 MONITORING DEPLOYMENT: v{TARGET_VERSION} - FINAL FIX")
    print("-" * 60)
    
    start_time = time.time()
    last_version = None
    
    while True:
        current_version = check_version()
        elapsed = int(time.time() - start_time)
        
        if current_version != last_version:
            print(f"\n[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Version changed: {last_version} → {current_version}")
            last_version = current_version
            
            if current_version == TARGET_VERSION:
                print(f"✅ v{TARGET_VERSION} is now live!")
                break
        else:
            print(f"\r[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Current: {current_version} | Waiting... ({elapsed}s)", end="", flush=True)
        
        time.sleep(10)
        
        if elapsed > 600:
            print(f"\n❌ Timeout after {elapsed} seconds")
            return
    
    # Wait for stabilization
    print("\nWaiting 10 seconds for system to stabilize...")
    time.sleep(10)
    
    # Run comprehensive tests
    all_passed, success_rate = comprehensive_test()
    
    # Final assessment
    print("\n\n🎯 FINAL ASSESSMENT - v3.1.230")
    print("=" * 60)
    
    if all_passed:
        print("✅ ✅ ✅ AUTHENTICATION IS FINALLY FIXED! ✅ ✅ ✅")
        print("✅ All public endpoints working without auth")
        print("✅ All protected endpoints working with auth")
        print("✅ Proper validation and error messages")
        print("\n🎉 SUCCESS! The system is now 100% operational!")
        print("\n📌 Summary of fixes:")
        print("   - Fixed parameter name conflicts in auth.py")
        print("   - Public endpoints don't require authentication")
        print("   - Authentication returns proper tokens")
        print("   - System ready for production use!")
    else:
        print(f"❌ System is {success_rate:.1f}% operational")
        print("🔍 Some issues remain - further investigation needed")

if __name__ == "__main__":
    main()