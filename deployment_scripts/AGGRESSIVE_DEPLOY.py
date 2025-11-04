#!/usr/bin/env python3
"""
Aggressive deployment that cancels ALL other deployments continuously
"""

import time
import requests
import json
import threading
from datetime import datetime

RENDER_API_KEY = "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
SERVICE_ID = "srv-d1tfs4idbo4c73di6k00"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}"}

# Keep canceling webhook deployments in background
def cancel_thread(protected_id):
    """Background thread that continuously cancels webhook deployments"""
    while True:
        try:
            url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=20"
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code == 200:
                deploys = response.json()
                for d in deploys:
                    deploy = d["deploy"]
                    deploy_id = deploy["id"]
                    status = deploy["status"]
                    trigger = deploy.get("trigger", "")
                    
                    # Cancel ANY deployment that's not ours
                    if (deploy_id != protected_id and 
                        status in ["created", "build_in_progress", "update_in_progress", "pre_deploy_in_progress"]):
                        
                        print(f"  🔨 Canceling interfering deployment: {deploy_id} ({trigger})")
                        cancel_url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}/cancel"
                        requests.post(cancel_url, headers=HEADERS)
        except:
            pass
        
        time.sleep(5)  # Check every 5 seconds

def main():
    print("🚨 AGGRESSIVE DEPLOYMENT MODE")
    print("=" * 50)
    print("Will cancel ALL other deployments continuously\n")
    
    # Cancel everything first
    print("Clearing all existing deployments...")
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=50"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        for d in response.json():
            deploy = d["deploy"]
            if deploy["status"] in ["created", "build_in_progress", "update_in_progress"]:
                requests.post(
                    f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy['id']}/cancel",
                    headers=HEADERS
                )
                print(f"  Canceled: {deploy['id']}")
    
    print("\nWaiting 10 seconds for cancellations to complete...")
    time.sleep(10)
    
    # Create our deployment
    print("\n🚀 Creating protected deployment...")
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
    data = {
        "clearCache": "do_not_clear",
        "image": {
            "ownerId": "usr-cja1ipir0cfc73gqbl60",
            "imagePath": "docker.io/mwwoodworth/brainops-backend:v3.3.11",
            "registryCredentialId": "rcr-cja1ipir0cfc73gqbl5g"
        }
    }
    
    response = requests.post(
        url, 
        headers={**HEADERS, "Content-Type": "application/json"}, 
        json=data
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create deployment: {response.text}")
        return
    
    deploy = response.json()
    deploy_id = deploy["id"]
    print(f"✅ Created deployment: {deploy_id}")
    
    # Start background cancellation thread
    print("\n🛡️ Starting protection thread...")
    cancel_t = threading.Thread(target=cancel_thread, args=(deploy_id,), daemon=True)
    cancel_t.start()
    
    # Monitor our deployment
    print("\n📊 Monitoring deployment (canceling all others)...\n")
    
    start_time = time.time()
    max_duration = 1800  # 30 minutes max
    
    while time.time() - start_time < max_duration:
        # Check our deployment status
        url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            deploy = response.json()
            status = deploy["status"]
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"[{timestamp}] Status: {status}")
            
            if status == "live":
                print("\n🎉🎉🎉 DEPLOYMENT SUCCESSFUL! 🎉🎉🎉")
                print("v3.3.11 is now LIVE!")
                print("\n✅ Testing API health:")
                try:
                    health = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=10)
                    if health.status_code == 200:
                        print(json.dumps(health.json(), indent=2))
                    else:
                        print(f"API returned {health.status_code}")
                except:
                    print("API is starting up...")
                return
            elif status in ["canceled", "build_failed", "update_failed"]:
                print(f"\n❌ Deployment failed: {status}")
                print("Retrying in 30 seconds...")
                time.sleep(30)
                # Recursive retry
                main()
                return
        
        time.sleep(15)
    
    print("\n⏱️ Timeout after 30 minutes")

if __name__ == "__main__":
    main()