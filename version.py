"""
Version management for BrainOps Backend
"""

__version__ = "163.4.2"
__build__ = "2026-01-18T20:18:38Z"
__status__ = "production"
# v163.4.2: Fix revenue_leads insert to include metadata in lead capture.
# v163.4.1: Fix CNS startup - set app.state.cns before optional memory storage to prevent init failure
# v163.4.0: CNS Gemini fallback - when OpenAI quota exceeded, falls back to Gemini embeddings
# v163.3.5: Stripe webhook fallback - use BRAINOPS_STRIPE_WEBHOOK_SECRET if primary is placeholder
# v163.3.4: Stripe config fallback - use NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY if primary is placeholder
# v163.3.3: Add /stripe-automation/debug-env endpoint to trace env var mystery
# v163.3.2: Make /stripe-automation/config and /health public (publishable key is client-facing)
# v163.3.1: Clean Docker rebuild - ensure env vars from Render take precedence
# v163.3.0: CNS fix - .dockerignore excludes .env, improved AI provider status logging
# v163.2.4: SECURITY - Do not log generated ENCRYPTION_KEY; fail fast in prod
# v163.2.3: /health remains shallow but reports "healthy" for compatibility
# v163.2.2: Make /health a shallow liveness probe (Render stability)
# v163.2.1: Accept X-Diagnostics-Key header for diagnostics auth
# v163.2.0: Live readiness + credits + SiteSeer video analysis + SQL hardening
# - Added /ready, /capabilities, /diagnostics endpoints
# - Added credits balance/debit API with HMAC signing + nonce replay protection
# - Added SiteSeer video analysis endpoint with frame sampling and aggregation
# - Hardened analytics SQL query path with allowlists and parameterization
# v163.1.0: SECURITY - Tenant isolation hardening (P0 fix from Codex audit)
# - Created brainops_backend DB role WITHOUT rolbypassrls (RLS now enforced)
# - Added tenant-aware database connection wrapper (sets app.current_tenant_id)
# - Database.py now sets PostgreSQL session variables for RLS enforcement
# - Added get_tenant_db() FastAPI dependency for automatic tenant context
# - Added get_tenant_connection() async context manager for direct pool use
# - Updated RLS middleware to set app.current_tenant_id from JWT claims
# v163.0.33: Fix log flooding from auth failures and Vercel log drain
# - Rate-limited JWT verification error logging (once per minute per error type)
# - Rate-limited authentication failure logging (once per minute per path)
# - Improved Vercel log drain to handle empty/malformed data silently
# v163.0.32: Self-healing production config + Database optimization
# - Fixed self_healing_system.py: Uses Supabase instead of localhost
# - Docker and Redis now graceful-optional for containerized environments
# - Database optimized: RLS on unified_brain, new indexes, ANALYZE complete
# v163.0.29: Critical AI OS fixes - Orchestrator, Routes, MCP
# - Fixed _invoke_agent: Now makes real HTTP calls to brainops-ai-agents
# - Added complete-erp alias routes: /api/v1/complete-erp/* -> /api/v1/erp/*
# - Added MCP Bridge client: Active tool execution (245 tools, 11 servers)
# - Archived 17 zombie FIX_*.py scripts
# - Explicit route loading bypasses fragile dynamic loader
# v163.0.28: Security fix - Stripe webhook signature verification
# - stripe_automation.py: Added proper webhook signature verification
# - Prevents forged webhook events
# v163.0.27: Performance & Security hardening
# - Connection pool: min=1→10, max=5→40 for 9,800+ customers scale
# - Statement caching: enabled (100 statements) for query performance
# - SQL injection: parameterized LIMIT/OFFSET in warehouse_management.py
# v163.0.26: Fix all async/await bugs and database connection issues
# - Fixed job_analytics.py: Converted from SQLAlchemy sync to asyncpg
# - Fixed admin_dashboard.py: Uses app.state.db_pool instead of new connections
# - Fixed tenants.py: Converted to asyncpg, fixed route paths
# - Fixed ai_brain_core_v2.py: Environment variable for DB password
# v163.0.24: Remove invalid ssl_context from psycopg2 connect_args
# - psycopg2 uses sslmode parameter, NOT ssl_context (that's for asyncpg)
# - sslmode=require works correctly for Supabase pooler
# v163.0.23: (broken) Attempted SSL context fix - invalid parameter
# v163.0.22: Fix get_current_user to respect API key middleware auth
# - get_current_user now checks request.state.user (set by APIKeyMiddleware) first
# - Allows both JWT and API key authentication to work with route dependencies
# - Fixes "Missing authorization header" error when using X-API-Key
# v163.0.21: Fix authentication middleware to accept API keys
# - AuthenticationMiddleware now allows X-API-Key header to pass through
# - APIKeyMiddleware properly validates API keys against database
# - Added /api/v1/logs/vercel and /api/v1/logs/render to exempt paths
# v163.0.20: SSL fix + Security hardening deployment
# v163.0.17: Previous stable version
