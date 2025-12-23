"""
Version management for BrainOps Backend
"""

__version__ = "163.0.27"
__build__ = "2025-12-23T18:30:00Z"
__status__ = "production"
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
