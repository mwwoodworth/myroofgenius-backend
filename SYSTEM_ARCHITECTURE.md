# BrainOps AI OS - Complete System Architecture

## 🏗️ System Overview
BrainOps is evolving into a true AI-native Operating System that orchestrates multiple AI agents, manages business operations, and generates revenue autonomously.

## 🔧 Unique Configurations & Critical Settings

### 1. Docker Deployment Architecture
- **CRITICAL**: main_v504.py is copied to main.py in Docker container
- **Version Management**: Version must be updated in both main.py AND main_v504.py
- **Health Endpoint**: Uses app.version dynamically (not hardcoded)

### 2. Render Deployment Pipeline
```
GitHub → Docker Hub → Render (via webhook)
         ↓
    main_v504.py → main.py in container
```

### 3. Database Architecture
- **Primary**: Supabase PostgreSQL
- **Connection**: Via pooler for production
- **Migrations**: Run via ENSURE_ALL_TABLES_V513.sql
- **Password**: Brain0ps2O2S (stored securely)

### 4. Revenue System Status (v5.13)
- **Operational**: 3/13 endpoints
  - ✅ Test Revenue
  - ✅ AI Competitor Analysis  
  - ✅ AI Estimate Generation
- **Pending**: Stripe, Pipeline, Landing Pages, Ads, Dashboard routes
- **Issue**: Route registration in FastAPI needs completion

### 5. Monitoring & Observability
- **Permanent Tools**: /scripts/observability/
  - render_monitor.py - Health & deployment status
  - watch_deployment.py - Real-time deployment tracking
  - check_deployment.sh - Quick status checks
  - test_all_revenue_routes.py - Revenue validation

### 6. Environment Variables (Render)
```
DATABASE_URL=postgresql://...
STRIPE_SECRET_KEY=sk_live_...
GEMINI_API_KEY=AIzaSyC0ymsOlEUe-...
RENDER_API_KEY=rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx
```

### 7. Multi-Repository Structure
```
/home/mwwoodworth/code/
├── fastapi-operator-env/     # Backend v5.13
├── myroofgenius-app/         # Frontend (Vercel)
├── weathercraft-erp/         # ERP System
├── brainops-aios-master/     # AI OS Core
└── brainops-task-os/         # Task Management UI
```

### 8. API Endpoints Structure
- Public: /api/v1/products/public, /api/v1/aurea/public
- Revenue: /api/v1/{test-revenue, ai-estimation, stripe-revenue, etc}
- CRM: /api/v1/crm/*
- AI: /api/v1/agents/*, /api/v1/ai-board/*

### 9. Deployment Commands
```bash
# Build & Deploy
docker build -t mwwoodworth/brainops-backend:vX.X.X .
docker push mwwoodworth/brainops-backend:vX.X.X
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"

# Monitor
python3 scripts/observability/render_monitor.py
```

### 10. Known Quirks
- Render caches Docker images aggressively - use cache bust in Dockerfile
- Version in health endpoint must use app.version not hardcoded
- Email-validator required for pydantic email fields
- Routes must be imported BEFORE app creation
- main_v504.py is the actual source file (not main.py)

## 🚀 Current Production Status

### Live Systems
- **Backend API**: v5.13 at https://brainops-backend-prod.onrender.com
- **MyRoofGenius**: https://myroofgenius.com
- **WeatherCraft**: https://weathercraft-app.vercel.app
- **Task OS**: https://brainops-task-os.vercel.app

### Database
- 1,089 CenterPoint customers synced
- All revenue tables created
- CRM fully operational
- AI memory system active

### Features Status
- ✅ Authentication: 100% operational
- ✅ CRM: Complete with full CRUD
- ✅ AI Agents: 10 agents integrated
- ✅ Memory System: Persistent and working
- ⚠️ Revenue System: 23% operational (3/13 endpoints)
- ✅ Public API: Accessible without auth
- ✅ Monitoring: Observability tools deployed

## 🎯 Next Session Starting Point

1. **Fix remaining revenue routes** (10 endpoints need registration)
2. **Complete Stripe webhook configuration**
3. **Set up SendGrid for email automation**
4. **Configure Google Ads API credentials**
5. **Deploy landing page frontend components**

## 📊 Metrics to Track
- Revenue endpoint availability (currently 3/13)
- API response times
- Database query performance
- Docker image deployment success rate
- Customer acquisition through AI estimation

## 🔐 Security Notes
- All credentials in environment variables
- Database password never in code
- API keys rotated regularly
- RLS policies on all tables
- Auth required except public routes

---
Last Updated: 2025-08-18 00:00 MDT
Version: 5.13
Status: Partially Operational