-- BRAINOPS COMPLETE KNOWLEDGE STORAGE
-- This stores ALL operational knowledge in persistent memory

-- 1. SYSTEM ARCHITECTURE
INSERT INTO copilot_messages (title, content, memory_type, role, is_pinned, tags, meta_data, is_active, created_at, updated_at) VALUES
('BRAINOPS COMPLETE SYSTEM ARCHITECTURE', E'# BRAINOPS MASTER ARCHITECTURE V4.49

## CORE INFRASTRUCTURE
- **Backend**: FastAPI v4.49 on Render (https://brainops-backend-prod.onrender.com)
- **Database**: PostgreSQL via Supabase (148 tables operational)
- **Frontend Apps**:
  - MyRoofGenius: https://myroofgenius.com (Vercel)
  - WeatherCraft ERP: https://weathercraft-erp.vercel.app
  - BrainOps Task OS: https://brainops-task-os.vercel.app
- **Docker**: mwwoodworth/brainops-backend:latest

## DATABASE CONNECTION STRINGS
- Primary: postgresql://postgres:<DB_PASSWORD_REDACTED>@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres
- Pooler: postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require

## DEPLOYMENT PIPELINE
1. Code changes → git push origin main
2. Docker build: docker build -t mwwoodworth/brainops-backend:vX.XX -f Dockerfile .
3. Docker push: docker push mwwoodworth/brainops-backend:vX.XX
4. Render deploy: curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM
5. Vercel: Auto-deploys on git push

## AI PROVIDERS (Multi-LLM Resilience)
- Primary: Claude (Anthropic)
- Secondary: GPT-4 (OpenAI)
- Tertiary: Gemini (Google)

## GITHUB REPOSITORIES
- Backend: git@github.com:mwwoodworth/fastapi-operator-env.git
- Frontend: git@github.com:mwwoodworth/myroofgenius-app.git
- ERP: https://github.com/mwwoodworth/weathercraft-erp.git
- Task OS: https://github.com/mwwoodworth/brainops-task-os.git

## CRITICAL TABLES
- env_master: Environment variables
- ai_agents: AI configurations
- automations: Workflow rules
- copilot_messages: Persistent memory
- customers/jobs/invoices: Business data
- centerpoint_sync_log: Sync tracking', 
'critical_sop', 'system', true, '{architecture,system,infrastructure,critical}', '{"version": "4.49", "critical": true}'::jsonb, true, NOW(), NOW()),

-- 2. COMPLETE CREDENTIALS AND SECRETS
('BRAINOPS CREDENTIALS VAULT', E'# CRITICAL CREDENTIALS - NEVER LOSE

## DOCKER HUB
- Username: mwwoodworth
- PAT: dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho
- Login: docker login -u mwwoodworth -p dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho

## SUPABASE
- Password: <DB_PASSWORD_REDACTED>
- Anon Key: <JWT_REDACTED>
- Service Role: <JWT_REDACTED>

## RENDER
- API Key: rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx
- Service ID: srv-d1tfs4idbo4c73di6k00
- Deploy Hook: https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM

## CENTERPOINT
- Base URL: https://api.centerpointconnect.io
- Bearer Token: eyJvcmciOiI2NmJlMzEwMzFiMGJjMTAwMDEwM2RiN2MiLCJpZCI6ImM4ZDdiMDIyNGQ4NDQ5OGI5M2MwYzY4MTc0NWU5M2Y0IiwiaCI6Im11cm11cjEyOCJ9
- Tenant ID: 97f82b360baefdd73400ad342562586

## TEST USERS
- Admin: admin@brainops.com / AdminPassword123!
- Test: test@brainops.com / TestPassword123!
- Demo: demo@myroofgenius.com / DemoPassword123!',
'critical_sop', 'system', true, '{credentials,secrets,vault,critical}', '{"version": "4.49", "encrypted": false}'::jsonb, true, NOW(), NOW()),

-- 3. OPERATIONAL PROCEDURES
('BRAINOPS OPERATIONAL PROCEDURES', E'# STANDARD OPERATING PROCEDURES

## DEPLOYMENT PROCEDURE
1. Make code changes in /home/mwwoodworth/code/fastapi-operator-env
2. Test locally: python3 test_live_api.py
3. Git commit and push:
   git add -A
   git commit -m "feat: Description"
   git push origin main
4. Build Docker:
   docker build -t mwwoodworth/brainops-backend:vX.XX -f Dockerfile .
   docker tag mwwoodworth/brainops-backend:vX.XX mwwoodworth/brainops-backend:latest
5. Push Docker:
   docker push mwwoodworth/brainops-backend:vX.XX
   docker push mwwoodworth/brainops-backend:latest
6. Deploy to Render:
   curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"

## DATABASE MIGRATIONS
1. Create migration: alembic revision -m "description"
2. Apply to production:
   DATABASE_URL="postgresql://..." psql -f migration.sql
3. Verify: psql -c "\dt"

## MONITORING PROCEDURES
- Check health: curl https://brainops-backend-prod.onrender.com/api/v1/health
- View logs: Papertrail or Render dashboard
- Database status: psql -c "SELECT COUNT(*) FROM customers"

## RECOVERY PROCEDURES
1. Backend down: Restart via Render dashboard
2. Database issues: Run sync scripts
3. Frontend issues: Redeploy via Vercel
4. Docker issues: Rebuild with --no-cache',
'critical_sop', 'system', true, '{procedures,operations,sop,deployment}', '{"version": "4.49"}'::jsonb, true, NOW(), NOW()),

-- 4. TODO TRACKING SYSTEM
('BRAINOPS MASTER TODO LIST', E'# CRITICAL TASKS FOR 100% OPERATION

## IMMEDIATE (NOW)
1. ✅ Store all knowledge in database
2. ⏳ Run CenterPoint sync for 1,089 customers
3. ⏳ Enable automations for self-healing
4. ⏳ Configure AI decision logging

## PRIORITY (24 HOURS)
1. Set up cron jobs for continuous sync
2. Enable all 7 AI agents fully
3. Configure monitoring dashboards
4. Test all API endpoints

## MAINTENANCE (WEEKLY)
1. Review system performance
2. Optimize database indexes
3. Update dependencies
4. Rotate credentials

## TRACKING
- Use copilot_messages for persistence
- Update status in real-time
- Log all decisions
- Never lose context',
'todo', 'system', true, '{todo,tasks,tracking,operational}', '{"version": "4.49", "priority": "critical"}'::jsonb, true, NOW(), NOW()),

-- 5. CENTERPOINT SYNC PROCEDURES
('CENTERPOINT DATA SYNC PROCEDURES', E'# CENTERPOINT SYNC OPERATIONS

## MANUAL SYNC COMMAND
DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require" npx tsx scripts/centerpoint-complete-sync.ts

## SYNC SCRIPTS AVAILABLE
- scripts/centerpoint-complete-sync.ts
- scripts/SYNC_CENTERPOINT_NOW.ts
- scripts/centerpoint-full-sync.ts
- scripts/populate-production-data.ts

## EXPECTED RESULTS
- 1,089 customers from CenterPoint
- Jobs, invoices, estimates populated
- Files and photos synced
- Sync logs in centerpoint_sync_log

## CRON JOB SETUP
*/30 * * * * cd /home/mwwoodworth/code/weathercraft-erp && npm run sync:centerpoint',
'critical_sop', 'system', true, '{centerpoint,sync,data,integration}', '{"version": "4.49"}'::jsonb, true, NOW(), NOW());

-- Store AI agent configurations
INSERT INTO copilot_messages (title, content, memory_type, role, is_pinned, tags, meta_data, is_active, created_at, updated_at) VALUES
('AI AGENT CONFIGURATIONS', E'# AI AGENT OPERATIONAL CONFIG

## AGENT ROSTER (7 ACTIVE)
1. **AUREA Executive AI**
   - Role: Primary control interface
   - Capabilities: Full system authority
   - Status: ACTIVE

2. **Revenue Optimization Agent**
   - Role: Self-improving revenue engine
   - Capabilities: Pricing, upsell, conversion
   - Status: ACTIVE

3. **Customer Success Agent**
   - Role: Support and engagement
   - Capabilities: Tickets, chat, email
   - Status: ACTIVE

4. **Operations Agent**
   - Role: Workflow automation
   - Capabilities: Task scheduling, resource allocation
   - Status: ACTIVE

5. **Analytics Agent**
   - Role: Data analysis and insights
   - Capabilities: Reports, predictions, trends
   - Status: ACTIVE

6. **Security Agent**
   - Role: Threat detection and response
   - Capabilities: Monitoring, alerts, remediation
   - Status: ACTIVE

7. **Integration Agent**
   - Role: Third-party coordination
   - Capabilities: API sync, webhooks, ETL
   - Status: ACTIVE

## DECISION LOGGING
All agents MUST log decisions to ai_decision_logs table
Include: agent_id, decision_type, context, outcome, timestamp',
'ai_config', 'system', true, '{ai,agents,configuration}', '{"version": "4.49"}'::jsonb, true, NOW(), NOW());

SELECT 'Knowledge base stored successfully' as status;
