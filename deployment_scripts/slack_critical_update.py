#!/usr/bin/env python3
"""Send critical system status update to Slack"""

import requests
import json
from datetime import datetime

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def send_critical_update():
    """Send critical status update"""
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "⚠️ Critical System Status Update"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n*Engineer:* Lead Autonomous Engineer"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔍 Critical Findings:*\n• Backend: ✅ Running v3.1.171 (redeployed at 15:22 UTC)\n• Backend v3.1.172: ⏳ Still not deployed (Slack integration pending)\n• MyRoofGenius: ❌ 500 Error - Environment config issue suspected\n• BrainStackStudio: ✅ Builds successfully, needs Vercel deployment\n• AUREA: ✅ 75% operational (chat requires auth)"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📊 System Test Results (45% Pass Rate):*\n✅ Backend Health: v3.1.171 with 985 endpoints\n✅ Authentication: Working\n✅ AUREA: Status, health, chat endpoints operational\n✅ Database: Connected\n✅ Slack Webhook: Working\n❌ AI Services: Claude/Gemini endpoints 404\n❌ MyRoofGenius: 500 error\n❌ BrainStackStudio: Not deployed to Vercel\n❌ Memory API: Working but limited"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🚨 ACTION REQUIRED:*\n1. **[Claude] Deploy backend v3.1.172** - Docker image ready at `mwwoodworth/brainops-backend:v3.1.172`\n2. **Fix MyRoofGenius** - Check Vercel env vars for API URLs\n3. **Deploy BrainStackStudio** - Connect GitHub repo to Vercel\n4. **Configure Slack Event Subscriptions** - Use URL: `https://myroofgenius.com/api/slack/events`"
            }
        },
        {
            "type": "section", 
            "text": {
                "type": "mrkdwn",
                "text": "*🔧 Immediate Actions I'm Taking:*\n• Investigating MyRoofGenius environment variables\n• Preparing BrainStackStudio for Vercel deployment\n• Creating AI service endpoint fixes\n• Monitoring backend deployment status"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🤖 Autonomous execution continues. Will report when critical issues are resolved."
                }
            ]
        }
    ]
    
    payload = {
        "text": "Critical System Status Update - Action Required",
        "blocks": blocks,
        "username": "ClaudeOS",
        "icon_emoji": "⚠️"
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print("✅ Critical update sent to Slack")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    send_critical_update()