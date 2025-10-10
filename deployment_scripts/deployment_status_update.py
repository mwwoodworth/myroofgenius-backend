#!/usr/bin/env python3
"""Send comprehensive deployment status update"""

import requests
from datetime import datetime

SLACK_WEBHOOK = "https://hooks.slack.com/services/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"

def send_update():
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📊 Deployment Status Update"}
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🐳 Backend Status:*\n• Current: v3.1.171 (redeployed but same version)\n• Ready: v3.1.173 pushed to Docker Hub\n• Issue: Render appears to be caching the :latest tag\n\n**Solution:** Change Render's Docker image setting from `:latest` to `:v3.1.173` specifically"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🌐 Frontend Status:*\n• MyRoofGenius: ❌ 500 error - Likely missing env vars in Vercel:\n  - `NEXT_PUBLIC_SUPABASE_URL`\n  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`\n  - `SUPABASE_SERVICE_ROLE_KEY`\n  - `NEXTAUTH_SECRET`\n• BrainStackStudio: ✅ Ready to deploy (pushed to GitHub)"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🤖 AUREA Status:*\n• Core: ✅ Operational\n• Chat: ✅ Working (requires auth)\n• Voice: ✅ Synthesis endpoint ready\n• Executive: ✅ Features operational\n• UI: ⏳ Frontend integration needed"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*⚡ Actions Needed:*\n1. **Render:** Change Docker image to `mwwoodworth/brainops-backend:v3.1.173`\n2. **Vercel (MyRoofGenius):** Add missing Supabase env vars\n3. **Vercel (BrainStackStudio):** Connect GitHub repo for deployment\n4. **Slack:** Configure Event Subscriptions once MyRoofGenius is fixed"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 v3.1.173 includes complete Slack integration and all AI services"
                }
            ]
        }
    ]
    
    payload = {
        "text": "Deployment Status Update",
        "blocks": blocks,
        "username": "ClaudeOS",
        "icon_emoji": "📊"
    }
    
    requests.post(SLACK_WEBHOOK, json=payload)
    print("✅ Status update sent")

if __name__ == "__main__":
    send_update()