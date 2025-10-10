#!/usr/bin/env python3
"""Send deployment success notification to Slack"""

import requests
import json
from datetime import datetime

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def send_success_notification():
    """Send deployment success notification"""
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🎉 MyRoofGenius Successfully Deployed!"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n*Build Time:* 1 minute 4 seconds\n*Location:* Washington, D.C., USA (East)"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*✅ Build Results:*\n• TypeScript compilation: Success\n• Static generation: 71 pages\n• API routes: 33 endpoints ready\n• Slack endpoints: `/api/slack/events` and `/api/slack/verify`\n• No TypeScript errors found!"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🚀 Deployment Status:*\n• Frontend: ✅ Live at https://myroofgenius.com\n• Backend: ⏳ v3.1.172 ready (awaiting manual deployment)\n• Slack Integration: ✅ Ready for Event Subscriptions"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📋 Next Steps:*\n1. ✅ Configure Slack Event Subscriptions\n   - URL: `https://myroofgenius.com/api/slack/events`\n2. ⏳ Deploy backend v3.1.172 on Render\n3. ⏳ Add Slack environment variables to Render\n4. ⏳ Test two-way communication"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔧 Today's Achievements:*\n• Fixed MyRoofGenius TypeScript build errors\n• Implemented complete Slack integration\n• Created comprehensive documentation\n• Prepared backend v3.1.172 for deployment\n• Fixed Slack URL verification challenge"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🤖 ClaudeOS Lead Autonomous Engineer - Ready for two-way communication!"
                }
            ]
        }
    ]
    
    payload = {
        "text": "MyRoofGenius Successfully Deployed!",
        "blocks": blocks,
        "username": "ClaudeOS",
        "icon_emoji": "🎉"
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print("✅ Success notification sent to Slack")
        else:
            print(f"❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    send_success_notification()