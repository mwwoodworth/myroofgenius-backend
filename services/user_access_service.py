"""User role/permission/invitation service."""

from __future__ import annotations

import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import HTTPException

from core.request_safety import sanitize_payload, sanitize_text

logger = logging.getLogger(__name__)


class UserAccessService:
    """Manage tenant-scoped roles, permissions, and invitations."""

    DEFAULT_PERMISSIONS = {
        "owner": ["users:write", "users:read", "billing:write", "billing:read", "leads:write", "leads:read"],
        "admin": ["users:write", "users:read", "billing:read", "leads:write", "leads:read"],
        "manager": ["users:read", "leads:write", "leads:read"],
        "member": ["users:read", "leads:read"],
        "viewer": ["users:read", "leads:read"],
    }

    async def ensure_tables(self, conn: asyncpg.Connection) -> None:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_role_assignments (
                id UUID PRIMARY KEY,
                tenant_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                role_name VARCHAR(100) NOT NULL,
                permissions JSONB,
                updated_by VARCHAR(255),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE (tenant_id, user_id)
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_invitations (
                id UUID PRIMARY KEY,
                tenant_id VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                role_name VARCHAR(100) NOT NULL,
                permissions JSONB,
                invitation_token VARCHAR(255) UNIQUE NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                invited_by VARCHAR(255),
                expires_at TIMESTAMP NOT NULL,
                accepted_at TIMESTAMP,
                accepted_user_id VARCHAR(255),
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE (tenant_id, email, status)
            )
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_invites_token ON user_invitations(invitation_token)
            """
        )

    def _resolve_permissions(self, role_name: str, permissions: Optional[List[str]]) -> List[str]:
        role_key = (role_name or "member").lower()
        if permissions:
            clean = [sanitize_text(item, max_length=120) for item in permissions if item]
            return sorted(set(item for item in clean if item))
        return list(self.DEFAULT_PERMISSIONS.get(role_key, self.DEFAULT_PERMISSIONS["member"]))

    async def assign_role(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: str,
        user_id: str,
        role_name: str,
        permissions: Optional[List[str]],
        updated_by: Optional[str],
    ) -> Dict[str, Any]:
        await self.ensure_tables(conn)

        role = sanitize_text(role_name, max_length=100)
        if not role:
            raise HTTPException(status_code=400, detail="Role is required")

        resolved_permissions = self._resolve_permissions(role, permissions)

        row = await conn.fetchrow(
            """
            INSERT INTO user_role_assignments (
                id, tenant_id, user_id, role_name,
                permissions, updated_by, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5::jsonb, $6, NOW()
            )
            ON CONFLICT (tenant_id, user_id) DO UPDATE
            SET role_name = EXCLUDED.role_name,
                permissions = EXCLUDED.permissions,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING id, role_name, permissions, updated_at
            """,
            str(uuid.uuid4()),
            tenant_id,
            sanitize_text(user_id, max_length=255),
            role,
            json.dumps(resolved_permissions),
            sanitize_text(updated_by, max_length=255),
        )

        return {
            "id": str(row["id"]),
            "role": row["role_name"],
            "permissions": row["permissions"] or [],
            "updated_at": row["updated_at"],
        }

    async def create_invitation(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: str,
        email: str,
        role_name: str,
        permissions: Optional[List[str]],
        invited_by: Optional[str],
        expires_in_hours: int = 72,
    ) -> Dict[str, Any]:
        await self.ensure_tables(conn)

        clean_email = sanitize_text(email, max_length=255)
        role = sanitize_text(role_name, max_length=100)
        if not clean_email or not role:
            raise HTTPException(status_code=400, detail="Email and role are required")

        token = secrets.token_urlsafe(36)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=max(1, expires_in_hours))
        resolved_permissions = self._resolve_permissions(role, permissions)

        try:
            row = await conn.fetchrow(
                """
                INSERT INTO user_invitations (
                    id, tenant_id, email, role_name, permissions,
                    invitation_token, status, invited_by, expires_at, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5::jsonb,
                    $6, 'pending', $7, $8, NOW()
                )
                RETURNING id, email, role_name, invitation_token, expires_at
                """,
                str(uuid.uuid4()),
                tenant_id,
                clean_email,
                role,
                json.dumps(resolved_permissions),
                token,
                sanitize_text(invited_by, max_length=255),
                expires_at,
            )
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=409, detail="An active invitation already exists for this user")

        return {
            "id": str(row["id"]),
            "email": row["email"],
            "role": row["role_name"],
            "invitation_token": row["invitation_token"],
            "expires_at": row["expires_at"],
        }

    async def list_invitations(self, conn: asyncpg.Connection, *, tenant_id: str) -> List[Dict[str, Any]]:
        await self.ensure_tables(conn)
        rows = await conn.fetch(
            """
            SELECT id, email, role_name, permissions, status, expires_at, invited_by, created_at
            FROM user_invitations
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            """,
            tenant_id,
        )

        return [
            {
                "id": str(row["id"]),
                "email": row["email"],
                "role": row["role_name"],
                "permissions": row["permissions"] or [],
                "status": row["status"],
                "expires_at": row["expires_at"],
                "invited_by": row["invited_by"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    async def accept_invitation(
        self,
        conn: asyncpg.Connection,
        *,
        invitation_token: str,
        user_id: str,
    ) -> Dict[str, Any]:
        await self.ensure_tables(conn)

        token = sanitize_text(invitation_token, max_length=255)
        if not token:
            raise HTTPException(status_code=400, detail="Invitation token is required")

        invite = await conn.fetchrow(
            """
            SELECT id, tenant_id, email, role_name, permissions, status, expires_at
            FROM user_invitations
            WHERE invitation_token = $1
            """,
            token,
        )
        if not invite:
            raise HTTPException(status_code=404, detail="Invitation not found")
        if invite["status"] != "pending":
            raise HTTPException(status_code=409, detail="Invitation has already been used")
        if invite["expires_at"] <= datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Invitation has expired")

        await conn.execute(
            """
            UPDATE user_invitations
            SET status = 'accepted', accepted_user_id = $1, accepted_at = NOW()
            WHERE id = $2
            """,
            sanitize_text(user_id, max_length=255),
            invite["id"],
        )

        await self.assign_role(
            conn,
            tenant_id=invite["tenant_id"],
            user_id=user_id,
            role_name=invite["role_name"],
            permissions=list(invite["permissions"] or []),
            updated_by=user_id,
        )

        return {
            "status": "accepted",
            "tenant_id": invite["tenant_id"],
            "email": invite["email"],
            "role": invite["role_name"],
            "permissions": invite["permissions"] or [],
        }


user_access_service = UserAccessService()
