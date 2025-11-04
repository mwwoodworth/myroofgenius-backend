"""
Inventory API
Provides inventory item listings with graceful degradation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, Optional
import logging

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


def _empty(limit: int, offset: int) -> Dict[str, Any]:
    return {
        "success": True,
        "data": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "degraded": True,
        "message": "Inventory data unavailable; returning empty list."
    }


@router.get("/items")
async def list_inventory_items(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = None,
    location_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List inventory items for the authenticated tenant."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        logger.warning("Database pool unavailable; returning fallback inventory list.")
        return _empty(limit, offset)

    query = """
        SELECT id, item_name, sku, category, quantity_on_hand,
               reorder_point, uom, location_id, created_at, updated_at
        FROM inventory_items
        WHERE tenant_id = $1
    """
    params = [tenant_id]
    param_idx = 1

    if category:
        param_idx += 1
        query += f" AND category = ${param_idx}"
        params.append(category)

    if location_id:
        param_idx += 1
        query += f" AND location_id = ${param_idx}"
        params.append(location_id)

    query += f" ORDER BY item_name LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}"
    params.extend([limit, offset])

    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM inventory_items WHERE tenant_id = $1",
                tenant_id
            )
    except Exception as exc:
        message = str(exc)
        if "does not exist" in message or "UndefinedTable" in message:
            logger.warning("Inventory schema unavailable; returning fallback dataset.")
            return _empty(limit, offset)
        logger.error(f"Error listing inventory: {message}")
        raise HTTPException(status_code=500, detail="Failed to list inventory items")

    items = []
    for row in rows:
        record = dict(row)
        record["id"] = str(record.get("id"))
        items.append(record)

    return {
        "success": True,
        "data": items,
        "total": count or 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/items/{item_id}")
async def get_inventory_item(
    item_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Retrieve an inventory item."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        logger.warning("Database pool unavailable; returning fallback inventory detail.")
        return {
            "success": True,
            "data": None,
            "degraded": True,
            "message": "Inventory data unavailable; detail cannot be retrieved."
        }

    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, item_name, sku, category, quantity_on_hand,
                       reorder_point, uom, location_id, created_at, updated_at
                FROM inventory_items
                WHERE id = $1 AND tenant_id = $2
                """,
                item_id,
                tenant_id
            )
    except Exception as exc:
        message = str(exc)
        if "does not exist" in message or "UndefinedTable" in message:
            logger.warning("Inventory schema unavailable; returning fallback inventory detail.")
            return {
                "success": True,
                "data": None,
                "degraded": True,
                "message": "Inventory schema unavailable; detail cannot be retrieved."
            }
        logger.error(f"Error retrieving inventory item {item_id}: {message}")
        raise HTTPException(status_code=500, detail="Failed to retrieve inventory item")

    if not row:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    record = dict(row)
    record["id"] = str(record.get("id"))

    return {
        "success": True,
        "data": record
    }
