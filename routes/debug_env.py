"""
Debug endpoint to check environment variables (REMOVE IN PRODUCTION!)
"""

from fastapi import APIRouter
import os

router = APIRouter(prefix="/api/v1/debug", tags=["Debug"])

@router.get("/env-check")
async def check_env():
    """Check environment variables (first/last chars only for security)"""

    def mask_key(key_value):
        if not key_value:
            return "NOT_SET"
        if len(key_value) < 20:
            return f"{key_value[:3]}***{key_value[-3:]}"
        return f"{key_value[:10]}***{key_value[-10:]}"

    return {
        "OPENAI_API_KEY": mask_key(os.getenv("OPENAI_API_KEY")),
        "ANTHROPIC_API_KEY": mask_key(os.getenv("ANTHROPIC_API_KEY")),
        "GEMINI_API_KEY": mask_key(os.getenv("GEMINI_API_KEY")),
        "DATABASE_URL": "SET" if os.getenv("DATABASE_URL") else "NOT_SET",
        "total_env_vars": len(os.environ)
    }
