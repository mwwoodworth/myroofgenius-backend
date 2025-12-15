"""
Version management for BrainOps Backend
"""

__version__ = "163.0.21"
__build__ = "2025-12-15T19:42:00Z"
__status__ = "production"
# v163.0.21: Fix authentication middleware to accept API keys
# - AuthenticationMiddleware now allows X-API-Key header to pass through
# - APIKeyMiddleware properly validates API keys against database
# - Added /api/v1/logs/vercel and /api/v1/logs/render to exempt paths
# v163.0.20: SSL fix + Security hardening deployment
# v163.0.17: Previous stable version
