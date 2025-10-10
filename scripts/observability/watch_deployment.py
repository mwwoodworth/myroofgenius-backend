#!/usr/bin/env python3
"""
Watch Render deployment in real-time
"""

import time
import requests
import sys
from datetime import datetime

RENDER_API_KEY = "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
DEPLOY_ID = sys.argv[1] if len(sys.argv) > 1 else "dep-d2hbrc7diees73ebjv20"

def get_deploy_status(deploy_id):
    """Get deployment status"""
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    url = f"https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys/{deploy_id}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error: {e}")
    return None

def main():
    print(f"Watching deployment: {DEPLOY_ID}")
    print("=" * 50)
    
    last_status = None
    start_time = time.time()
    
    while True:
        deploy = get_deploy_status(DEPLOY_ID)
        
        if deploy:
            status = deploy.get("status", "unknown")
            
            if status != last_status:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed:3d}s] Status: {status}")
                
                if status == "live":
                    print("✅ Deployment successful!")
                    print(f"Started: {deploy.get('startedAt')}")
                    print(f"Finished: {deploy.get('finishedAt')}")
                    break
                elif status in ["failed", "canceled"]:
                    print(f"❌ Deployment {status}")
                    break
                
                last_status = status
        
        time.sleep(5)

if __name__ == "__main__":
    main()