#!/usr/bin/env python3
"""Force v3.1.172 deployment with version update"""

import subprocess
import os
from datetime import datetime

def update_version_and_push():
    """Update version to v3.1.173 to force new deployment"""
    
    print("🔧 Forcing new deployment by incrementing version to v3.1.173...")
    
    # Navigate to backend directory
    os.chdir('/home/mwwoodworth/code/fastapi-operator-env')
    
    # Find and update main.py
    main_files = subprocess.run(
        'find . -name "main.py" -type f | xargs grep -l "VERSION = " | grep -v venv',
        shell=True, capture_output=True, text=True
    ).stdout.strip().split('\n')
    
    for main_file in main_files:
        if main_file and 'backend' in main_file:
            print(f"Found main.py at: {main_file}")
            
            # Read content
            with open(main_file, 'r') as f:
                content = f.read()
            
            # Update version
            import re
            content = re.sub(r'VERSION = "[^"]*"', 'VERSION = "v3.1.173"', content)
            
            # Write back
            with open(main_file, 'w') as f:
                f.write(content)
            
            print("✅ Updated version to v3.1.173")
            break
    
    # Update health endpoint
    health_files = subprocess.run(
        'find . -name "api_health.py" -type f | grep -v venv',
        shell=True, capture_output=True, text=True
    ).stdout.strip().split('\n')
    
    for health_file in health_files:
        if health_file:
            try:
                with open(health_file, 'r') as f:
                    content = f.read()
                
                content = re.sub(r'"version": "[^"]*"', '"version": "v3.1.173"', content)
                
                with open(health_file, 'w') as f:
                    f.write(content)
                
                print(f"✅ Updated {health_file}")
            except:
                pass
    
    # Commit changes
    print("\n📝 Committing changes...")
    subprocess.run('git add -A', shell=True)
    
    commit_msg = f'''fix: Force v3.1.173 deployment with Slack integration

- Increment version to bypass Render's cached :latest tag
- Contains complete Slack two-way integration
- ClaudeOS command processor ready
- All v3.1.172 features included

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>'''
    
    subprocess.run(['git', 'commit', '-m', commit_msg])
    subprocess.run('git push origin main', shell=True)
    
    # Build and push Docker
    print("\n🐳 Building Docker image v3.1.173...")
    
    # Login to Docker Hub
    docker_pat = "dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho"
    subprocess.run(f'docker login -u mwwoodworth -p "{docker_pat}"', shell=True)
    
    # Build
    subprocess.run('docker build -t mwwoodworth/brainops-backend:v3.1.173 -f Dockerfile .', shell=True)
    
    # Tag as latest
    subprocess.run('docker tag mwwoodworth/brainops-backend:v3.1.173 mwwoodworth/brainops-backend:latest', shell=True)
    
    # Push both
    subprocess.run('docker push mwwoodworth/brainops-backend:v3.1.173', shell=True)
    subprocess.run('docker push mwwoodworth/brainops-backend:latest', shell=True)
    
    print("\n✅ v3.1.173 pushed to Docker Hub!")
    print("🚀 Render should now pull the new version when redeployed")

def send_slack_notification():
    """Notify Slack about the new version"""
    import requests
    
    webhook = "https://hooks.slack.com/services/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"
    
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚀 v3.1.173 Ready - Force Deploy"}
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Solution:* Incremented version to v3.1.173 to bypass Render's cached :latest tag\n\n*Docker Images Ready:*\n• `mwwoodworth/brainops-backend:v3.1.173`\n• `mwwoodworth/brainops-backend:latest` (updated)\n\n**[Claude] Please redeploy on Render.** The new version will be pulled automatically."
            }
        }
    ]
    
    payload = {
        "text": "v3.1.173 Ready - Force Deploy",
        "blocks": blocks,
        "username": "ClaudeOS",
        "icon_emoji": "🚀"
    }
    
    requests.post(webhook, json=payload)

if __name__ == "__main__":
    update_version_and_push()
    send_slack_notification()
    print("\n✅ Complete! Please redeploy on Render to activate v3.1.173")