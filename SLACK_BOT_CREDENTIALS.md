# BrainOps Slack Bot Integration Credentials

## ⚠️ CONFIDENTIAL - DO NOT COMMIT TO GIT

### App Information
- **App Name**: BrainOps Notifications
- **App ID**: A094Z281Z5H
- **Client ID**: 8793573557089.9169076067187

### Secret Keys (SENSITIVE)
- **Client Secret**: 3ed23967ae043aa0f12f1548c065486b
- **Signing Secret**: 8c4b99851ae4b119c5097e552583e4c1
- **Verification Token**: ae268i63PugrWqkhs56LFdYJ

### OAuth Tokens
- **xapp Token**: xapp-1-A094Z281Z5H-9256950304852-3b736b4402f4331cadc9fff54481f001aa7e2e85c2e2e82c53ebd789b5b7e6fc
- **xoxe.xoxb Token**: xoxe.xoxb-1-MS0yLTg3OTM1NzM1NTcwODktOTE5NjY4NzMwOTI4MC05Mjg1OTg3MjA0MTAwLTkyODU5ODcyMTc2NTItNzQzOTc4NGFmMDI4MzYyZDM2ZTU5MmQ1ZGY4NTljM2Q0YmRhNjkyNzY5M2NiZmU5Y2M5YTZkYmI5YjBlMWNlZA
- **xoxe Token**: xoxe-1-My0xLTg3OTM1NzM1NTcwODktOTI4NTk4NzIwNDEwMC05Mjg1OTg3MjE3ODI4LTk5YmE1ZDM2Yzk0ZDViN2Q3NDI5NDU0YThiNWEwNmQzMGNlZDc1ZDVjNzU2MGY3MGIwOWE0MDcwNzAyNzA5MWQ

### OAuth Callback
- **Redirect URL**: https://myroofgenius.com/api/slack/oauth/callback

### Key Permissions (Bot Token Scopes)
- chat:write - Send messages
- channels:history - View channel messages
- channels:manage - Manage channels
- files:write - Upload files
- incoming-webhook - Post to specific channels
- app_mentions:read - See @mentions
- conversations.connect:manage - Manage Slack Connect

### Current Webhook URL (Working)
```
https://hooks.slack.com/services/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
```

## Implementation Notes

To enable two-way communication:

1. **Set up Event Subscriptions** in Slack app settings
2. **Create webhook endpoint** at `/api/slack/events`
3. **Implement message polling** or WebSocket connection
4. **Store tokens securely** in environment variables

## Security Notes
- NEVER commit these credentials to git
- Store in secure environment variables only
- Rotate tokens regularly
- Use IP restrictions if possible