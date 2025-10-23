"""
Jobs API Routes
Manages job tracking and operations
"""

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

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
    assigned_to: Optional[str] = None
):
    """List all jobs"""
    try:
        db_pool = request.app.state.db_pool

        query = """
            SELECT j.id, j.job_number, j.customer_id, j.title, j.description,
                   j.status, j.priority, j.assigned_to, j.scheduled_date,
                   j.completed_date, j.estimated_hours, j.actual_hours, j.created_at,
                   c.name as customer_name
            FROM jobs j
            LEFT JOIN customers c ON j.customer_id = c.id
            WHERE 1=1
        """

        params = []
        param_count = 0

        if status:
            param_count += 1
            query += f" AND j.status = ${param_count}"
            params.append(status)

        if customer_id:
            param_count += 1
            query += f" AND j.customer_id = ${param_count}"
            params.append(customer_id)

        if assigned_to:
            param_count += 1
            query += f" AND j.assigned_to = ${param_count}"
            params.append(assigned_to)

        param_count += 1
        query += f" ORDER BY j.created_at DESC LIMIT ${param_count}"
        params.append(limit)

        param_count += 1
        query += f" OFFSET ${param_count}"
        params.append(offset)

        async with db_pool.acquire() as conn:
            jobs = await conn.fetch(query, *params)

            # Get total count
            count_query = "SELECT COUNT(*) FROM jobs WHERE 1=1"
            count_params = []
            cp = 0

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
            if job_dict.get('estimated_hours'):
                job_dict['estimated_hours'] = float(job_dict['estimated_hours'])
            if job_dict.get('actual_hours'):
                job_dict['actual_hours'] = float(job_dict['actual_hours'])
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
        raise HTTPException(status_code=500, detail="Failed to list jobs")

@router.get("/{job_id}")
async def get_job(
    job_id: str,
    request: Request
):
    """Get job details"""
    try:
        db_pool = request.app.state.db_pool

        async with db_pool.acquire() as conn:
            job = await conn.fetchrow("""
                SELECT j.id, j.job_number, j.customer_id, j.title, j.description,
                       j.status, j.priority, j.assigned_to, j.scheduled_date,
                       j.completed_date, j.estimated_hours, j.actual_hours, j.created_at,
                       c.name as customer_name, c.email as customer_email
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.id
                WHERE j.id = $1::uuid
            """, job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_dict = dict(job)
        # Convert Decimal to float
        if job_dict.get('estimated_hours'):
            job_dict['estimated_hours'] = float(job_dict['estimated_hours'])
        if job_dict.get('actual_hours'):
            job_dict['actual_hours'] = float(job_dict['actual_hours'])

        return {
            "success": True,
            "data": job_dict
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job")

@router.get("/stats/summary")
async def get_job_stats(
    request: Request
):
    """Get job statistics"""
    try:
        db_pool = request.app.state.db_pool

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
            """)

            # Get average completion time
            avg_completion = await conn.fetchval("""
                SELECT AVG(EXTRACT(epoch FROM (completed_date - created_at))/86400) as avg_days
                FROM jobs
                WHERE completed_date IS NOT NULL
            """)

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
        raise HTTPException(status_code=500, detail="Failed to get job statistics")