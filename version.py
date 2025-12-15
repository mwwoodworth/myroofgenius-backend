"""
Version management for BrainOps Backend
"""

__version__ = "163.0.23"
__build__ = "2025-12-15T20:02:00Z"
__status__ = "production"
# v163.0.23: Fix SQLAlchemy SSL context for Supabase pooler
# - database.py now uses SSL context with disabled cert verification
# - Fixes "Database temporarily unavailable" for ERP routes
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
