# Render Pre-Deploy Migration Setup - v3.1.0

## Overview

Version 3.1.0 introduces Pre-Deploy commands to handle database migrations BEFORE the service starts. This solves the migration timeout issues that have been causing deployment failures.

## What Changed

### 1. New Scripts
- **`pre_deploy.sh`** - Runs all database migrations during pre-deploy phase
- **`startup_clean.sh`** - Clean startup script without migration logic

### 2. Updated Files
- **`startup.sh`** - Now just forwards to startup_clean.sh
- **`render.yaml`** - Added preDeployCommand
- **`Dockerfile`** - Made new scripts executable

## Render Configuration

### Option 1: Using render.yaml (Recommended)

The `render.yaml` has been updated with:
```yaml
preDeployCommand: ./apps/backend/pre_deploy.sh
```

To apply:
1. Commit and push to GitHub
2. In Render dashboard, go to Settings → Build & Deploy
3. Under "Deploy Configuration", select "Use render.yaml"
4. Save changes

### Option 2: Manual Configuration

If not using render.yaml:
1. Go to your service in Render dashboard
2. Settings → Build & Deploy
3. Add Pre-Deploy Command: `./apps/backend/pre_deploy.sh`
4. Save changes

## Deployment Process

### Step 1: Build and Push Docker Image

```bash
# Login to Docker Hub
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

# Build v3.1.0
docker build -t mwwoodworth/brainops-backend:v3.1.0 -f Dockerfile .

# Tag as latest
docker tag mwwoodworth/brainops-backend:v3.1.0 mwwoodworth/brainops-backend:latest

# Push both tags
docker push mwwoodworth/brainops-backend:v3.1.0
docker push mwwoodworth/brainops-backend:latest
```

### Step 2: Deploy on Render

1. Go to Render dashboard
2. Manual Deploy → "Deploy latest commit"
3. Monitor the deployment logs

## What Happens During Deployment

### Pre-Deploy Phase (NEW)
1. Runs `pre_deploy.sh`
2. Applies Alembic migrations
3. Applies SQL migrations
4. Verifies database health
5. If any step fails, deployment is aborted

### Service Start Phase
1. Runs `startup_clean.sh`
2. Applies DATABASE_URL fix
3. Quick database connectivity check
4. Starts Uvicorn server immediately

## Benefits

1. **No More Timeouts** - Migrations run before port detection
2. **Cleaner Separation** - Migrations vs runtime concerns
3. **Fail Fast** - Bad migrations stop deployment
4. **Faster Startup** - Service starts immediately after pre-deploy

## Monitoring

During deployment, you'll see:
```
==> Running pre-deploy command...
🚀 BrainOps Pre-Deploy Starting...
🔄 Running Alembic migrations...
✅ Alembic migrations completed
🔧 Applying critical database fixes...
✅ Critical data type fixes applied
🏥 Verifying database health...
✅ Pre-deploy completed successfully!
==> Starting service...
🚀 BrainOps Backend Starting...
✅ Database connection successful
🌟 Starting Uvicorn server...
```

## Rollback Plan

If issues occur:
1. Render will automatically rollback on pre-deploy failure
2. Previous version continues running
3. Check logs to identify migration issues
4. Fix and redeploy

## Database Fixes to Apply

After successful deployment, apply comprehensive fixes:

```bash
# Connect to database
psql $DATABASE_URL

# Apply comprehensive fixes
\i BRAINOPS_DATABASE_COMPREHENSIVE_FIX.sql
```

This will:
- Fix all 486 identified schema issues
- Add missing indexes
- Enable Row Level Security
- Set up automatic update triggers

## Troubleshooting

### Pre-Deploy Fails
- Check migration SQL syntax
- Ensure DATABASE_URL is set
- Look for permission issues

### Service Won't Start After Pre-Deploy
- Check DATABASE_URL fix is working
- Verify port binding (PORT=10000)
- Check for import errors

### Database Connection Issues
- Verify DATABASE_URL format
- Check SSL requirements
- Ensure connection pooling limits

## Summary

Pre-Deploy commands ensure:
- ✅ Migrations complete before service starts
- ✅ No more "No open ports detected" errors
- ✅ Failed migrations don't bring down the service
- ✅ Cleaner, more maintainable code structure

---

**Version**: 3.1.0
**Date**: 2025-07-23
**Key Change**: Migrations moved to Pre-Deploy phase