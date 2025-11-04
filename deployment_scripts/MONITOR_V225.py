#!/usr/bin/env python3
"""
Monitor v3.1.225 deployment and test authentication
"""
import time
import requests
import json
from datetime import datetime, timezone

BACKEND_URL = "https://brainops-backend-prod.onrender.com"
TARGET_VERSION = "3.1.225"

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
    """Test authentication endpoint"""
    try:
        # Test with empty body to see validation error
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={},
            timeout=5
        )
        
        print(f"\nEmpty body test:")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text[:200] if response.text else '<empty>'}")
        
        # Test with valid credentials
        response = requests.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "test@brainops.com", "password": "TestPassword123!"},
            timeout=5
        )
        
        print(f"\nValid credentials test:")
        print(f"  Status: {response.status_code}")
        if response.text:
            try:
                data = response.json()
                if "access_token" in data:
                    print("  ✅ Login successful! Token received")
                else:
                    print(f"  Response: {json.dumps(data, indent=2)}")
            except:
                print(f"  Response: {response.text[:200]}")
        else:
            print("  ❌ Empty response body")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing login: {e}")
        return False

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
        print("\n\n🧪 TESTING AUTHENTICATION...")
        print("-" * 50)
        
        # Give it a moment to stabilize
        time.sleep(5)
        
        if test_login():
            print("\n✅ AUTHENTICATION FIXED!")
        else:
            print("\n⚠️  Authentication still has issues")

if __name__ == "__main__":
    main()