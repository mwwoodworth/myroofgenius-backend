#!/usr/bin/env python3
"""
Deployment Monitor - Track v3.1.224 deployment progress
"""
import time
import requests
import json
from datetime import datetime, timezone

BACKEND_URL = "https://brainops-backend-prod.onrender.com"
TARGET_VERSION = "3.1.224"
DEPLOYMENT_ID = "dep-d27atavdiees73cbjgp0"

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

def main():
    print(f"🚀 MONITORING DEPLOYMENT: {DEPLOYMENT_ID}")
    print(f"Target Version: {TARGET_VERSION}")
    print("-" * 50)
    
    start_time = time.time()
    last_version = None
    
    while True:
        current_version = check_version()
        elapsed = int(time.time() - start_time)
        
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        
        if current_version != last_version:
            if current_version == TARGET_VERSION:
                print(f"\n✅ [{timestamp}] DEPLOYMENT SUCCESSFUL!")
                print(f"   Version {TARGET_VERSION} is now live!")
                print(f"   Total deployment time: {elapsed} seconds")
                break
            else:
                print(f"[{timestamp}] Current version: {current_version} (waiting for {TARGET_VERSION})")
                last_version = current_version
        else:
            # Just update the timer
            print(f"\r[{timestamp}] Waiting... ({elapsed}s)", end="", flush=True)
            
        # Check every 10 seconds
        time.sleep(10)
        
        # Timeout after 10 minutes
        if elapsed > 600:
            print(f"\n❌ Deployment timeout after {elapsed} seconds")
            print("Please check Render dashboard manually")
            break

if __name__ == "__main__":
    main()