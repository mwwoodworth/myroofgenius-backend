import os
import subprocess
import requests
import json
from datetime import datetime

def deploy_backend():
    """Deploy revenue-enabled backend"""
    
    print("🔨 Building Docker image with revenue features...")
    
    # Build Docker image
    docker_tag = "mwwoodworth/brainops-backend:v3.1.250-revenue"
    
    build_cmd = f"docker build -t {docker_tag} -f Dockerfile ."
    subprocess.run(build_cmd, shell=True, check=True)
    
    print("📤 Pushing to Docker Hub...")
    push_cmd = f"docker push {docker_tag}"
    subprocess.run(push_cmd, shell=True, check=True)
    
    print("🔄 Triggering Render deployment...")
    
    # Trigger Render webhook
    webhook_url = "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"
    
    response = requests.get(webhook_url)
    
    if response.status_code == 200:
        print("✅ Backend deployment triggered successfully!")
    else:
        print(f"⚠️ Deployment trigger returned: {response.status_code}")
    
    return True

if __name__ == "__main__":
    deploy_backend()
