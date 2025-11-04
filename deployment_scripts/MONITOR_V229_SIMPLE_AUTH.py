#!/usr/bin/env python3
"""
Monitor v3.1.229 deployment - Simple Auth
"""
import time
import requests
import json
from datetime import datetime, timezone

BACKEND_URL = "https://brainops-backend-prod.onrender.com"
TARGET_VERSION = "3.1.229"

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

def test_authentication():
    """Test authentication with simple auth route"""
    print("\n🔐 TESTING AUTHENTICATION")
    print("=" * 50)
    
    # Test valid login
    print("\n1. Testing login with valid credentials:")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "test@brainops.com", "password": "TestPassword123!"},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ LOGIN SUCCESSFUL!")
            print(f"   Access Token: {data.get('access_token', '')[:40]}...")
            print(f"   Refresh Token: {data.get('refresh_token', '')[:40]}...")
            print(f"   User Data: {data.get('user', {})}")
            return True, data.get('access_token')
        else:
            print(f"   ❌ Login failed")
            if response.text:
                print(f"   Response: {response.text[:200]}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def test_public_endpoints():
    """Test public endpoints"""
    print("\n🌐 TESTING PUBLIC ENDPOINTS")
    print("=" * 50)
    
    endpoints = [
        ("/api/v1/marketplace/products", "Marketplace Products"),
        ("/api/v1/marketplace/categories", "Marketplace Categories"), 
        ("/api/v1/automations/status", "Automations Status"),
    ]
    
    all_passed = True
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name}: Working (no auth required)")
            else:
                print(f"   ❌ {name}: Failed with {response.status_code}")
                all_passed = False
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
            all_passed = False
    
    return all_passed

def test_protected_endpoint(token):
    """Test protected endpoint with token"""
    print("\n🔒 TESTING PROTECTED ENDPOINT")
    print("=" * 50)
    
    if not token:
        print("   ⚠️ No token available, skipping protected endpoint test")
        return False
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Protected endpoint working!")
            print(f"   User: {data}")
            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print(f"🚀 MONITORING DEPLOYMENT: v{TARGET_VERSION}")
    print("-" * 50)
    
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
    
    # Run tests
    auth_passed, token = test_authentication()
    public_passed = test_public_endpoints()
    protected_passed = test_protected_endpoint(token) if token else False
    
    # Final assessment
    print("\n\n🎯 FINAL ASSESSMENT")
    print("=" * 50)
    
    if auth_passed and public_passed:
        print("✅ AUTHENTICATION IS FIXED!")
        print("✅ PUBLIC ENDPOINTS ARE WORKING!")
        print("✅ SYSTEM IS OPERATIONAL!")
        print("\n🎉 SUCCESS! The authentication issue has been resolved!")
    else:
        print("❌ Some issues remain")
        if not auth_passed:
            print("   - Authentication still failing")
        if not public_passed:
            print("   - Some public endpoints not working")

if __name__ == "__main__":
    main()