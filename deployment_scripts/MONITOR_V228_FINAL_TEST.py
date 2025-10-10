#!/usr/bin/env python3
"""
Monitor v3.1.228 deployment - FINAL AUTH FIX
"""
import time
import requests
import json
from datetime import datetime, timezone

BACKEND_URL = "https://brainops-backend-prod.onrender.com"
TARGET_VERSION = "3.1.228"

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

def test_complete_system():
    """Test the complete system"""
    print("\n🧪 COMPREHENSIVE SYSTEM TEST")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Health check
    print("\n1. Health Check:")
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        tests_total += 1
        if response.status_code == 200:
            print("   ✅ API is healthy")
            tests_passed += 1
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        tests_total += 1
    
    # Test 2: Login with valid credentials
    print("\n2. Authentication - Valid Login:")
    token = None
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "test@brainops.com", "password": "TestPassword123!"},
            timeout=10
        )
        tests_total += 1
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                token = data["access_token"]
                print("   ✅ Login successful!")
                print(f"   Token: {token[:30]}...")
                print(f"   User: {data.get('user', {}).get('email', 'Unknown')}")
                tests_passed += 1
            else:
                print("   ❌ No access token in response")
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        tests_total += 1
    
    # Test 3: Login with invalid credentials
    print("\n3. Authentication - Invalid Login:")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"},
            timeout=5
        )
        tests_total += 1
        
        if response.status_code == 401:
            print("   ✅ Correctly rejected invalid credentials")
            tests_passed += 1
        else:
            print(f"   ❌ Expected 401, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        tests_total += 1
    
    # Test 4: Empty login body
    print("\n4. Authentication - Empty Body:")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={},
            timeout=5
        )
        tests_total += 1
        
        if response.status_code == 422:
            print("   ✅ Correctly validated empty body")
            tests_passed += 1
        else:
            print(f"   ❌ Expected 422, got {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        tests_total += 1
    
    # Test 5-7: Public endpoints
    public_endpoints = [
        ("/api/v1/marketplace/products", "Marketplace Products"),
        ("/api/v1/marketplace/categories", "Marketplace Categories"),
        ("/api/v1/automations/status", "Automations Status"),
    ]
    
    for endpoint, name in public_endpoints:
        tests_total += 1
        print(f"\n{tests_total}. {name} (Public):")
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print("   ✅ Public access working")
                tests_passed += 1
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test 8: Protected endpoint with token
    if token:
        tests_total += 1
        print(f"\n{tests_total}. Protected Endpoint (with token):")
        try:
            response = requests.get(
                f"{BACKEND_URL}/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if response.status_code == 200:
                print("   ✅ Protected access working")
                tests_passed += 1
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 RESULTS: {tests_passed}/{tests_total} tests passed")
    success_rate = (tests_passed / tests_total * 100) if tests_total > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("✅ SYSTEM IS OPERATIONAL!")
    elif success_rate >= 70:
        print("⚠️ SYSTEM PARTIALLY OPERATIONAL")
    else:
        print("❌ SYSTEM HAS CRITICAL ISSUES")
    
    return success_rate

def main():
    print(f"🚀 MONITORING DEPLOYMENT: v{TARGET_VERSION}")
    print("-" * 50)
    
    start_time = time.time()
    last_version = None
    deployed = False
    
    while True:
        current_version = check_version()
        elapsed = int(time.time() - start_time)
        
        if current_version != last_version:
            print(f"\n[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Version changed: {last_version} → {current_version}")
            last_version = current_version
            
            if current_version == TARGET_VERSION:
                print(f"✅ v{TARGET_VERSION} is now live!")
                deployed = True
                break
        else:
            print(f"\r[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Current: {current_version} | Waiting... ({elapsed}s)", end="", flush=True)
        
        time.sleep(10)
        
        if elapsed > 600:
            print(f"\n❌ Timeout after {elapsed} seconds")
            break
    
    if deployed:
        # Give it a moment to stabilize
        print("\nWaiting 10 seconds for system to stabilize...")
        time.sleep(10)
        
        # Run comprehensive tests
        success_rate = test_complete_system()
        
        print("\n\n🎯 FINAL STATUS")
        print("=" * 50)
        if success_rate >= 90:
            print("✅ v3.1.228 DEPLOYMENT SUCCESSFUL!")
            print("✅ Authentication is FIXED!")
            print("✅ Public endpoints are WORKING!")
            print("✅ System is READY FOR PRODUCTION!")
        else:
            print("❌ v3.1.228 still has issues")
            print("🔍 Further investigation required")

if __name__ == "__main__":
    main()