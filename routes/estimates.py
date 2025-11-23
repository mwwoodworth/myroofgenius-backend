"""
Estimates API
Full CRUD for Estimates with Tenant Isolation
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, Optional, List
import logging
import json

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/estimates", tags=["Estimates"])

@router.get("")
@router.get("/")
async def list_estimates(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    job_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List estimates for the authenticated tenant."""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        db_pool = getattr(request.app.state, "db_pool", None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        query = """
            SELECT e.id, e.estimate_number, e.customer_id, e.job_id, e.title, e.status,
                   e.total_amount, e.subtotal, e.tax_amount, e.expires_at, e.created_at,
                   c.name as customer_name,
                   j.title as job_title
            FROM estimates e
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN jobs j ON e.job_id = j.id
            WHERE e.tenant_id = $1
        """
        params = [tenant_id]
        param_idx = 1

        if status:
            param_idx += 1
            query += f" AND e.status = ${param_idx}"
            params.append(status)

        if customer_id:
            param_idx += 1
            query += f" AND e.customer_id = ${param_idx}"
            params.append(customer_id)

        if job_id:
            param_idx += 1
            query += f" AND e.job_id = ${param_idx}"
            params.append(job_id)

        query += f" ORDER BY e.created_at DESC LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}"
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            # Count query
            count_query = "SELECT COUNT(*) FROM estimates WHERE tenant_id = $1"
            count_params = [tenant_id]
            cp = 1
            
            if status:
                cp += 1
                count_query += f" AND status = ${cp}"
                count_params.append(status)
            if customer_id:
                cp += 1
                count_query += f" AND customer_id = ${cp}"
                count_params.append(customer_id)
            if job_id:
                cp += 1
                count_query += f" AND job_id = ${cp}"
                count_params.append(job_id)
                
            total = await conn.fetchval(count_query, *count_params)

        estimates = []
        for row in rows:
            record = dict(row)
            record["id"] = str(record.get("id"))
            # Convert decimals
            for f in ["total_amount", "subtotal", "tax_amount"]:
                if record.get(f) is not None:
                    record[f] = float(record[f])
            estimates.append(record)

        return {
            "success": True,
            "data": {
                "total": total or 0,
                "estimates": estimates,
                "limit": limit,
                "offset": offset
            }
        }

    except Exception as e:
        logger.error(f"Error listing estimates: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to list estimates")

@router.get("/{estimate_id}")
async def get_estimate(
    estimate_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get estimate details."""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        db_pool = getattr(request.app.state, "db_pool", None)
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT e.id, e.estimate_number, e.customer_id, e.job_id, e.title, e.status,
                       e.total_amount, e.subtotal, e.tax_amount, e.items, e.notes, e.terms,
                       e.expires_at, e.created_at,
                       c.name as customer_name, c.email as customer_email,
                       j.title as job_title
                FROM estimates e
                LEFT JOIN customers c ON e.customer_id = c.id
                LEFT JOIN jobs j ON e.job_id = j.id
                WHERE e.id = $1::uuid AND e.tenant_id = $2
            """, estimate_id, tenant_id)

        if not row:
            raise HTTPException(status_code=404, detail="Estimate not found")

        estimate = dict(row)
        estimate["id"] = str(estimate.get("id"))
        
        # Convert decimals
        for f in ["total_amount", "subtotal", "tax_amount"]:
            if estimate.get(f) is not None:
                estimate[f] = float(estimate[f])
        
        # Parse items if string
        if estimate.get('items') and isinstance(estimate['items'], str):
            try:
                estimate['items'] = json.loads(estimate['items'])
            except:
                estimate['items'] = []

        return {
            "success": True,
            "data": estimate
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting estimate: {e}")
        raise HTTPException(status_code=500, detail="Failed to get estimate details")
