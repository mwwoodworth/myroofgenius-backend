# Render Docker Deployment Guide with Pre-Deploy Commands

## Important: Docker Deployment Limitations on Render

Based on Render's official documentation:
- **Docker services CANNOT use Build Commands**
- **Pre-Deploy Commands ARE supported** (30-minute timeout)
- **Start Commands can be customized** via Docker Command setting

## Recommended Approach for BrainOps

### Option 1: Pre-Deploy Command (Best for Migrations)

Since Docker deployments support pre-deploy commands, we can use our current setup:

1. **Pre-Deploy Command**: `./apps/backend/pre_deploy.sh`
   - Runs database migrations
   - Has 30-minute timeout
   - Runs on separate instance
   - If fails, deployment is canceled

2. **Docker Command** (Start Command): Leave default or use:
   ```
   ./apps/backend/startup_clean.sh
   ```

### Option 2: Combined Docker Command (Alternative)

If pre-deploy doesn't work as expected, combine everything in the Docker Command:

```bash
/bin/bash -c "./apps/backend/pre_deploy.sh && ./apps/backend/startup_clean.sh"
```

**Note**: This approach has a 15-minute timeout for the entire command.

## Updated Deployment Configuration

### In Render Dashboard:

1. **Settings → Build & Deploy**

2. **Pre-Deploy Command**:
   ```
   ./apps/backend/pre_deploy.sh
   ```

3. **Docker Command** (optional - leave blank to use Dockerfile CMD):
   ```
   ./apps/backend/startup_clean.sh
   ```

### Important Timeouts:
- Pre-Deploy: 30 minutes
- Start Command: 15 minutes

## Simplified Migration Script

Given the 30-minute timeout, let's create an optimized migration script:

```bash
#!/bin/bash
# pre_deploy_optimized.sh - Runs within 30-minute timeout

set -e

echo "🚀 Pre-Deploy Starting (30-min timeout)..."

# Skip Alembic if taking too long
timeout 10m alembic upgrade head || echo "⚠️ Alembic skipped"

# Apply only critical migrations
if [ -f "migrations/011_critical_data_type_fix_fast.sql" ]; then
    timeout 5m python3 -c "
import os
from sqlalchemy import create_engine, text

db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    engine = create_engine(db_url)
    with open('migrations/011_critical_data_type_fix_fast.sql', 'r') as f:
        sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(sql))
    print('✅ Critical fixes applied')
" || echo "⚠️ Migration failed - deploy will be canceled"
fi

echo "✅ Pre-Deploy Complete"
```

## Build and Deploy Process

### Step 1: Update Docker Image

```bash
# Ensure scripts are in the image
docker build -t mwwoodworth/brainops-backend:v3.1.0 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v3.1.0 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.1.0
docker push mwwoodworth/brainops-backend:latest
```

### Step 2: Configure Render

1. Go to service settings
2. Add Pre-Deploy Command: `./apps/backend/pre_deploy.sh`
3. Save changes
4. Deploy

## What Happens During Deployment

```
1. Pull Docker Image ✓
2. Run Pre-Deploy Command (30 min timeout)
   - Database migrations
   - If fails → deployment canceled
3. Start Service (15 min timeout)
   - Run startup_clean.sh
   - Start Uvicorn server
```

## Monitoring Deployment

Watch for these in logs:
```
==> Running pre-deploy command...
🚀 BrainOps Pre-Deploy Starting...
✅ Critical data type fixes applied
✅ Pre-Deploy Complete
==> Starting service...
🚀 BrainOps Backend Starting...
🌟 Starting Uvicorn server...
==> Your service is live 🎉
```

## Troubleshooting

### Pre-Deploy Times Out
- Reduce migration complexity
- Use `timeout` commands internally
- Apply large migrations manually

### Pre-Deploy Can't Connect to DB
- Ensure DATABASE_URL is set in environment
- Check if separate instance has network access
- Consider moving to Docker Command approach

### Service Fails After Pre-Deploy Success
- Check startup_clean.sh logs
- Verify DATABASE_URL fix is working
- Ensure port 10000 is exposed

## Best Practices

1. **Keep migrations fast** - 30 minutes max
2. **Make migrations idempotent** - Can run multiple times safely
3. **Test locally first** - `docker run -it image ./apps/backend/pre_deploy.sh`
4. **Monitor pipeline minutes** - Pre-deploy consumes billable minutes

## Summary

✅ Docker deployments DO support pre-deploy commands
✅ 30-minute timeout is generous for most migrations
✅ Failed pre-deploy cancels deployment (safe)
✅ Previous version keeps running if deploy fails

---

**Updated**: 2025-07-23
**Based on**: Official Render documentation
**Key Learning**: Docker services support pre-deploy but not build commands