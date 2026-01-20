"""
User compatibility endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Any, Dict

from core.supabase_auth import get_authenticated_user


router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me")
async def get_current_user(current_user: Dict[str, Any] = Depends(get_authenticated_user)):
    return {
        "id": current_user.get("id"),
        "email": current_user.get("email"),
        "tenant_id": current_user.get("tenant_id"),
        "role": current_user.get("role"),
        "user_metadata": current_user.get("user_metadata"),
        "app_metadata": current_user.get("app_metadata"),
    }
