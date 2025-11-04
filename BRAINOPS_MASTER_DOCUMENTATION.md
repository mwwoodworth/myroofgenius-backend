# 🧠 BrainOps AI OS - Master Documentation & SOPs

## 🎯 System Overview
- **Version**: v30.3.0
- **Status**: 73.9% Operational (17/23 endpoints)
- **Database**: 3,587 customers, 12,820 jobs, 481 tables
- **AI Agents**: 34 active agents
- **Last Updated**: 2025-09-14

## 📝 STANDARD OPERATING PROCEDURES (SOPs)

### Deployment SOPs
1. Always test locally before deployment
2. Build Docker image with version tag
3. Push to Docker Hub with both version and latest tags
4. Trigger Render deployment
5. Monitor health endpoint for version confirmation
6. Run live API tests

### Task Management SOPs
1. **ALWAYS** use TodoWrite tool for task tracking
2. Update task status in real-time
3. Only one task in_progress at a time
4. Document blockers immediately
5. Complete tasks before starting new ones
6. Sync with Notion task manager

## 🔧 CRITICAL ENVIRONMENT VARIABLES

### Database
- DATABASE_URL: PostgreSQL connection string ✅
- SUPABASE_PROJECT_REF: yomagoqdmxszqtdwuhab ✅

### Deployment
- DOCKER_PAT: dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho ✅
- RENDER_API_KEY: rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx ✅

### Integration
- NOTION_TOKEN: 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 ✅

## 🏗️ SYSTEM ARCHITECTURE

### Infrastructure
- **Production**: https://brainops-backend-prod.onrender.com
- **Database**: db.yomagoqdmxszqtdwuhab.supabase.co
- **Docker**: mwwoodworth/brainops-backend

## 📊 SYSTEM STATUS
- **Backend Health**: v30.3.0 LIVE in production ✅
- **Database**: Connected, 3,587 customers
- **Jobs**: 12,820 in system
- **AI Agents**: 34 operational
- **Endpoints**: Workflows fixed locally (needs production update)
- **Notion Sync**: ✅ 10 customers, 10 jobs synced
- **Last Deployment**: 2025-09-14 (dep-d33n51odl3ps7390v8b0)
