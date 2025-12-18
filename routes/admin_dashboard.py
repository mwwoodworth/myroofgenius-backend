"""
Admin dashboard Module - v163.0.26
Fixed to use app.state.db_pool for proper connection management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncpg
import uuid
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Database pool dependency - uses app state
async def get_db_pool(request: Request) -> asyncpg.Pool:
    """Get database pool from app state"""
    pool = getattr(request.app.state, 'db_pool', None)
    if pool is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    return pool

# Models
class AdminDashboardBase(BaseModel):
    name: str = Field(..., description="Name")
    description: Optional[str] = None
    status: str = "active"
    data: Optional[Dict[str, Any]] = {}

class AdminDashboardCreate(AdminDashboardBase):
    pass

class AdminDashboardResponse(AdminDashboardBase):
    id: str
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=AdminDashboardResponse)
async def create_admin_dashboard(
    request: Request,
    item: AdminDashboardCreate,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Create new admin dashboard record"""
    try:
        async with pool.acquire() as conn:
            query = """
                INSERT INTO admin_dashboard (name, description, status, data)
                VALUES ($1, $2, $3, $4)
                RETURNING id, created_at, updated_at
            """

            result = await conn.fetchrow(
                query, item.name, item.description, item.status,
                json.dumps(item.data) if item.data else None
            )

        return {
            **item.dict(),
            "id": str(result['id']),
            "created_at": result['created_at'],
            "updated_at": result['updated_at']
        }
    except Exception as e:
        logger.error(f"Error creating admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create record: {str(e)}")

@router.get("/", response_model=List[AdminDashboardResponse])
async def list_admin_dashboard(
    request: Request,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """List admin dashboard records"""
    try:
        query = "SELECT * FROM admin_dashboard WHERE 1=1"
        params = []
        param_count = 0

        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, skip])

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [
            {
                **dict(row),
                "id": str(row['id']),
                "data": json.loads(row['data']) if row['data'] else {}
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error listing admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list records: {str(e)}")

@router.get("/stats/summary")
async def get_admin_dashboard_stats(
    request: Request,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get admin dashboard statistics - comprehensive system overview"""
    try:
        async with pool.acquire() as conn:
            # Get overall system stats
            system_stats = await conn.fetchrow("""
                SELECT
                    (SELECT COUNT(*) FROM customers) as total_customers,
                    (SELECT COUNT(*) FROM jobs) as total_jobs,
                    (SELECT COUNT(*) FROM invoices) as total_invoices,
                    (SELECT COUNT(*) FROM tenants) as total_tenants,
                    (SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE status = 'paid' OR payment_status = 'paid') as total_revenue
            """)

            # Get recent activity
            recent_jobs = await conn.fetchval("""
                SELECT COUNT(*) FROM jobs
                WHERE created_at > CURRENT_DATE - INTERVAL '7 days'
            """)

            recent_customers = await conn.fetchval("""
                SELECT COUNT(*) FROM customers
                WHERE created_at > CURRENT_DATE - INTERVAL '7 days'
            """)

            # Get job status breakdown
            job_status = await conn.fetch("""
                SELECT status, COUNT(*) as count
                FROM jobs
                GROUP BY status
            """)

            # Get monthly revenue trend (last 6 months)
            monthly_revenue = await conn.fetch("""
                SELECT
                    DATE_TRUNC('month', created_at) as month,
                    COALESCE(SUM(total_amount), 0) as revenue
                FROM invoices
                WHERE created_at > CURRENT_DATE - INTERVAL '6 months'
                    AND (status = 'paid' OR payment_status = 'paid')
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month DESC
                LIMIT 6
            """)

        return {
            "success": True,
            "data": {
                "overview": {
                    "total_customers": system_stats['total_customers'] or 0,
                    "total_jobs": system_stats['total_jobs'] or 0,
                    "total_invoices": system_stats['total_invoices'] or 0,
                    "total_tenants": system_stats['total_tenants'] or 0,
                    "total_revenue": float(system_stats['total_revenue'] or 0)
                },
                "recent_activity": {
                    "jobs_last_7_days": recent_jobs or 0,
                    "customers_last_7_days": recent_customers or 0
                },
                "job_status_breakdown": {
                    row['status']: row['count'] for row in job_status
                },
                "monthly_revenue": [
                    {
                        "month": row['month'].isoformat() if row['month'] else None,
                        "revenue": float(row['revenue'] or 0)
                    }
                    for row in monthly_revenue
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/{item_id}", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    request: Request,
    item_id: str,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get specific admin dashboard record"""
    try:
        query = "SELECT * FROM admin_dashboard WHERE id = $1"

        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, uuid.UUID(item_id))

        if not row:
            raise HTTPException(status_code=404, detail="Admin dashboard not found")

        return {
            **dict(row),
            "id": str(row['id']),
            "data": json.loads(row['data']) if row['data'] else {}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get record: {str(e)}")

@router.put("/{item_id}")
async def update_admin_dashboard(
    request: Request,
    item_id: str,
    updates: Dict[str, Any],
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Update admin dashboard record"""
    try:
        if 'data' in updates:
            updates['data'] = json.dumps(updates['data'])

        set_clauses = []
        params = []
        for i, (field, value) in enumerate(updates.items(), 1):
            set_clauses.append(f"{field} = ${i}")
            params.append(value)

        params.append(uuid.UUID(item_id))
        query = f"""
            UPDATE admin_dashboard
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE id = ${len(params)}
            RETURNING id
        """

        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, *params)

        if not result:
            raise HTTPException(status_code=404, detail="Admin dashboard not found")

        return {"message": "Admin dashboard updated", "id": str(result['id'])}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update record: {str(e)}")

@router.delete("/{item_id}")
async def delete_admin_dashboard(
    request: Request,
    item_id: str,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Delete admin dashboard record"""
    try:
        query = "DELETE FROM admin_dashboard WHERE id = $1 RETURNING id"

        async with pool.acquire() as conn:
            result = await conn.fetchrow(query, uuid.UUID(item_id))

        if not result:
            raise HTTPException(status_code=404, detail="Admin dashboard not found")

        return {"message": "Admin dashboard deleted", "id": str(result['id'])}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete record: {str(e)}")
