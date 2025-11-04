"""
Estimates API
Lightweight estimates endpoints with graceful degradation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, Optional
import logging

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/estimates", tags=["Estimates"])


def _empty(limit: int, offset: int) -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "total": 0,
            "estimates": [],
            "limit": limit,
            "offset": offset
        },
        "degraded": True,
        "message": "Estimates data unavailable; returning empty list."
    }


@router.get("")
@router.get("/")
async def list_estimates(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List estimates for the authenticated tenant."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    db_pool = getattr(request.app.state, "db_pool", None)
    if not db_pool:
        logger.warning("Database pool unavailable; returning fallback estimates list.")
        return _empty(limit, offset)

    query = """
        SELECT id, estimate_number, customer_id, title, status,
               total_amount, created_at
        FROM estimates
        WHERE tenant_id = $1
    """
    params = [tenant_id]
    param_idx = 1

    if status:
        param_idx += 1
        query += f" AND status = ${param_idx}"
        params.append(status)

    if customer_id:
        param_idx += 1
        query += f" AND customer_id = ${param_idx}"
        params.append(customer_id)

    query += f" ORDER BY created_at DESC LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}"
    params.extend([limit, offset])

    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM estimates WHERE tenant_id = $1",
                tenant_id
            )
    except Exception as exc:
        logger.warning(f"Estimates listing degraded fallback activated: {exc}")
        return _empty(limit, offset)

    estimates = []
    for row in rows:
        record = dict(row)
        record["id"] = str(record.get("id"))
        if record.get("total_amount") is not None:
            record["total_amount"] = float(record["total_amount"])
        estimates.append(record)

    return {
        "success": True,
        "data": {
            "total": count or 0,
            "estimates": estimates,
            "limit": limit,
            "offset": offset
        }
    }
