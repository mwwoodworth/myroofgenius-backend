"""
Projects compatibility endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.supabase_auth import get_authenticated_user
from database import get_db


router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


@router.get("")
def list_projects(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_authenticated_user),
):
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    rows = (
        db.execute(
            text(
                """
                SELECT id, name, description, status, priority, start_date, due_date, created_at
                FROM projects
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"tenant_id": tenant_id, "limit": limit},
        )
        .mappings()
        .all()
    )

    return {
        "projects": [
            {
                "id": str(row["id"]),
                "name": row["name"],
                "description": row["description"],
                "status": row["status"],
                "priority": row["priority"],
                "start_date": row["start_date"].isoformat() if row["start_date"] else None,
                "due_date": row["due_date"].isoformat() if row["due_date"] else None,
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in rows
        ],
        "total": len(rows),
    }
