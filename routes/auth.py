"""Auth compatibility endpoints backed by Supabase Auth."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from core.supabase_auth import (
    SUPABASE_URL,
    SUPABASE_JWT_SECRET,
    SUPABASE_ANON_AVAILABLE,
    SUPABASE_SERVICE_AVAILABLE,
    supabase_anon,
)
from core.request_safety import sanitize_text


router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=256)


@router.get("/health")
def auth_health():
    status = "operational" if SUPABASE_URL and SUPABASE_ANON_AVAILABLE else "degraded"
    return {
        "status": status,
        "supabase_url_configured": bool(SUPABASE_URL),
        "supabase_anon_configured": SUPABASE_ANON_AVAILABLE,
        "supabase_service_configured": SUPABASE_SERVICE_AVAILABLE,
        "supabase_jwt_configured": bool(SUPABASE_JWT_SECRET),
    }


@router.post("/login")
def login(payload: LoginRequest):
    if not supabase_anon:
        raise HTTPException(
            status_code=503,
            detail="Supabase auth is not configured (SUPABASE_URL/SUPABASE_ANON_KEY missing).",
        )

    clean_email = sanitize_text(str(payload.email), max_length=255)
    clean_password = sanitize_text(payload.password, max_length=256)
    if not clean_email or not clean_password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    try:
        response = supabase_anon.auth.sign_in_with_password(
            {"email": clean_email, "password": clean_password}
        )
    except Exception as exc:
        logger.warning("Auth login failed for %s", clean_email)
        raise HTTPException(status_code=401, detail="Invalid credentials") from exc

    session = getattr(response, "session", None)
    user = getattr(response, "user", None)
    if not session or not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_in": session.expires_in,
        "token_type": session.token_type,
        "user": {
            "id": user.id,
            "email": user.email,
            "user_metadata": user.user_metadata,
            "app_metadata": user.app_metadata,
        },
    }
