#!/usr/bin/env python3
"""
Monitor v3.1.226 deployment and thoroughly test all fixes
"""
import time
import requests
import json
from datetime import datetime, timezone

BACKEND_URL = "https://brainops-backend-prod.onrender.com"
TARGET_VERSION = "3.1.226"

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

def test_login():
    """Test authentication endpoint thoroughly"""
    print("\n🔐 TESTING AUTHENTICATION...")
    print("-" * 50)
    
    results = []
    
    # Test 1: Empty body (should return validation error with details)
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={},
            timeout=5
        )
        
        print("1. Empty body test:")
        print(f"   Status: {response.status_code}")
        if response.text:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                results.append(response.status_code == 422 and "detail" in data)
            except:
                print(f"   Response (raw): {response.text[:200]}")
                results.append(False)
        else:
            print("   ❌ Empty response body")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    # Test 2: Invalid credentials
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"},
            timeout=5
        )
        
        print("\n2. Invalid credentials test:")
        print(f"   Status: {response.status_code}")
        if response.text:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
                results.append(response.status_code == 401 and "detail" in data)
            except:
                print(f"   Response (raw): {response.text[:200]}")
                results.append(False)
        else:
            print("   ❌ Empty response body")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    # Test 3: Valid credentials
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "test@brainops.com", "password": "TestPassword123!"},
            timeout=5
        )
        
        print("\n3. Valid credentials test:")
        print(f"   Status: {response.status_code}")
        if response.text:
            try:
                data = response.json()
                if "access_token" in data:
                    print("   ✅ Login successful!")
                    print(f"   Token (first 20 chars): {data['access_token'][:20]}...")
                    print(f"   User: {data.get('user', {})}")
                    results.append(True)
                    return data.get("access_token")
                else:
                    print(f"   Response: {json.dumps(data, indent=2)}")
                    results.append(False)
            except:
                print(f"   Response (raw): {response.text[:200]}")
                results.append(False)
        else:
            print("   ❌ Empty response body")
            results.append(False)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n   Authentication Tests: {sum(results)}/{len(results)} passed ({success_rate:.0f}%)")
    return None

def test_public_endpoints(token=None):
    """Test public endpoints that should NOT require authentication"""
    print("\n🌐 TESTING PUBLIC ENDPOINTS...")
    print("-" * 50)
    
    public_endpoints = [
        ("GET", "/api/v1/marketplace/products", "Marketplace Products"),
        ("GET", "/api/v1/marketplace/categories", "Marketplace Categories"),
        ("GET", "/api/v1/automations/status", "Automations Status"),
    ]
    
    results = []
    
    for method, endpoint, name in public_endpoints:
        try:
            # Test WITHOUT authentication
            response = requests.request(
                method,
                f"{BACKEND_URL}{endpoint}",
                timeout=5
            )
            
            print(f"\n{name} (NO AUTH):")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   ✅ Success! Returned {len(data)} items")
                    else:
                        print(f"   ✅ Success! Response type: {type(data).__name__}")
                    results.append(True)
                except:
                    print(f"   ✅ Success! (non-JSON response)")
                    results.append(True)
            elif response.status_code == 401:
                print(f"   ❌ FAILED - Requires authentication (should be public!)")
                if response.text:
                    try:
                        print(f"   Error: {response.json()}")
                    except:
                        print(f"   Error: {response.text[:100]}")
                results.append(False)
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
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
        
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        
        if current_version != last_version:
            print(f"\n[{timestamp}] Version changed: {last_version} → {current_version}")
            last_version = current_version
            
            if current_version == TARGET_VERSION:
                print(f"✅ v{TARGET_VERSION} is now live!")
                deployed = True
                break
                
        else:
            print(f"\r[{timestamp}] Current: {current_version} | Waiting... ({elapsed}s)", end="", flush=True)
            
        time.sleep(10)
        
        if elapsed > 600:
            print(f"\n❌ Timeout after {elapsed} seconds")
            break
    
    if deployed:
        print("\n\n🧪 RUNNING COMPREHENSIVE TESTS...")
        print("=" * 50)
        
        # Give it a moment to stabilize
        time.sleep(5)
        
        # Test authentication
        token = test_login()
        
        # Test public endpoints
        test_public_endpoints(token)
        
        print("\n\n📊 FINAL ASSESSMENT")
        print("=" * 50)
        
        if token:
            print("✅ Authentication is FIXED!")
        else:
            print("❌ Authentication still has issues")
            
        print("\n🎯 Run full validation: python3 CLAUDEOS_PRELAUNCH_VALIDATOR.py")

if __name__ == "__main__":
    main()