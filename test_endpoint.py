"""
Test endpoint to verify deployment
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "status": "working",
        "message": "Test endpoint is accessible",
        "version": "43.2.0"
    }

@router.get("/test/info")
async def test_info():
    """Get deployment info"""
    import os
    import sys
    return {
        "python_version": sys.version,
        "working_dir": os.getcwd(),
        "env_vars": len(os.environ),
        "modules_loaded": len(sys.modules)
    }