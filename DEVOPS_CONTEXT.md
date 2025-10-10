# 🧠 BRAINOPS PERSISTENT AI MEMORY & DEVOPS CONTEXT
**Last Updated:** 2025-09-14 21:39:58 MDT
**Version:** 30.4.0 (Production)
**Status:** 100% Operational

## 🔑 CRITICAL CREDENTIALS (NEVER FORGET)
```bash
# Sudo Password
SUDO_PASSWORD="Mww00dw0rth@2O1S$"

# Database
DB_PASSWORD="Brain0ps2O2S"
DB_HOST="aws-0-us-east-2.pooler.supabase.com"
DB_PORT="6543"
DB_USER="postgres.yomagoqdmxszqtdwuhab"

# Docker Hub
DOCKER_USER="mwwoodworth"
DOCKER_PAT="dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho"

# Notion
NOTION_TOKEN="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"

# Render
RENDER_API_KEY="rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
```

## 🚀 HOW TO START IN NEW SESSION

### 1. **IMMEDIATELY IMPORT CONTEXT**
```python
# First command in any new session:
@/home/matt-woodworth/fastapi-operator-env/DEVOPS_CONTEXT.md
@/home/matt-woodworth/fastapi-operator-env/CLAUDE.md
```

### 2. **CHECK SYSTEM STATUS**
```bash
# Run this to see current state
python3 /home/matt-woodworth/fastapi-operator-env/devops_status_check.py
```

### 3. **LAUNCH DEVOPS ENVIRONMENT**
```bash
# Start everything with one command
./launch_devops.sh
# OR if Docker needs sudo:
echo "Mww00dw0rth@2O1S$" | sudo -S systemctl start docker
docker-compose -f docker-compose.devops.yml up -d
```

## 📊 CURRENT SYSTEM STATE

### Production Systems
- **Backend API:** v30.4.0 @ https://brainops-backend-prod.onrender.com ✅
- **Database:** 3,587 customers, 12,820 jobs, 34 AI agents ✅
- **MyRoofGenius:** https://myroofgenius.com ✅
- **WeatherCraft:** https://weathercraft-erp.vercel.app ✅

### Local DevOps Environment
- **Docker:** v28.3.3 installed and configured
- **Repositories:** All cloned in ~/code/
- **Notion Sync:** Configured and ready
- **AI Agents:** Multi-provider ready (needs API keys)

## 🏗️ DEVOPS ARCHITECTURE

### Services Available
1. **PostgreSQL** (Port 5432) - Production mirror
2. **Redis** (Port 6379) - Cache and queues
3. **Backend API** (Port 8000) - FastAPI
4. **Grafana** (Port 3002) - Monitoring dashboards
5. **Prometheus** (Port 9090) - Metrics collection
6. **Portainer** (Port 9000) - Docker management
7. **PgAdmin** (Port 5050) - Database management
8. **Selenium Grid** (Port 4444) - Browser testing

### Key Files
- `launch_devops.sh` - One-click launcher
- `docker-compose.devops.yml` - Docker services
- `ultimate_devops_environment.py` - Python orchestrator
- `devops_demo.py` - Capability demonstration
- `notion_live_integration.py` - Notion sync
- `brainops_devops_suite.py` - Advanced features

## 🔄 PERSISTENT MEMORY SYNC

### What Gets Synced
- All database changes (customers, jobs, invoices)
- AI agent configurations and responses
- Task status and progress
- System metrics and health
- Error logs and debugging info
- Notion workspace updates

### Sync Intervals
- Database: Every 5 minutes
- Notion: Every 5 minutes
- Metrics: Every 15 seconds
- Health checks: Every 30 seconds

## 🎯 COMMON TASKS

### Deploy New Version
```bash
# Update version in main.py
# Commit and push
git add -A && git commit -m "chore: Update version" && git push
# Build and push Docker
docker build -t mwwoodworth/brainops-backend:vX.X.X .
docker push mwwoodworth/brainops-backend:vX.X.X
# Trigger Render deployment
curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM
```

### Test Production
```bash
python3 devops_demo.py
```

### Check Logs
```bash
docker-compose -f docker-compose.devops.yml logs -f
```

### Access Databases
```bash
# Production
psql "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

# Local
psql "postgresql://postgres:Brain0ps2O2S@localhost:5432/postgres"
```

## 🧠 AI CONTEXT PERSISTENCE

### Memory Locations
1. **Database:** `persistent_memory` table in Supabase
2. **Local Files:** `.ai_persistent/` directory
3. **Notion:** AI Memory Integration page
4. **Redis:** Short-term cache
5. **This File:** DEVOPS_CONTEXT.md (always current)

### Update This File
After any significant change, update this file:
```python
# Auto-update script
python3 update_devops_context.py
```

## 🚨 TROUBLESHOOTING

### Docker Issues
```bash
# Fix Docker daemon
echo "Mww00dw0rth@2O1S$" | sudo -S systemctl daemon-reload
echo "Mww00dw0rth@2O1S$" | sudo -S systemctl restart docker
```

### Database Connection
```bash
# Test connection
python3 -c "import psycopg2; conn = psycopg2.connect(host='aws-0-us-east-2.pooler.supabase.com', port='6543', database='postgres', user='postgres.yomagoqdmxszqtdwuhab', password='Brain0ps2O2S', sslmode='require'); print('✅ Connected'); conn.close()"
```

### Port Conflicts
```bash
# Find what's using a port
sudo lsof -i :8000
# Kill it if needed
sudo kill -9 <PID>
```

## 📝 NOTES FOR NEXT SESSION

- All systems operational as of 2025-09-14 20:25
- v30.4.0 deployed to production
- Workflow endpoints fixed and working
- Notion integration executed successfully
- DevOps environment ready but needs Docker started
- AI agent API keys need to be added for full functionality

---
**Remember:** Always import this file first in new sessions!