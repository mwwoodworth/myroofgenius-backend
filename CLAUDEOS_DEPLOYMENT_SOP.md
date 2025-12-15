# 🚀 CLAUDEOS DEPLOYMENT SOP (Standard Operating Procedures)

## CRITICAL: USE THESE AUTOMATED DEPLOYMENT PROCEDURES - NO MANUAL STEPS

### ⚡ QUICK DEPLOYMENT COMMANDS

#### 1. Frontend (MyRoofGenius) - Vercel
```bash
# Automatic deployment on git push to main
git push origin main

# Manual deployment if needed
curl -X POST https://api.vercel.com/v13/deployments \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"myroofgenius-app","gitSource":{"ref":"main","repo":"mwwoodworth/myroofgenius-app","type":"github"}}'
```

#### 2. Backend (BrainOps) - Render
```bash
# Deploy Hook (USE THIS FIRST)
curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM

# Alternative API Deploy
curl -X POST \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys
```

#### 3. Database (Supabase) - Auto-syncs
```bash
# Database changes sync automatically
# Manual migration if needed
supabase db push
```

---

## 📋 DEPLOYMENT WORKFLOW

### Phase 1: Code Changes
1. Make code changes
2. Update version numbers
3. Commit with proper message format
4. Push to GitHub

### Phase 2: Automated Deployments
```bash
# 1. Frontend auto-deploys via Vercel GitHub integration
git push origin main

# 2. Backend requires Docker build and push, then deploy hook
cd /home/mwwoodworth/code/fastapi-operator-env
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'
docker build -t mwwoodworth/brainops-backend:vX.X.X -f Dockerfile .
docker tag mwwoodworth/brainops-backend:vX.X.X mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:vX.X.X
docker push mwwoodworth/brainops-backend:latest

# 3. Trigger Render deployment
curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM
```

### Phase 3: Verification
```bash
# Check backend health
curl https://brainops-backend-prod.onrender.com/api/v1/health

# Check frontend
curl https://myroofgenius.com

# Check database
# Via Supabase dashboard or API
```

---

## 🔑 CRITICAL CREDENTIALS (NEVER LOSE)

### Docker Hub
- Username: `mwwoodworth`
- PAT: `dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho`
- Login: `docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'`

### Render
- API Key: `rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx`
- Service ID: `srv-d1tfs4idbo4c73di6k00`
- Deploy Hook: `https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM`

### Vercel
- Set in GitHub Secrets:
  - VERCEL_TOKEN
  - VERCEL_ORG_ID  
  - VERCEL_PROJECT_ID

### Supabase
- Project Ref: `yomagoqdmxszqtdwuhab`
- Database Password: `<DB_PASSWORD_REDACTED>
- Connection: `postgresql://postgres:<DB_PASSWORD_REDACTED>@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres`

---

## 🤖 AUTOMATION SCRIPTS

### Complete Deployment Script
```bash
#!/bin/bash
# save as deploy-all.sh

echo "🚀 Starting ClaudeOS Full Deployment"

# 1. Backend Deployment
echo "📦 Building Backend Docker Image..."
cd /home/mwwoodworth/code/fastapi-operator-env
VERSION=$(grep 'VERSION = ' main.py | cut -d'"' -f2)
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'
docker build -t mwwoodworth/brainops-backend:v$VERSION -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v$VERSION mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v$VERSION
docker push mwwoodworth/brainops-backend:latest

echo "🔗 Triggering Render Deployment..."
curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM

# 2. Frontend Deployment
echo "🎨 Deploying Frontend..."
cd /home/mwwoodworth/code/myroofgenius-app
git add -A
git commit -m "chore: Deploy v$VERSION"
git push origin main

# 3. Verification
echo "✅ Verifying Deployments..."
sleep 30
curl -s https://brainops-backend-prod.onrender.com/api/v1/health | jq .
curl -s -o /dev/null -w "%{http_code}" https://myroofgenius.com

echo "🎉 Deployment Complete!"
```

### Health Check Script
```bash
#!/bin/bash
# save as check-health.sh

echo "🏥 ClaudeOS Health Check"
echo "========================"

# Backend
echo -n "Backend API: "
BACKEND_STATUS=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health | jq -r .status)
echo "✅ $BACKEND_STATUS"

# Frontend  
echo -n "Frontend: "
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://myroofgenius.com)
if [ $FRONTEND_CODE -eq 200 ]; then
    echo "✅ Operational"
else
    echo "❌ Error (HTTP $FRONTEND_CODE)"
fi

# Database
echo -n "Database: "
DB_STATUS=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health | jq -r .database)
echo "✅ $DB_STATUS"

echo "========================"
```

---

## 📡 WEBHOOK CONFIGURATIONS

### Slack Notifications
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/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
```

### Stripe Webhooks
- Endpoint: `https://myroofgenius.com/api/webhook`
- Secret: Set `STRIPE_WEBHOOK_SECRET` in Vercel

### Self-Healing Webhooks
- Make.com webhook for test failures
- Set `MAKE_WEBHOOK_URL` in GitHub Secrets

---

## 🚨 CRITICAL REMINDERS

1. **NEVER manually deploy** - Use automated hooks
2. **ALWAYS push Docker images** before triggering Render
3. **Frontend auto-deploys** on git push to main
4. **Database syncs automatically** via Supabase
5. **Check health endpoints** after deployment
6. **Use persistent memory** to track deployments

---

## 📊 MONITORING

### Real-time Monitoring
- Backend Health: https://brainops-backend-prod.onrender.com/api/v1/health
- Frontend Status: https://myroofgenius.com/api/health
- Database: Supabase Dashboard

### Logs
- Backend: Render Dashboard → Logs
- Frontend: Vercel Dashboard → Functions → Logs
- Database: Supabase Dashboard → Logs

---

## 🔄 ROLLBACK PROCEDURES

### Frontend Rollback
```bash
# Via Vercel Dashboard or CLI
vercel rollback
```

### Backend Rollback
```bash
# Deploy previous Docker image
docker push mwwoodworth/brainops-backend:v[PREVIOUS_VERSION]
curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM
```

---

## 💾 PERSISTENT MEMORY INTEGRATION

### Store Deployment Info
```typescript
// Use in deployment scripts
await createMemory({
  title: `Deployment v${version}`,
  content: `Deployed frontend and backend version ${version}`,
  memory_type: 'deployment',
  tags: ['deployment', 'production', version],
  meta_data: {
    frontend_url: 'https://myroofgenius.com',
    backend_url: 'https://brainops-backend-prod.onrender.com',
    timestamp: new Date().toISOString(),
    status: 'success'
  }
})
```

### Query Deployment History
```typescript
const deployments = await getMemories({
  memory_type: 'deployment',
  order_by: 'created_at',
  order: 'desc',
  limit: 10
})
```

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Code changes committed and pushed
- [ ] Version numbers updated
- [ ] Docker image built and pushed
- [ ] Render deployment triggered
- [ ] Frontend auto-deployed via Vercel
- [ ] Health checks passing
- [ ] Monitoring active
- [ ] Deployment logged in persistent memory

---

**REMEMBER**: This is a FULLY AUTONOMOUS SYSTEM. Use the automated deployment procedures. Manual intervention should be RARE and only for emergencies.

Last Updated: ${new Date().toISOString()}