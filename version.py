"""
Version management for BrainOps Backend
"""

__version__ = "163.0.20"
__build__ = "2025-12-15T19:30:00Z"
__status__ = "production"
# v163.0.20: SSL fix + Security hardening deployment
# - Fixed SSL certificate verification for Supabase pooler
# - MCP Bridge auth now requires X-API-Key
# - Backend auth properly validates API keys
# v163.0.17: Previous stable version
