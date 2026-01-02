# BrainOps Backend - Development Context

## Quick Reference

### Database Connection
```
Host: aws-0-us-east-2.pooler.supabase.com
User: postgres.yomagoqdmxszqtdwuhab
Database: postgres
Password: ${DB_PASSWORD}
```

**Connection Strings**:
- Pooler: `${DATABASE_URL}` (see secure credentials file)

### Production URLs
| Service | URL |
|---------|-----|
| Backend API | https://brainops-backend-prod.onrender.com |
| MyRoofGenius | https://myroofgenius.com |
| Weathercraft ERP | https://weathercraft-erp.vercel.app |

## System Architecture

```
Backend: FastAPI (Python) on Render
Frontend: Next.js on Vercel
Database: PostgreSQL via Supabase
AI: Claude, Gemini, GPT-4
```

## Docker Deployment

```bash
# Login
docker login -u mwwoodworth -p '${DOCKER_PAT}'

# Build and push
docker build -t mwwoodworth/brainops-backend:vX.X.X -f Dockerfile .
docker tag mwwoodworth/brainops-backend:vX.X.X mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:vX.X.X
docker push mwwoodworth/brainops-backend:latest
```

**Render Deploy Hook**: `https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=${RENDER_DEPLOY_KEY}`

## Test Credentials
- Admin: admin@brainops.com / AdminPassword123!
- Test: test@brainops.com / TestPassword123!
- Demo: demo@myroofgenius.com / DemoPassword123!

## Render Environment Variables
Required:
- DATABASE_URL
- JWT_SECRET_KEY
- GEMINI_API_KEY
- ANTHROPIC_API_KEY (if using Claude)
- OPENAI_API_KEY (if using GPT)

## Repository Structure
```
/home/matt-woodworth/dev/
├── myroofgenius-backend/     # This repo - FastAPI backend
├── myroofgenius-app/         # Frontend (Next.js)
├── weathercraft-erp/         # ERP frontend
└── brainops-ai-agents/       # AI agents service
```

## Key Commands

```bash
# Test live API
curl https://brainops-backend-prod.onrender.com/api/v1/health

# Check DB
PGPASSWORD=${DB_PASSWORD} psql -h aws-0-us-east-2.pooler.supabase.com \
  -U postgres.yomagoqdmxszqtdwuhab -d postgres -c "SELECT COUNT(*) FROM customers;"
```

## Operational Notes
1. Render does NOT auto-deploy from Docker Hub - trigger manually
2. Always push Docker images after code changes
3. Database schema must match code before deployment
4. Update version in main.py and api_health.py
5. This file is gitignored - credentials are LOCAL ONLY
