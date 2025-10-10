# Pre-Deploy Command Summary for BrainOps

## The Solution

Use Render's Pre-Deploy Command feature to run database migrations BEFORE the service starts:

```yaml
preDeployCommand: ./apps/backend/pre_deploy.sh
```

## Why This Fixes Our Issues

1. **30-minute timeout** instead of 15 minutes for startup
2. **No more "No open ports detected"** - migrations run before port check
3. **Safe rollback** - if migrations fail, previous version keeps running
4. **Clean separation** - migrations vs runtime concerns

## Quick Setup

### 1. In Render Dashboard
- Go to Settings → Build & Deploy
- Add Pre-Deploy Command: `./apps/backend/pre_deploy.sh`
- Save

### 2. Deploy v3.1.0
```bash
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'
docker build -t mwwoodworth/brainops-backend:v3.1.0 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v3.1.0 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.1.0
docker push mwwoodworth/brainops-backend:latest
```

### 3. Trigger Deploy
- Manual deploy in Render dashboard
- Watch logs for pre-deploy execution

## Key Files

- `pre_deploy.sh` - Runs all migrations
- `startup_clean.sh` - Starts server without migrations
- `render.yaml` - Updated with preDeployCommand

## Important Notes

- Docker services support pre-deploy but NOT build commands
- Pre-deploy runs on a separate instance
- Uses billable "pipeline minutes"
- Previous version keeps running if deploy fails

## Database Schema Fixes

After deployment, apply comprehensive fixes:
```bash
psql $DATABASE_URL -f BRAINOPS_DATABASE_COMPREHENSIVE_FIX.sql
```

This fixes all 486 identified issues.

---

**Remember**: All this information is now saved in CLAUDE.md files for permanent reference.