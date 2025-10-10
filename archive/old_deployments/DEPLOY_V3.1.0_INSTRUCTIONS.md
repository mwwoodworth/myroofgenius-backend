# Deploy v3.1.0 - Final Instructions

## ✅ Completed Steps

1. **Code Changes** - All files updated and committed
2. **Docker Image** - v3.1.0 built and pushed to Docker Hub
3. **Documentation** - All CLAUDE.md files updated with pre-deploy knowledge

## 🚀 Next Steps (Manual in Render Dashboard)

### 1. Configure Pre-Deploy Command

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your service: `brainops-backend-prod`
3. Go to **Settings** → **Build & Deploy**
4. In **Pre-Deploy Command** field, enter:
   ```
   ./apps/backend/pre_deploy.sh
   ```
5. Click **Save Changes**

### 2. Trigger Deployment

1. Go to **Manual Deploy** section
2. Click **Deploy latest commit**
3. Monitor the deployment logs

### 3. What to Watch For

During deployment, you should see:

```
==> Pulling Docker image...
==> Running pre-deploy command...
🚀 BrainOps Pre-Deploy Starting...
🔄 Running Alembic migrations...
✅ Alembic migrations completed
🔧 Applying critical database fixes...
✅ Critical data type fixes applied
🏥 Verifying database health...
  ✅ memory_entries: X records
  ✅ users: X records
  ✅ projects: X records
  ✅ memory_entries.version type: integer
✅ Pre-deploy completed successfully!
==> Starting service...
🚀 BrainOps Backend Starting...
📌 Using startup.sh (migrations handled by pre-deploy)
✅ Database connection successful
🌟 Starting Uvicorn server...
==> Your service is live 🎉
```

### 4. Verify Deployment

Once deployed, check:
```bash
curl https://brainops-backend-prod.onrender.com/api/v1/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "service": "brainops-api",
  "version": "3.1.0"
}
```

## 📊 Database Fixes (After Deployment)

Once v3.1.0 is running successfully, apply the comprehensive database fixes:

```bash
# Connect to production database
psql $DATABASE_URL

# Apply all 486 fixes
\i BRAINOPS_DATABASE_COMPREHENSIVE_FIX.sql
```

This will:
- Fix 2 critical issues (missing primary keys)
- Fix 59 major issues (timestamp defaults)
- Fix 191 minor issues (NOT NULL constraints)
- Fix 228 performance issues (missing indexes)
- Fix 6 security issues (enable RLS)

## 🎯 Success Criteria

- [x] Version shows 3.1.0
- [ ] Pre-deploy runs successfully
- [ ] No "No open ports detected" errors
- [ ] Service starts within 15 minutes
- [ ] Health endpoint responds
- [ ] No migration errors in logs

## ⚠️ If Issues Occur

1. **Pre-Deploy Fails**: Check DATABASE_URL is set correctly
2. **Service Won't Start**: Check startup_clean.sh logs
3. **Migrations Timeout**: The 30-minute timeout should be sufficient
4. **Rollback**: Previous version (3.0.16) will keep running

---

**Version**: 3.1.0
**Date**: 2025-07-23
**Key Feature**: Pre-Deploy Migrations