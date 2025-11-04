#!/usr/bin/env python3
import requests
import time
import json

RENDER_API_KEY = "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
SERVICE_ID = "srv-d1tfs4idbo4c73di6k00"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}"}

print("🚀 Deploying v3.3.12 with critical fixes...")

# Create deployment
url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
data = {
    "clearCache": "do_not_clear",
    "image": {
        "ownerId": "usr-cja1ipir0cfc73gqbl60",
        "imagePath": "docker.io/mwwoodworth/brainops-backend:v3.3.12",
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
    print(f"✅ Created deployment: {deploy_id}")
    
    # Monitor deployment
    for i in range(60):
        r = requests.get(
            f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}",
            headers=HEADERS
        )
        if r.status_code == 200:
            status = r.json()["status"]
            print(f"[{time.strftime('%H:%M:%S')}] Status: {status}")
            
            if status == "live":
                print("\n🎉 Deployment successful! Testing API...")
                time.sleep(10)
                try:
                    health = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=10)
                    if health.status_code == 200:
                        print("✅ API Health Check:")
                        print(json.dumps(health.json(), indent=2))
                    else:
                        print(f"API returned {health.status_code}")
                except Exception as e:
                    print(f"API test error: {e}")
                break
            elif status in ["canceled", "build_failed", "update_failed"]:
                print(f"❌ Deployment failed: {status}")
                break
        
        time.sleep(30)
else:
    print(f"❌ Failed to create deployment: {response.text}")
