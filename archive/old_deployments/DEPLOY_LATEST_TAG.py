#!/usr/bin/env python3
"""
Deploy using :latest tag (which points to v3.3.15)
"""
import requests
import time

RENDER_API_KEY = "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
SERVICE_ID = "srv-d1tfs4idbo4c73di6k00"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}"}

print("🚀 Deploying :latest tag (v3.3.15)...")

# Cancel existing deployments
url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=3"
r = requests.get(url, headers=HEADERS)
if r.status_code == 200:
    for deploy_data in r.json():
        deploy = deploy_data['deploy']
        if deploy['status'] in ['created', 'build_in_progress', 'update_in_progress']:
            cancel_url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy['id']}/cancel"
            requests.post(cancel_url, headers=HEADERS)
            print(f"Canceled: {deploy['id']}")

time.sleep(3)

# Deploy latest
url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
data = {
    "clearCache": "clear",
    "image": {
        "ownerId": "usr-cja1ipir0cfc73gqbl60",
        "imagePath": "docker.io/mwwoodworth/brainops-backend:latest",
        "registryCredentialId": "rcr-cja1ipir0cfc73gqbl5g"
    }
}

response = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=data)

if response.status_code in [200, 201]:
    deploy_id = response.json()["id"]
    print(f"✅ Deployment created: {deploy_id}")
    
    # Monitor
    for i in range(40):
        r = requests.get(f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}", headers=HEADERS)
        if r.status_code == 200:
            status = r.json()["status"]
            print(f"Status: {status}")
            if status == "live":
                print("✅ DEPLOYMENT SUCCESSFUL!")
                time.sleep(15)
                
                # Test
                try:
                    health = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=10)
                    if health.status_code == 200:
                        print(f"✅ API WORKING! Version: {health.json().get('version')}")
                    else:
                        print(f"API returned {health.status_code}")
                except Exception as e:
                    print(f"API test error: {e}")
                break
            elif status in ["canceled", "build_failed", "update_failed"]:
                print(f"❌ Failed: {status}")
                break
        time.sleep(30)
else:
    print(f"❌ Error: {response.text}")