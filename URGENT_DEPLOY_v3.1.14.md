# 🚨 URGENT: Deploy v3.1.14 NOW!

## Current Status
- **Live Version**: 3.0.14 (OLD - still running)
- **Docker Hub**: v3.1.14 (READY - pushed successfully)
- **Critical Fix**: Import error fixed in v3.1.14

## ⚡ IMMEDIATE ACTION REQUIRED

### Option 1: Deploy via Render Dashboard (RECOMMENDED)
1. **Go to**: https://dashboard.render.com/web/srv-cja1ipir0cfc73gqbl70
2. **Click**: "Manual Deploy" button
3. **Select**: Image tag `v3.1.14` or `latest`
4. **Click**: "Deploy"
5. **Monitor**: Watch the deployment logs

### Option 2: Deploy via Render API
```bash
# Deploy using webhook (if configured)
curl -X POST "https://api.render.com/deploy/srv-cja1ipir0cfc73gqbl70?key=jd4i5jfsTtvmXZjTyzkjd84l"

# Or using API key
curl -X POST \
  -H "Authorization: Bearer 4b6b1a40f7b042f5a04dd1234f3e36c8" \
  -H "Content-Type: application/json" \
  -d '{"imageUrl":"docker.io/mwwoodworth/brainops-backend:v3.1.14"}' \
  https://api.render.com/v1/services/srv-cja1ipir0cfc73gqbl70/deploys
```

## 📊 Verification Steps

### 1. Check Version After Deployment
```bash
curl -s https://brainops-backend-prod.onrender.com/api/v1/health | jq .
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "service": "brainops-api",
  "version": "3.1.14"  ← MUST BE 3.1.14
}
```

### 2. Test Core Functionality
```bash
# Test authentication endpoint
curl -X POST https://brainops-backend-prod.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@brainops.com","password":"TestPassword123!"}'

# Test API docs
curl -I https://brainops-backend-prod.onrender.com/docs
```

## 🔍 What Was Fixed in v3.1.14

### Critical Import Error:
```python
# ❌ WRONG (v3.1.13)
from apps.backend.notifications import NotificationService

# ✅ FIXED (v3.1.14)
from apps.backend.services.notifications import NotificationService
```

### Also Fixed:
- All service import paths corrected
- SchedulingEngine → SchedulingService class name
- Ultimate startup script with 7 fallback strategies (from v3.1.13)

## 📝 Docker Image Details
- **Repository**: mwwoodworth/brainops-backend
- **Tag**: v3.1.14
- **Digest**: sha256:48e789caaab44102ac44bf84c1da29e7c46ec1d2eea7360db8c424531ced083e
- **Status**: ✅ Successfully pushed to Docker Hub

## ⏰ Time-Critical Notes
1. The system is currently running an OLD version (3.0.14)
2. Multiple critical fixes are waiting in v3.1.14
3. The Docker image is ready and waiting
4. Manual deployment is required via Render dashboard

## 🎯 Success Criteria
- Health endpoint shows version "3.1.14"
- No import errors in logs
- All API endpoints are accessible
- Authentication works correctly

---

**Created**: 2025-07-24 01:23 UTC
**Priority**: CRITICAL - Deploy immediately!
**Next Step**: Go to Render dashboard and deploy v3.1.14