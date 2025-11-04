#!/usr/bin/env python3
import requests
import time

RENDER_API_KEY = "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
SERVICE_ID = "srv-d1tfs4idbo4c73di6k00"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}"}

print("🚀 Deploying latest image...")

url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
data = {
    "clearCache": "clear",
    "image": {
        "ownerId": "usr-cja1ipir0cfc73gqbl60",
        "imagePath": "docker.io/mwwoodworth/brainops-backend:latest",
        "registryCredentialId": "rcr-cja1ipir0cfc73gqbl5g"
    }
}

r = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=data)

if r.status_code in [200, 201]:
    deploy_id = r.json()["id"]
    print(f"✅ Deployment created: {deploy_id}")
    
    # Monitor
    for i in range(40):
        status_r = requests.get(
            f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}",
            headers=HEADERS
        )
        if status_r.status_code == 200:
            status = status_r.json()["status"]
            print(f"  Status: {status}")
            if status in ["live", "canceled", "build_failed", "update_failed"]:
                break
        time.sleep(30)
else:
    print(f"❌ Error: {r.text}")
