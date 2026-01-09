"""
Jobs API Routes
Manages job tracking and operations
"""

from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import logging
from uuid import UUID, uuid4

from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

def _parse_uuid(value: Any, field: str) -> UUID:
    try:
        return UUID(str(value))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field}") from exc


def _parse_job_category(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"service", "construction"}:
        return raw
    if not raw:
        return "service"
    raise HTTPException(status_code=400, detail="Invalid job_category (expected 'service' or 'construction')")

class Job(BaseModel):
    """Job model"""
    id: str
    job_number: Optional[str] = None
    customer_id: str
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    assigned_to: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    created_at: Optional[datetime] = None

@router.get("")
@router.get("/")  # Handle both with and without trailing slash
async def list_jobs(
    request: Request,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List all jobs for the authenticated tenant"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        query = """
            SELECT j.id, j.job_number, j.customer_id, j.title, j.description,
                   j.status, j.priority, j.job_type, j.assigned_to, j.tags,
                   j.scheduled_date, j.scheduled_start, j.scheduled_end,
                   j.completed_date, j.address, j.city, j.state,
                   COALESCE(j.service_zip, j.job_zip, j.zip) as zip_code,
                   j.estimated_hours, j.actual_hours, j.estimated_cost, 
                   j.total_amount, j.paid_amount, j.created_at,
                   c.name as customer_name
            FROM jobs j
            LEFT JOIN customers c ON j.customer_id = c.id
            WHERE j.tenant_id = $1
        """

        params = [tenant_id]
        param_count = 0

        if status:
            param_count += 1
            query += f" AND j.status = ${param_count + 1}"
            params.append(status)

        if customer_id:
            param_count += 1
            query += f" AND j.customer_id = ${param_count + 1}"
            params.append(customer_id)

        if assigned_to:
            param_count += 1
            query += f" AND j.assigned_to = ${param_count + 1}"
            params.append(assigned_to)

        query += " ORDER BY j.created_at DESC LIMIT ${} OFFSET ${}".format(param_count + 2, param_count + 3)
        params.extend([limit, offset])

        async with db_pool.acquire() as conn:
            jobs = await conn.fetch(query, *params)

            # Get total count
            count_query = "SELECT COUNT(*) FROM jobs WHERE tenant_id = $1"
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

            if assigned_to:
                cp += 1
                count_query += f" AND assigned_to = ${cp}"
                count_params.append(assigned_to)

            total = await conn.fetchval(count_query, *count_params) if count_params else await conn.fetchval(count_query)

        # Convert to list of dicts
        result = []
        for job in jobs:
            job_dict = dict(job)
            # Convert Decimal to float for JSON serialization
            for field in ['estimated_hours', 'actual_hours', 'estimated_cost', 'total_amount', 'paid_amount']:
                value = job_dict.get(field)
                if value is not None:
                    job_dict[field] = float(value)
            result.append(job_dict)

        return {
            "success": True,
            "data": result,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to list jobs")

@router.post("")
@router.post("/")  # Handle both with and without trailing slash
async def create_job(
    request: Request,
    job: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Create a job for the authenticated tenant."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id_raw = current_user.get("tenant_id")

        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")

        customer_id = job.get("customer_id") or None
        customer_uuid = _parse_uuid(customer_id, "customer_id") if customer_id else None

        title = (job.get("title") or job.get("name") or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Job title is required")

        description = job.get("description") or None
        status = (job.get("status") or "pending").strip() or "pending"
        priority = (job.get("priority") or "MEDIUM").strip() or "MEDIUM"
        job_type = job.get("job_type") or job.get("type") or None

        job_category = _parse_job_category(job.get("job_category"))

        job_id = uuid4()

        created_by: Optional[UUID] = None
        try:
            created_by = _parse_uuid(current_user.get("id"), "user_id")
        except Exception:
            created_by = None

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                org_id = await conn.fetchval(
                    "SELECT org_id FROM jobs WHERE tenant_id = $1 LIMIT 1",
                    tenant_id,
                )
                if not org_id:
                    org_id = UUID("00000000-0000-0000-0000-000000000001")

                row = await conn.fetchrow(
                    """
                    INSERT INTO jobs (
                        id,
                        tenant_id,
                        org_id,
                        job_category,
                        customer_id,
                        title,
                        description,
                        status,
                        priority,
                        job_type,
                        created_by,
                        created_at,
                        updated_at
                    ) VALUES (
                        $1, $2, $3, $4,
                        $5, $6, $7,
                        $8, $9, $10,
                        $11,
                        NOW(), NOW()
                    )
                    RETURNING id::text AS id, job_number
                    """,
                    job_id,
                    tenant_id,
                    org_id,
                    job_category,
                    customer_uuid,
                    title,
                    description,
                    status,
                    priority,
                    job_type,
                    created_by,
                )

        row_data = dict(row) if row else {}
        return {"success": True, "data": {"id": row_data.get("id", str(job_id)), "job_number": row_data.get("job_number")}}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error creating job: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create job")


@router.put("/{job_id}")
async def update_job(
    job_id: str,
    request: Request,
    job: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Update a job for the authenticated tenant."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id_raw = current_user.get("tenant_id")

        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        job_uuid = _parse_uuid(job_id, "job_id")

        update_fields: Dict[str, Any] = {}

        if "title" in job or "name" in job:
            title = (job.get("title") or job.get("name") or "").strip()
            if title:
                update_fields["title"] = title
        if "description" in job:
            update_fields["description"] = job.get("description")
        if "status" in job:
            update_fields["status"] = (job.get("status") or "").strip()
        if "priority" in job:
            update_fields["priority"] = (job.get("priority") or "").strip()
        if "assigned_to" in job:
            update_fields["assigned_to"] = job.get("assigned_to")
        if "job_type" in job or "type" in job:
            update_fields["job_type"] = job.get("job_type") or job.get("type")
        if "job_category" in job:
            update_fields["job_category"] = _parse_job_category(job.get("job_category"))
        if "customer_id" in job:
            update_fields["customer_id"] = _parse_uuid(job.get("customer_id"), "customer_id")

        if "scheduled_date" in job:
            update_fields["scheduled_date"] = job.get("scheduled_date")
        if "scheduled_start" in job:
            update_fields["scheduled_start"] = job.get("scheduled_start")
        if "scheduled_end" in job:
            update_fields["scheduled_end"] = job.get("scheduled_end")
        if "completed_date" in job:
            update_fields["completed_date"] = job.get("completed_date")

        if "total_amount" in job:
            update_fields["total_amount"] = job.get("total_amount")
        if "paid_amount" in job:
            update_fields["paid_amount"] = job.get("paid_amount")

        # Strip None/empty strings to avoid blanking fields unexpectedly.
        cleaned = {k: v for k, v in update_fields.items() if v is not None and v != ""}
        if not cleaned:
            raise HTTPException(status_code=400, detail="No updatable fields provided")

        set_clauses = []
        values: list[Any] = []
        idx = 1
        for key, value in cleaned.items():
            set_clauses.append(f"{key} = ${idx}")
            values.append(value)
            idx += 1
        set_clauses.append("updated_at = NOW()")

        values.extend([job_uuid, tenant_id])

        query = f"""
            UPDATE jobs
            SET {", ".join(set_clauses)}
            WHERE id = ${idx} AND tenant_id = ${idx + 1}
            RETURNING id::text AS id
        """

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)

        if not row:
            raise HTTPException(status_code=404, detail="Job not found")

        return {"success": True, "data": {"id": row["id"]}}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error updating job: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update job")


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    """Soft-delete a job (archive) for the authenticated tenant."""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id_raw = current_user.get("tenant_id")

        if not tenant_id_raw:
            raise HTTPException(status_code=403, detail="Tenant assignment required")
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        tenant_id = _parse_uuid(tenant_id_raw, "tenant_id")
        job_uuid = _parse_uuid(job_id, "job_id")

        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE jobs
                SET archived = TRUE,
                    updated_at = NOW()
                WHERE id = $1 AND tenant_id = $2
                RETURNING id::text AS id
                """,
                job_uuid,
                tenant_id,
            )

        if not row:
            raise HTTPException(status_code=404, detail="Job not found")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error deleting job: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete job")

