"""User compatibility and access-management endpoints."""

from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from core.request_safety import require_tenant_id, sanitize_payload
from core.supabase_auth import get_authenticated_user
from services.user_access_service import user_access_service


router = APIRouter(prefix="/api/v1/users", tags=["Users"])


async def get_db_conn(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")
    async with pool.acquire() as conn:
        yield conn


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(..., min_length=2, max_length=100)
    permissions: Optional[List[str]] = None
    expires_in_hours: int = Field(default=72, ge=1, le=720)


class AcceptInviteRequest(BaseModel):
    invitation_token: str = Field(..., min_length=12, max_length=255)


class RoleAssignmentRequest(BaseModel):
    user_id: str = Field(..., min_length=2, max_length=255)
    role: str = Field(..., min_length=2, max_length=100)
    permissions: Optional[List[str]] = None


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


@router.get("/permissions/available")
async def get_available_permissions():
    return {"roles": user_access_service.DEFAULT_PERMISSIONS}


@router.post("/roles/assign")
async def assign_user_role(
    payload: RoleAssignmentRequest,
    conn: asyncpg.Connection = Depends(get_db_conn),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    result = await user_access_service.assign_role(
        conn,
        tenant_id=tenant_id,
        user_id=payload.user_id,
        role_name=payload.role,
        permissions=payload.permissions,
        updated_by=str(current_user.get("id") or ""),
    )
    return result


@router.post("/invitations")
async def invite_user(
    payload: InviteRequest,
    conn: asyncpg.Connection = Depends(get_db_conn),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    result = await user_access_service.create_invitation(
        conn,
        tenant_id=tenant_id,
        email=str(payload.email),
        role_name=payload.role,
        permissions=payload.permissions,
        invited_by=str(current_user.get("id") or ""),
        expires_in_hours=payload.expires_in_hours,
    )
    return sanitize_payload(result)


@router.get("/invitations")
async def list_invitations(
    conn: asyncpg.Connection = Depends(get_db_conn),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    return await user_access_service.list_invitations(conn, tenant_id=tenant_id)


@router.post("/invitations/accept")
async def accept_invitation(
    payload: AcceptInviteRequest,
    conn: asyncpg.Connection = Depends(get_db_conn),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return await user_access_service.accept_invitation(
        conn,
        invitation_token=payload.invitation_token,
        user_id=str(user_id),
    )
