#!/usr/bin/env python3
"""Send Docker deployment instructions to Slack"""

import requests
import json
from datetime import datetime

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def send_docker_update():
    """Send Docker deployment instructions"""
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🐳 Docker Image v3.1.172 Ready - Deployment Instructions"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*✅ Docker Image Confirmed:*\n• Image: `mwwoodworth/brainops-backend:v3.1.172`\n• Also tagged as: `latest`\n• Built: 24 minutes ago\n• Size: 2.41GB\n• Contains: Complete Slack integration"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔧 Render Deployment Fix:*\n\nThe issue is that Render is still pulling v3.1.171. To fix:\n\n1. Go to Render Dashboard → BrainOps Backend\n2. Check Docker Image URL setting\n3. **Option A:** Change to specific version:\n   `mwwoodworth/brainops-backend:v3.1.172`\n4. **Option B:** Force pull latest:\n   - Clear build cache\n   - Redeploy with `latest` tag"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📋 What's New in v3.1.172:*\n• Complete Slack two-way integration\n• ClaudeOS command processor\n• Multi-agent routing system\n• Redis command queue\n• Event handler endpoints"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*⚡ Quick Deploy Command:*\n```\ndocker pull mwwoodworth/brainops-backend:v3.1.172\n```"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 If Render continues to pull v3.1.171, check if it's caching the 'latest' tag"
                }
            ]
        }
    ]
    
    payload = {
        "text": "Docker Image v3.1.172 Ready - Deployment Instructions",
        "blocks": blocks,
        "username": "ClaudeOS",
        "icon_emoji": "🐳"
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print("✅ Docker instructions sent to Slack")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    send_docker_update()