#!/usr/bin/env python3
import time
import requests

DEPLOY_ID = "dep-d2ek4qidbo4c738he1mg"
HEADERS = {"Authorization": "Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"}

print(f"📊 Monitoring deployment: {DEPLOY_ID}\n")

for i in range(60):  # Check for 30 minutes
    try:
        r = requests.get(
            f"https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys/{DEPLOY_ID}",
            headers=HEADERS
        )
        if r.status_code == 200:
            status = r.json()["status"]
            print(f"[{time.strftime('%H:%M:%S')}] Status: {status}")
            
            if status == "live":
                print("\n🎉 DEPLOYMENT SUCCESSFUL! v3.3.11 is LIVE!")
                # Test the API
                try:
                    health = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=10)
                    if health.status_code == 200:
                        print("\n✅ API Health Check:")
                        import json
                        print(json.dumps(health.json(), indent=2))
                except:
                    print("\nAPI is still starting up...")
                break
            elif status in ["canceled", "build_failed", "update_failed"]:
                print(f"\n❌ Deployment failed: {status}")
                break
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(30)