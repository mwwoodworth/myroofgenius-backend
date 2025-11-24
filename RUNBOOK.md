# MyRoofGenius Backend – Operations Runbook

Production API for MyRoofGenius + ERP integrations. Stack: Python 3.11, FastAPI/Uvicorn, Render.

## Endpoints & Health
- Health: `${BACKEND_URL}/health` (expects JSON with `status`, `version`, `database`, `offline_mode`).
- Public products: `${BACKEND_URL}/api/v1/products/public` (200, array).
- Port: 10000 in production (Render), 8000 locally (dev/compose).

## Environment (minimum)
- DB: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` or `DATABASE_URL` (Supabase: `aws-0-us-east-2.pooler.supabase.com`).
- API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` (as needed by AI features).
- JWT: `JWT_SECRET_KEY`.
- Misc: `ENV=production`, `PORT` (default 10000), optional `OFFLINE_MODE=false`.

## Local Dev
```bash
# Using docker compose (preferred)
docker-compose -f ../docker-compose.dev.yml up backend postgres redis

# Direct run (port 8000, hot reload)
cd myroofgenius-backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
If port 8000 is occupied by `brainops-automation-backend`, stop that container or change dev port (e.g., `--port 8001`).

## Deployment (Render)
- Service: `brainops-backend-prod` (Render Web Service).
- Build: `pip install -r requirements.txt`.
- Start: `uvicorn main:app --host 0.0.0.0 --port 10000`.
- Health check path: `/health` (must return 200).
- Post-deploy smoke: run `../scripts/backend-drift-guard.sh` and `../scripts/prod-smoke.sh`.

## Tests / Quality
- Add/maintain unit/API tests for `routes/products_public.py` and AI endpoints.
- CI/prod smoke: use `../scripts/backend-drift-guard.sh` (version drift + products endpoint) and `../scripts/prod-smoke.sh`.

## Ops Checks
- Drift: `/health` `version` must match local `version.py`.
- Data: `/api/v1/products/public` returns array; failures block deploy.
- Logs: check Render logs; locally, `logs/backend.log` (symlinked to `/mnt/extra/dev/logs`).

