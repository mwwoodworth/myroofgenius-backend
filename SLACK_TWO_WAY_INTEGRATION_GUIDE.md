# 🚀 BrainOps Slack Two-Way Communication Integration

## Overview

This integration enables real-time two-way communication between Slack and the BrainOps ClaudeOS multi-agent system. You can send commands via Slack and receive responses, creating a seamless development environment.

## Architecture

```
Slack User → Slack API → MyRoofGenius (/api/slack/events)
                ↓
         ClaudeOS Backend (/api/v1/claudeos/slack-command)
                ↓
         LangGraphOS Orchestrator
                ↓
         Multi-Agent Processing
                ↓
         Redis Queue & Response
                ↓
         Slack API ← Response
```

## Features

### 1. **Command Recognition**
- Automatically detects command intent
- Routes to appropriate agents
- Supports natural language processing

### 2. **Multi-Agent Support**
- **Coordinator**: Overall task management
- **Developer**: Code changes and fixes
- **Deployer**: Deployment and releases
- **Tester**: Testing and validation
- **Monitor**: System health and alerts
- **Planner**: Architecture and design
- **Documenter**: Documentation updates

### 3. **Real-time Processing**
- Redis queue for command management
- Priority-based execution
- Async processing with status updates

### 4. **Persistent Context**
- All messages stored in Supabase
- Conversation threading support
- Historical command tracking

## Setup Instructions

### 1. Configure Slack App

1. Go to https://api.slack.com/apps/A094Z281Z5H
2. Enable Event Subscriptions
3. Set Request URL: `https://myroofgenius.com/api/slack/events`
4. Subscribe to bot events:
   - `message.channels`
   - `message.im`
   - `message.groups`
   - `app_mention`

### 2. Environment Variables

Add to `.env.local` (MyRoofGenius):
```env
# Slack Credentials
SLACK_SIGNING_SECRET=8c4b99851ae4b119c5097e552583e4c1
SLACK_BOT_TOKEN=xoxb-8793573557089-9196687309280-743978...
SLACK_APP_ID=A094Z281Z5H
SLACK_CLIENT_ID=8793573557089.9169076067187
SLACK_CLIENT_SECRET=3ed23967ae043aa0f12f1548c065486b

# Backend
BRAINOPS_API_KEY=your-api-key
```

Add to Render (Backend):
```env
# Redis (optional but recommended)
REDIS_URL=redis://your-redis-instance

# Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 3. Database Setup

Run the SQL script to create tables:
```bash
psql $DATABASE_URL < CREATE_SLACK_MESSAGES_TABLE.sql
```

### 4. Deploy Components

1. **Frontend (MyRoofGenius)**:
   ```bash
   git add -A
   git commit -m "feat: Add Slack two-way communication"
   git push origin main
   # Vercel auto-deploys
   ```

2. **Backend (BrainOps)**:
   ```bash
   cd fastapi-operator-env/apps/backend
   docker build -t mwwoodworth/brainops-backend:v3.1.172 .
   docker push mwwoodworth/brainops-backend:v3.1.172
   docker push mwwoodworth/brainops-backend:latest
   # Deploy on Render
   ```

## Usage Examples

### Basic Commands

**Deploy Backend**:
```
@BrainOps deploy backend
```

**Run Tests**:
```
@BrainOps test all endpoints
```

**Check Status**:
```
@BrainOps status
```

**Fix Error**:
```
@BrainOps fix the authentication error in login endpoint
```

### Advanced Commands

**Complex Deployment**:
```
@BrainOps urgent: deploy frontend and backend, run all tests, and notify when complete
```

**Planning**:
```
@BrainOps plan a new feature for user dashboard with real-time analytics
```

**Debugging**:
```
@BrainOps debug why the memory service is returning 500 errors
```

## Command Processing Flow

1. **Message Received**: Slack sends event to webhook
2. **Signature Verified**: Security check
3. **Intent Parsed**: NLP determines command type
4. **Agents Selected**: Appropriate agents assigned
5. **Task Executed**: ClaudeOS processes command
6. **Response Sent**: Result posted back to Slack

## Monitoring

### Slack Command History
```
GET https://brainops-backend-prod.onrender.com/api/v1/claudeos/slack-history
```

### Redis Metrics
- Commands processed
- Average response time
- Error rate
- Queue depth

### Database Queries
```sql
-- Recent commands
SELECT * FROM slack_messages 
ORDER BY created_at DESC 
LIMIT 10;

-- Command performance
SELECT 
  status,
  COUNT(*) as count,
  AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_seconds
FROM slack_command_queue
GROUP BY status;
```

## Troubleshooting

### Common Issues

1. **"Invalid signature" error**:
   - Verify SLACK_SIGNING_SECRET is correct
   - Check timestamp is within 5 minutes

2. **Commands not processing**:
   - Ensure bot is in the channel
   - Check Redis connection
   - Verify backend is deployed

3. **No response received**:
   - Check SLACK_BOT_TOKEN permissions
   - Verify channel access
   - Check error logs

### Debug Endpoints

Test webhook:
```
POST /api/v1/claudeos/slack-webhook-test
```

Check integration:
```
GET /api/slack/health
```

## Security Considerations

1. **Signature Verification**: All requests verified with HMAC
2. **Token Security**: Store all tokens in environment variables
3. **Rate Limiting**: Implement to prevent abuse
4. **Access Control**: Bot only responds in authorized channels
5. **Audit Logging**: All commands logged for compliance

## Future Enhancements

1. **Interactive Components**: Buttons and modals
2. **Scheduled Tasks**: Cron-like command scheduling
3. **Multi-workspace**: Support for multiple Slack workspaces
4. **Voice Commands**: Integration with Slack Huddles
5. **AI Learning**: Command pattern recognition

## Support

For issues or questions:
- Check logs in Papertrail
- Review Slack app settings
- Verify environment variables
- Test with simple commands first

---

*Last Updated: 2025-07-31*