# Slack Integration Documentation

## Overview
This document contains the complete setup for two-way Slack communication with ClaudeOS/LangGraphOS.

## Slack Bot Credentials

### App Credentials
- **App Name**: BrainOps / MyRoofGenius
- **App ID**: A09ARP0R2DE
- **Client ID**: 8793573557089.9194318968435
- **Client Secret**: ee8eded2b951054ac969e12cf8c3ee3b
- **Signing Secret**: 8c4b99851ae4b119c5097e552583e4c1
- **Verification Token**: YoUnL6IPUL2fJCRVo0kKhtxE

### OAuth & Permissions
- **Bot User OAuth Token**: xoxb-8793573557089-9196687309280-743978e4af028362d36e592d5df859c3d4bda692769b3cbfe9cc9a6dbb9b0e1ced
- **Bot User ID**: A094Z281Z5H
- **Bot Scopes**: 
  - app_mentions:read
  - channels:history
  - channels:read
  - chat:write
  - chat:write.customize
  - im:history
  - im:read
  - im:write
  - incoming-webhook

### Webhook
- **Webhook URL**: https://hooks.slack.com/services/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
- **Channel**: #general (or configured channel)

## Architecture

### 1. Frontend (MyRoofGenius)
- **Endpoint**: `/api/slack/events`
- **File**: `src/app/api/slack/events/route.ts`
- **Features**:
  - Signature verification
  - Event handling (messages, mentions, DMs)
  - Message routing to ClaudeOS
  - Response threading
  - Supabase persistence

### 2. Backend (FastAPI)
- **Endpoint**: `/api/v1/claudeos/slack-command`
- **File**: `routes/claudeos_slack.py`
- **Features**:
  - Command processing
  - Multi-agent routing
  - Intent detection
  - Priority handling
  - LangGraphOS integration

### 3. Redis Queue
- **Service**: `services/redis_service.py`
- **Features**:
  - Command queuing
  - Task distribution
  - Result caching
  - Status tracking

## Setup Instructions

### 1. Environment Variables

#### Frontend (.env.local)
```bash
# Slack Integration
SLACK_SIGNING_SECRET=8c4b99851ae4b119c5097e552583e4c1
SLACK_BOT_TOKEN=xoxb-8793573557089-9196687309280-743978e4af028362d36e592d5df859c3d4bda692769b3cbfe9cc9a6dbb9b0e1ced
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/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
SLACK_APP_ID=A09ARP0R2DE
SLACK_CLIENT_ID=8793573557089.9194318968435
SLACK_CLIENT_SECRET=ee8eded2b951054ac969e12cf8c3ee3b
SLACK_VERIFICATION_TOKEN=YoUnL6IPUL2fJCRVo0kKhtxE
```

#### Backend (.env)
```bash
# Slack Integration
SLACK_SIGNING_SECRET=8c4b99851ae4b119c5097e552583e4c1
SLACK_BOT_TOKEN=xoxb-8793573557089-9196687309280-743978e4af028362d36e592d5df859c3d4bda692769b3cbfe9cc9a6dbb9b0e1ced
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/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
```

### 2. Slack App Configuration

#### Event Subscriptions
1. Go to https://api.slack.com/apps/A09ARP0R2DE/event-subscriptions
2. Enable Events
3. Set Request URL: `https://myroofgenius.com/api/slack/events`
4. Subscribe to bot events:
   - `app_mention`
   - `message.im`
   - `message.channels`
5. Save changes

#### Interactivity & Shortcuts
1. Go to https://api.slack.com/apps/A09ARP0R2DE/interactive-messages
2. Enable Interactivity
3. Set Request URL: `https://myroofgenius.com/api/slack/interactive`

#### Slash Commands (Optional)
1. Go to https://api.slack.com/apps/A09ARP0R2DE/slash-commands
2. Create commands:
   - `/claudeos` - Main command
   - `/deploy` - Deployment command
   - `/status` - System status

### 3. Database Setup

The integration uses Supabase tables:
- `slack_messages` - Message history
- `slack_commands` - Command queue
- `slack_responses` - Response tracking

## Usage

### Basic Communication
1. **Direct Message**: DM the bot for private communication
2. **Mention**: @BrainOps in any channel
3. **Commands**: Use slash commands for specific actions

### Example Messages
```
@BrainOps deploy backend v3.1.172
@BrainOps check system status
@BrainOps analyze frontend errors
@BrainOps run tests on MyRoofGenius
```

### Agent Routing
Messages are automatically routed based on keywords:
- **deploy**: Deployer, Tester agents
- **build/fix**: Dev, Debugger agents
- **test**: Tester, QA agents
- **analyze**: Analyzer, Memory agents
- **frontend**: Frontend, UI agents
- **backend**: Backend, API agents

## Monitoring

### Health Check
```bash
curl https://myroofgenius.com/api/slack/health
```

### Logs
- Frontend: Vercel dashboard logs
- Backend: Render dashboard logs
- Slack: App activity logs

## Security

1. **Signature Verification**: All requests verified with HMAC
2. **Token Storage**: Environment variables only
3. **Rate Limiting**: Built-in Slack rate limits
4. **Access Control**: Bot permissions scoped

## Troubleshooting

### Common Issues

1. **Signature Verification Failed**
   - Check timestamp (must be within 5 minutes)
   - Verify signing secret matches

2. **Bot Not Responding**
   - Check Event Subscriptions are enabled
   - Verify Request URL is correct
   - Check bot is in the channel

3. **404 Errors**
   - Ensure routes are deployed
   - Check URL paths match

### Debug Mode
Enable debug logging:
```typescript
// Frontend
const DEBUG = true;

// Backend
logging.getLogger().setLevel(logging.DEBUG)
```

## Next Steps

1. ✅ Configure Event Subscriptions in Slack App
2. ✅ Deploy backend v3.1.172 with Slack integration
3. ✅ Add environment variables to Vercel and Render
4. ✅ Test two-way communication flow
5. ⏳ Set up monitoring dashboard
6. ⏳ Create Slack command documentation

## Support

For issues or questions:
- Slack: #dev-support channel
- Email: support@myroofgenius.com
- Docs: https://docs.myroofgenius.com/slack-integration