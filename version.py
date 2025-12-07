"""
Version management for BrainOps Backend
"""

__version__ = "163.0.17"
__build__ = "2025-12-07T00:00:00Z"
__status__ = "production"
# v163.0.16: Resilient health check - always returns 200 OK for Render stability
# - Health check returns 200 with status field instead of 503
# - Added connection pool recycling (60s idle timeout)
# - Reduced pool size for Supabase pooler compatibility
# - Increased command timeout for slow queries
