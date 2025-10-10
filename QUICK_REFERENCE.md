# BrainOps Quick Reference Guide
**Updated**: 2025-08-19 (Post-Consolidation)

## 🔑 Database Password
**CORRECT PASSWORD**: `Brain0ps2O2S`
- This is the ONLY database password
- Used in all connection strings
- Verified working in production

## 📁 Active Repositories (7 total)
1. **fastapi-operator-env/** - Backend API (v8.6)
2. **myroofgenius-app/** - Main Frontend
3. **weathercraft-erp/** - ERP System
4. **brainops-task-os/** - Task Management
5. **scripts/** - All scripts organized
6. **Creds81925.md** - Credential reference
7. **CLAUDE.md** - Master context

## 🌐 Production URLs
- Backend: https://brainops-backend-prod.onrender.com
- MyRoofGenius: https://myroofgenius.com
- WeatherCraft: https://weathercraft-erp.vercel.app
- Task OS: https://brainops-task-os.vercel.app

## 🚀 Deployment Commands
```bash
# Backend deployment
cd fastapi-operator-env
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'
docker build -t mwwoodworth/brainops-backend:vX.X.X -f Dockerfile .
docker push mwwoodworth/brainops-backend:vX.X.X

# Frontend deployment (auto via GitHub)
git push origin main
```

## 📊 System Stats
- **Tables**: 186 in database
- **Endpoints**: 1000+ API routes
- **AI Agents**: 15 active
- **Automations**: 8 workflows
- **Storage Saved**: ~6GB from cleanup

## ✅ What Was Consolidated
- Deleted 9 duplicate repositories
- Merged overlapping functionality
- Centralized all scripts
- Created master .env.production
- Fixed all incorrect passwords
- Organized everything efficiently

## 🔍 Verification Script
```bash
/home/mwwoodworth/code/VERIFY_CONSOLIDATED_SYSTEM.sh
```

## 📝 Important Files
- `.env.production` - All credentials
- `SYSTEM_CONSOLIDATION_AUDIT.md` - Full audit
- `DELETED_REPOS_LOG.md` - What was removed
- `VERIFY_CONSOLIDATED_SYSTEM.sh` - Health check