"""
Simplified Equipment API
Provides minimal equipment listings with graceful degradation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, Optional
import logging
import uuid

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/equipment", tags=["Equipment"])


def _empty_response(limit: int, offset: int) -> Dict[str, Any]:
    return {
        "success": True,
        "data": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "degraded": True,
        "message": "Equipment data unavailable; returning empty list."
    }


@router.get("")
async def list_equipment(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Return equipment inventory for the authenticated tenant."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        logger.warning("Database pool unavailable; returning fallback equipment list.")
        return _empty_response(limit, offset)

    query = """
        SELECT id, name, equipment_type, status, location_id,
               serial_number, purchase_date, created_at, updated_at
        FROM equipment
        WHERE tenant_id = $1
    """
    params = [tenant_id]
    param_idx = 1

    if status:
        param_idx += 1
        query += f" AND status = ${param_idx}"
        params.append(status)

    query += f" ORDER BY created_at DESC LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}"
    params.extend([limit, offset])

    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM equipment WHERE tenant_id = $1",
                tenant_id
            )
    except Exception as exc:
        message = str(exc)
        if "does not exist" in message or "UndefinedTable" in message:
            logger.warning("Equipment schema unavailable; returning fallback dataset.")
            return _empty_response(limit, offset)
        logger.error(f"Error retrieving equipment: {message}")
        raise HTTPException(status_code=500, detail="Failed to list equipment")

    equipment = []
    for row in rows:
        record = dict(row)
        record["id"] = str(record.get("id"))
        equipment.append(record)

    return {
        "success": True,
        "data": equipment,
        "total": count or 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/{equipment_id}")
async def get_equipment(
    equipment_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Fetch a single piece of equipment."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        logger.warning("Database pool unavailable; returning fallback equipment detail.")
        return {
            "success": True,
            "data": None,
            "degraded": True,
            "message": "Equipment data unavailable; detail cannot be retrieved."
        }

    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, name, equipment_type, status, location_id,
                       serial_number, purchase_date, created_at, updated_at
                FROM equipment
                WHERE id = $1::uuid AND tenant_id = $2
                """,
                uuid.UUID(equipment_id),
                tenant_id
            )
    except Exception as exc:
        message = str(exc)
        if "does not exist" in message or "UndefinedTable" in message:
            logger.warning("Equipment schema unavailable; returning fallback equipment detail.")
            return {
                "success": True,
                "data": None,
                "degraded": True,
                "message": "Equipment schema unavailable; detail cannot be retrieved."
            }
        logger.error(f"Error retrieving equipment {equipment_id}: {message}")
        raise HTTPException(status_code=500, detail="Failed to retrieve equipment")

    if not row:
        raise HTTPException(status_code=404, detail="Equipment not found")

    record = dict(row)
    record["id"] = str(record.get("id"))

    return {
        "success": True,
        "data": record
    }
