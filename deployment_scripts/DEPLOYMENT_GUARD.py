#!/usr/bin/env python3
"""
Deployment Guard - Protects our deployment from webhook interference
"""

import time
import requests
import json
import sys
from datetime import datetime

RENDER_API_KEY = "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
SERVICE_ID = "srv-d1tfs4idbo4c73di6k00"
HEADERS = {"Authorization": f"Bearer {RENDER_API_KEY}"}

def cancel_webhook_deployments(protected_id):
    """Cancel any deployments that aren't our protected one"""
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys?limit=10"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        deploys = response.json()
        for d in deploys:
            deploy = d["deploy"]
            deploy_id = deploy["id"]
            status = deploy["status"]
            trigger = deploy["trigger"]
            
            # Cancel any webhook-triggered deployment that's not ours
            if (deploy_id != protected_id and 
                trigger == "deploy_hook" and 
                status in ["created", "build_in_progress", "update_in_progress"]):
                
                print(f"  Canceling webhook deployment: {deploy_id}")
                cancel_url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}/cancel"
                requests.post(cancel_url, headers=HEADERS)

def create_api_deployment():
    """Create a deployment via API"""
    url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
    data = {"clearCache": "do_not_clear"}
    
    response = requests.post(url, headers={**HEADERS, "Content-Type": "application/json"}, json=data)
    
    if response.status_code in [200, 201]:
        deploy = response.json()
        print(f"✅ Created API deployment: {deploy['id']}")
        return deploy["id"]
    else:
        print(f"❌ Failed to create deployment: {response.text}")
        return None

def monitor_deployment(deploy_id):
    """Monitor and protect our deployment"""
    print(f"\n🛡️ PROTECTING DEPLOYMENT: {deploy_id}")
    print("Canceling any webhook deployments that interfere...\n")
    
    start_time = time.time()
    max_duration = 1200  # 20 minutes max
    
    while time.time() - start_time < max_duration:
        # Cancel interfering deployments
        cancel_webhook_deployments(deploy_id)
        
        # Check our deployment status
        url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            deploy = response.json()
            status = deploy["status"]
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"[{timestamp}] Our deployment status: {status}")
            
            if status == "live":
                print("\n🎉🎉🎉 DEPLOYMENT SUCCESSFUL! 🎉🎉🎉")
                print("The deployment loop has been defeated!")
                return True
            elif status in ["canceled", "build_failed", "update_failed"]:
                print(f"\n❌ Deployment failed with status: {status}")
                return False
        
        time.sleep(15)  # Check every 15 seconds
    
    print("\n⏱️ Timeout after 20 minutes")
    return False

def main():
    print("🚨 DEPLOYMENT GUARD ACTIVATED")
    print("=" * 50)
    print("This will protect our deployment from webhook interference\n")
    
    # First, cancel all existing deployments
    print("Canceling all existing deployments...")
    cancel_webhook_deployments("none")
    
    # Create our API deployment
    deploy_id = create_api_deployment()
    
    if deploy_id:
        # Monitor and protect it
        success = monitor_deployment(deploy_id)
        
        if success:
            print("\n✅ Testing API health:")
            try:
                health_response = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=10)
                if health_response.status_code == 200:
                    print(json.dumps(health_response.json(), indent=2))
                else:
                    print(f"API returned status {health_response.status_code}")
            except:
                print("API is still starting up...")
    else:
        print("\n❌ Could not create deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()