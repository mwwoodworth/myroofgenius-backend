# 🚀 Slack Integration Deployment Instructions

## Immediate Actions Required

### 1. Configure Slack App (5 minutes)

1. Go to: https://api.slack.com/apps/A094Z281Z5H
2. Navigate to **Event Subscriptions**
3. Enable Events
4. Set Request URL: `https://myroofgenius.com/api/slack/events`
5. Add Bot Events:
   - `app_mention`
   - `message.channels`
   - `message.groups`
   - `message.im`
6. Save Changes

### 2. Add Environment Variables

#### Vercel (MyRoofGenius)
Go to: https://vercel.com/dashboard/project/myroofgenius/settings/environment-variables

Add these variables:
```
SLACK_SIGNING_SECRET=8c4b99851ae4b119c5097e552583e4c1
SLACK_BOT_TOKEN=xoxb-8793573557089-9196687309280-743978e4af028362d36e592d5df859c3d4bda692769b3cbfe9cc9a6dbb9b0e1ced
SLACK_APP_ID=A094Z281Z5H
BRAINOPS_API_KEY=[generate-secure-key]
```

#### Render (Backend)
Go to: https://dashboard.render.com/web/srv-cja1ipir0cfc73gqbl70/env

Add:
```
REDIS_URL=redis://[your-redis-instance]  # Optional but recommended
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/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
```

### 3. Create Database Tables

Run this SQL in Supabase SQL Editor:
```sql
-- Copy contents from CREATE_SLACK_MESSAGES_TABLE.sql
```

### 4. Deploy Backend

```bash
cd /home/mwwoodworth/code/fastapi-operator-env/apps/backend
docker build -t mwwoodworth/brainops-backend:v3.1.172 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v3.1.172 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.1.172
docker push mwwoodworth/brainops-backend:latest
```

Then trigger deployment on Render dashboard.

### 5. Frontend Auto-Deploys

MyRoofGenius will auto-deploy via Vercel (already pushed to GitHub).

## Testing the Integration

### Step 1: Verify Deployment
- Frontend: Check https://myroofgenius.com/api/slack/events returns 405 (GET not allowed)
- Backend: Check https://brainops-backend-prod.onrender.com/api/v1/claudeos/slack-webhook-test

### Step 2: Test in Slack
1. Go to your Slack workspace
2. Send a DM to @BrainOps Notifications
3. Try: "status"
4. You should see:
   - "🤖 Processing your request..."
   - Followed by the actual response

### Step 3: Test Commands
- `@BrainOps status` - System health check
- `@BrainOps help` - Available commands
- `@BrainOps deploy backend` - Deployment command
- `@BrainOps test all` - Run tests

## Troubleshooting

### If events aren't received:
1. Check Slack Event Subscriptions URL is verified
2. Verify environment variables in Vercel
3. Check Vercel function logs

### If responses aren't sent:
1. Verify SLACK_BOT_TOKEN is correct
2. Check bot has channel access
3. Review backend logs in Papertrail

### Debug Tools:
- Slack Event Log: https://api.slack.com/apps/A094Z281Z5H/event-subscriptions
- Vercel Logs: https://vercel.com/dashboard/project/myroofgenius/functions
- Backend Logs: https://dashboard.render.com/web/srv-cja1ipir0cfc73gqbl70/logs

## Success Indicators

✅ Slack shows "Your URL has been verified" in Event Subscriptions
✅ Bot responds to mentions and DMs
✅ Commands execute and return results
✅ Thread replies work correctly
✅ Database shows message records

## Next Steps

Once working:
1. Add more command types
2. Implement interactive components
3. Set up scheduled tasks
4. Add team notifications
5. Create command shortcuts

---

**Ready to Deploy!** 🚀