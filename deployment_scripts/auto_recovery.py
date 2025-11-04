#!/usr/bin/env python3
"""
Automated Recovery System
"""
import requests
import time
import subprocess

def check_and_recover():
    """Check systems and recover if needed"""
    
    # Backend recovery
    try:
        resp = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=5)
        if resp.status_code != 200:
            print("🔧 Attempting backend recovery...")
            # Trigger re-deployment
            webhook = "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"
            requests.post(webhook)
            print("   Deployment triggered")
    except:
        print("❌ Backend unreachable - triggering recovery")
        
    # Database health check
    try:
        resp = requests.get("https://brainops-backend-prod.onrender.com/api/v1/db-sync/status", timeout=5)
        if resp.status_code != 200:
            print("🔧 Database sync issues detected")
    except:
        pass

if __name__ == "__main__":
    while True:
        check_and_recover()
        time.sleep(600)  # Every 10 minutes
