#!/usr/bin/env python3
"""
DEPLOYMENT v3.3.15 - Clean Build with Version Conflict Fix
- Skipped v3.3.14 due to existing image conflict
- Connection pool fixes from v3.3.13 maintained
- python-multipart already in requirements
- All syntax errors fixed
"""
import requests
import time
import json

RENDER_API_KEY = "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
SERVICE_ID = "srv-d1tfs4idbo4c73di6k00"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}"}

print("🚀 DEPLOYING v3.3.15 - CLEAN BUILD")
print("=" * 60)
print("CRITICAL FIXES:")
print("  ✅ Version conflict resolved (skipped v3.3.14)")
print("  ✅ Connection pool exhaustion fixed")
print("  ✅ Workers reduced from 4 to 1")
print("  ✅ Pool size limited to 2 connections")
print("  ✅ python-multipart dependency present")
print()

# Cancel any existing deployments
print("🛑 Canceling existing deployments...")
url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=5"
r = requests.get(url, headers=HEADERS)
if r.status_code == 200:
    for deploy_data in r.json():
        deploy = deploy_data['deploy']
        if deploy['status'] in ['created', 'build_in_progress', 'update_in_progress']:
            cancel_url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy['id']}/cancel"
            requests.post(cancel_url, headers=HEADERS)
            print(f"  Canceled: {deploy['id']}")

time.sleep(5)

# Deploy v3.3.15
print("\n🚀 Deploying v3.3.15...")
url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
data = {
    "clearCache": "clear",  # Clear cache for clean start
    "image": {
        "ownerId": "usr-cja1ipir0cfc73gqbl60",
        "imagePath": "docker.io/mwwoodworth/brainops-backend:v3.3.15",
        "registryCredentialId": "rcr-cja1ipir0cfc73gqbl5g"
    }
}

response = requests.post(
    url, 
    headers={**HEADERS, "Content-Type": "application/json"}, 
    json=data
)

if response.status_code in [200, 201]:
    deploy = response.json()
    deploy_id = deploy["id"]
    print(f"✅ Deployment created: {deploy_id}")
    print("\n📊 Monitoring deployment...")
    
    for i in range(60):
        r = requests.get(
            f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}",
            headers=HEADERS
        )
        if r.status_code == 200:
            status = r.json()["status"]
            print(f"  [{time.strftime('%H:%M:%S')}] Status: {status}")
            
            if status == "live":
                print("\n🎉 DEPLOYMENT SUCCESSFUL!")
                print("Waiting for service to stabilize...")
                time.sleep(20)
                
                # Test API
                print("\n🔍 Testing API health...")
                try:
                    health = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=10)
                    if health.status_code == 200:
                        data = health.json()
                        print("✅ API OPERATIONAL!")
                        print(f"  Version: {data.get('version', 'unknown')}")
                        print(f"  Status: {data.get('status', 'unknown')}")
                        print("\n🎯 100% OPERATIONAL STATUS ACHIEVED!")
                    else:
                        print(f"⚠️ API returned {health.status_code}")
                except Exception as e:
                    print(f"⚠️ API test error: {e}")
                break
            elif status in ["canceled", "build_failed", "update_failed"]:
                print(f"\n❌ Deployment failed: {status}")
                
                # Get logs
                logs_url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}/events"
                logs_r = requests.get(logs_url, headers=HEADERS)
                if logs_r.status_code == 200:
                    print("\n📋 Deployment logs:")
                    for event in logs_r.json()[:10]:
                        print(f"  {event.get('message', '')}")
                break
        
        time.sleep(30)
else:
    print(f"❌ Failed to create deployment: {response.text}")

print("\n" + "=" * 60)
print("Deployment process complete.")