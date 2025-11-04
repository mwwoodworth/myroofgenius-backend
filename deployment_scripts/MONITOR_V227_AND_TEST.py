#!/usr/bin/env python3
"""
Monitor v3.1.227 deployment and test route priority fixes
"""
import time
import requests
import json
from datetime import datetime, timezone

BACKEND_URL = "https://brainops-backend-prod.onrender.com"
TARGET_VERSION = "3.1.227"

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

def check_loaded_routes():
    """Check which routes are loaded"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/routes", timeout=5)
        if response.status_code == 200:
            data = response.json()
            loaded = data.get("loaded_routes", [])
            
            # Count auth routes
            auth_routes = [r for r in loaded if 'auth' in r]
            print(f"\n📊 Auth routes loaded: {len(auth_routes)}")
            print(f"   First 5: {auth_routes[:5]}")
            
            # Check if problematic routes are loaded
            if 'auth' in loaded and 'auth_fixed' in loaded:
                print("   ⚠️ WARNING: Both 'auth' and 'auth_fixed' are loaded!")
            elif 'auth_fixed' in loaded:
                print("   ✅ Only auth_fixed loaded (good)")
            
            return loaded
    except Exception as e:
        print(f"   ❌ Error checking routes: {e}")
    return []

def test_authentication():
    """Test authentication endpoints"""
    print("\n🔐 TESTING AUTHENTICATION...")
    print("-" * 50)
    
    results = []
    
    # Test 1: Valid login
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "test@brainops.com", "password": "TestPassword123!"},
            timeout=10
        )
        
        print("1. Valid login test:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print("   ✅ LOGIN SUCCESSFUL!")
                print(f"   Token (first 20 chars): {data['access_token'][:20]}...")
                print(f"   User: {data.get('user', {})}")
                results.append(True)
                return data.get("access_token")
            else:
                print(f"   ❌ No access token in response")
                results.append(False)
        else:
            print(f"   ❌ Login failed with status {response.status_code}")
            if response.text:
                try:
                    error = response.json()
                    print(f"   Error: {error}")
                except:
                    print(f"   Response: {response.text[:200]}")
            results.append(False)
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    # Test 2: Empty body (should return 422 with details)
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={},
            timeout=5
        )
        
        print("\n2. Empty body test:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 422 and response.text:
            try:
                error = response.json()
                if "detail" in error:
                    print("   ✅ Proper validation error returned")
                    results.append(True)
                else:
                    print("   ❌ No detail in error response")
                    results.append(False)
            except:
                print(f"   ❌ Response not JSON: {response.text[:100]}")
                results.append(False)
        else:
            print(f"   ❌ Expected 422, got {response.status_code}")
            results.append(False)
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    success_rate = sum(results) / len(results) * 100 if results else 0
    print(f"\n   Authentication Tests: {sum(results)}/{len(results)} passed ({success_rate:.0f}%)")
    return None

def test_public_endpoints():
    """Test public endpoints"""
    print("\n🌐 TESTING PUBLIC ENDPOINTS...")
    print("-" * 50)
    
    endpoints = [
        ("GET", "/api/v1/marketplace/products", "Marketplace Products"),
        ("GET", "/api/v1/marketplace/categories", "Marketplace Categories"),
        ("GET", "/api/v1/automations/status", "Automations Status"),
    ]
    
    results = []
    
    for method, endpoint, name in endpoints:
        try:
            response = requests.request(
                method,
                f"{BACKEND_URL}{endpoint}",
                timeout=5
            )
            
            print(f"\n{name}:")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS - Public access working!")
                results.append(True)
            elif response.status_code in [401, 403]:
                print("   ❌ FAILED - Still requires authentication!")
                results.append(False)
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100 if results else 0
    print(f"\n   Public Endpoint Tests: {sum(results)}/{len(results)} passed ({success_rate:.0f}%)")

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
        print("\n\n🧪 RUNNING COMPREHENSIVE TESTS...")
        print("=" * 50)
        
        # Check loaded routes
        check_loaded_routes()
        
        # Give it a moment to stabilize
        time.sleep(5)
        
        # Test authentication
        token = test_authentication()
        
        # Test public endpoints
        test_public_endpoints()
        
        print("\n\n📊 FINAL ASSESSMENT")
        print("=" * 50)
        
        if token:
            print("✅ Authentication is WORKING!")
            print("🎯 SUCCESS: The route priority fix worked!")
        else:
            print("❌ Authentication still has issues")
            print("🔍 Need to investigate further")

if __name__ == "__main__":
    main()