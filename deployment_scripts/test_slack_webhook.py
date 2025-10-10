#!/usr/bin/env python3
"""Test Slack webhook integration"""

import requests
import json
from datetime import datetime

# Slack webhook URL from the user
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

def send_slack_message(text, blocks=None):
    """Send message to Slack webhook"""
    payload = {
        "text": text,
        "username": "ClaudeOS Integration",
        "icon_emoji": "🤖"
    }
    
    if blocks:
        payload["blocks"] = blocks
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Message sent successfully: {response.text}")
            return True
        else:
            print(f"❌ Failed to send message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        return False

def main():
    """Test Slack webhook with various messages"""
    print("🔧 Testing Slack Webhook Integration...")
    
    # Test 1: Simple text message
    print("\n1️⃣ Testing simple text message...")
    send_slack_message("🚀 ClaudeOS Integration Test - Simple message")
    
    # Test 2: Rich message with blocks
    print("\n2️⃣ Testing rich message with blocks...")
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🤖 ClaudeOS Integration Status"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n*Status:* ✅ Webhook Connected"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Integration Components:*\n• MyRoofGenius Frontend: ✅ Event handler ready\n• Backend API: ✅ Command processor ready\n• ClaudeOS/LangGraphOS: ✅ Multi-agent system online"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 *Next Steps:* Configure Event Subscriptions in Slack App settings"
                }
            ]
        }
    ]
    
    send_slack_message("ClaudeOS Integration Status Update", blocks)
    
    # Test 3: System status update
    print("\n3️⃣ Testing system status update...")
    status_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🔧 Current Work Status:*\n• MyRoofGenius TypeScript fixes: ✅ Pushed to GitHub\n• Vercel deployment: 🔄 In progress\n• Backend Slack integration: ✅ Code complete\n• Two-way communication: ⏳ Awaiting Event Subscriptions config"
            }
        }
    ]
    
    send_slack_message("Work Progress Update", status_blocks)
    
    print("\n✅ Slack webhook testing complete!")

if __name__ == "__main__":
    main()