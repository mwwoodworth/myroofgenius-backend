"""
Employees API Routes
Provides basic employee directory access with graceful degradation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, Optional
import logging

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/employees", tags=["Employees"])

@router.get("")
@router.get("/")
async def list_employees(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List employees for the authenticated tenant."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        query = """
            SELECT id, first_name, last_name, email, phone,
                   position, status, created_at
            FROM employees
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

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM employees WHERE tenant_id = $1",
                tenant_id
            )

        employees = []
        for row in rows:
            record = dict(row)
            record["id"] = str(record.get("id"))
            employees.append(record)

        return {
            "success": True,
            "data": employees,
            "total": count or 0,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing employees: {e}")
        raise HTTPException(status_code=500, detail="Failed to list employees")


@router.get("/{employee_id}")
async def get_employee(
    employee_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Retrieve an employee profile."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, first_name, last_name, email, phone,
                       position, status, created_at, updated_at
                FROM employees
                WHERE id = $1::uuid AND tenant_id = $2
                """,
                employee_id,
                tenant_id
            )

        if not row:
            raise HTTPException(status_code=404, detail="Employee not found")

        record = dict(row)
        record["id"] = str(record.get("id"))

        return {
            "success": True,
            "data": record
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving employee {employee_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve employee")