@router.get("/{job_id}")
async def get_job(
    job_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get job details for the authenticated tenant"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with db_pool.acquire() as conn:
            job = await conn.fetchrow("""
                SELECT j.id, j.job_number, j.customer_id, j.title, j.description,
                       j.status, j.priority, j.job_type, j.assigned_to, j.tags,
                       j.scheduled_date, j.scheduled_start, j.scheduled_end,
                       j.completed_date, j.address, j.city, j.state,
                       COALESCE(j.service_zip, j.job_zip, j.zip) as zip_code,
                       j.estimated_hours, j.actual_hours, j.estimated_cost,
                       j.total_amount, j.paid_amount, j.created_at, j.custom_fields,
                       c.name as customer_name, c.email as customer_email, 
                       c.phone as customer_phone
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.id
                WHERE j.id = $1::uuid AND j.tenant_id = $2
            """, job_id, tenant_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_dict = dict(job)
        # Convert Decimal to float
        for field in ['estimated_hours', 'actual_hours', 'estimated_cost', 'total_amount', 'paid_amount']:
            if job_dict.get(field):
                job_dict[field] = float(job_dict[field])

        return {
            "success": True,
            "data": job_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job details")

@router.get("/stats/summary")
async def get_job_stats(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get job statistics for the authenticated tenant"""
    try:
        db_pool = getattr(request.app.state, "db_pool", None)
        tenant_id = current_user.get("tenant_id")

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        if not db_pool:
            raise HTTPException(status_code=503, detail="Database unavailable")

        async with db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled,
                    COUNT(*) FILTER (WHERE priority = 'high') as high_priority,
                    COUNT(*) FILTER (WHERE priority = 'medium') as medium_priority,
                    COUNT(*) FILTER (WHERE priority = 'low') as low_priority
                FROM jobs
                WHERE tenant_id = $1
            """, tenant_id)

            # Get average completion time
            avg_completion = await conn.fetchval("""
                SELECT AVG(EXTRACT(epoch FROM (completed_date - created_at))/86400) as avg_days
                FROM jobs
                WHERE completed_date IS NOT NULL AND tenant_id = $1
            """, tenant_id)

        return {
            "success": True,
            "data": {
                "total_jobs": stats['total_jobs'],
                "by_status": {
                    "pending": stats['pending'],
                    "in_progress": stats['in_progress'],
                    "completed": stats['completed'],
                    "cancelled": stats['cancelled']
                },
                "by_priority": {
                    "high": stats['high_priority'],
                    "medium": stats['medium_priority'],
                    "low": stats['low_priority']
                },
                "average_completion_days": float(avg_completion) if avg_completion else 0
            }
        }

    except Exception as e:
        logger.error(f"Error getting job stats: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to get job statistics")
