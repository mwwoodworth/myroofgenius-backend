"""User-management records (tenant scoped, validated updates)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from core.request_safety import parse_uuid, require_tenant_id, sanitize_payload, sanitize_text
from core.supabase_auth import get_authenticated_user

router = APIRouter()


async def get_db(request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


class UserManagementBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: str = Field(default="active", min_length=2, max_length=40)
    data: Dict[str, Any] = Field(default_factory=dict)


class UserManagementCreate(UserManagementBase):
    pass


class UserManagementUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[str] = Field(default=None, min_length=2, max_length=40)
    data: Optional[Dict[str, Any]] = None


class UserManagementResponse(UserManagementBase):
    id: str
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=UserManagementResponse)
async def create_user_management(
    item: UserManagementCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    row = await conn.fetchrow(
        """
        INSERT INTO user_management (tenant_id, name, description, status, data)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, created_at, updated_at
        """,
        tenant_id,
        sanitize_text(item.name, max_length=200),
        sanitize_text(item.description, max_length=1000),
        sanitize_text(item.status, max_length=40),
        sanitize_payload(item.data),
    )

    return {
        **item.model_dump(),
        "id": str(row["id"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/", response_model=List[UserManagementResponse])
async def list_user_management(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    query = "SELECT * FROM user_management WHERE tenant_id = $1"
    params: List[Any] = [tenant_id]

    if status:
        params.append(sanitize_text(status, max_length=40))
        query += f" AND status = ${len(params)}"

    params.extend([limit, skip])
    query += f" ORDER BY created_at DESC LIMIT ${len(params)-1} OFFSET ${len(params)}"

    rows = await conn.fetch(query, *params)
    return [
        {
            **dict(row),
            "id": str(row["id"]),
            "data": row["data"] if row["data"] else {},
        }
        for row in rows
    ]


@router.get("/{item_id}", response_model=UserManagementResponse)
async def get_user_management(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    item_uuid = parse_uuid(item_id, field_name="item_id")

    row = await conn.fetchrow(
        "SELECT * FROM user_management WHERE id = $1 AND tenant_id = $2",
        item_uuid,
        tenant_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="User management not found")

    return {
        **dict(row),
        "id": str(row["id"]),
        "data": row["data"] if row["data"] else {},
    }


@router.put("/{item_id}")
async def update_user_management(
    item_id: str,
    updates: UserManagementUpdate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    item_uuid = parse_uuid(item_id, field_name="item_id")

    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    if "name" in update_data:
        update_data["name"] = sanitize_text(update_data["name"], max_length=200)
    if "description" in update_data:
        update_data["description"] = sanitize_text(update_data["description"], max_length=1000)
    if "status" in update_data:
        update_data["status"] = sanitize_text(update_data["status"], max_length=40)
    if "data" in update_data:
        update_data["data"] = sanitize_payload(update_data["data"] or {})

    params: List[Any] = []
    set_clauses: List[str] = []
    for field, value in update_data.items():
        params.append(value)
        set_clauses.append(f"{field} = ${len(params)}")

    params.extend([item_uuid, tenant_id])
    row = await conn.fetchrow(
        f"""
        UPDATE user_management
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = ${len(params)-1} AND tenant_id = ${len(params)}
        RETURNING id
        """,
        *params,
    )

    if not row:
        raise HTTPException(status_code=404, detail="User management not found")

    return {"message": "User management updated", "id": str(row["id"])}


@router.delete("/{item_id}")
async def delete_user_management(
    item_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)
    item_uuid = parse_uuid(item_id, field_name="item_id")

    row = await conn.fetchrow(
        "DELETE FROM user_management WHERE id = $1 AND tenant_id = $2 RETURNING id",
        item_uuid,
        tenant_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="User management not found")

    return {"message": "User management deleted", "id": str(row["id"])}


@router.get("/stats/summary")
async def get_user_management_stats(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    tenant_id = require_tenant_id(current_user)

    result = await conn.fetchrow(
        """
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent
        FROM user_management
        WHERE tenant_id = $1
        """,
        tenant_id,
    )
    return dict(result)
