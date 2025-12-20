"""
Service Catalog Module - Task 87
Service offerings and request management
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

router = APIRouter()

async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


class ServiceCreate(BaseModel):
    name: str
    description: str
    category: str
    price: Optional[float] = None
    delivery_time_days: Optional[int] = None
    requirements: Optional[List[str]] = []
    is_active: bool = True

class ServiceRequestCreate(BaseModel):
    service_id: str
    customer_id: str
    details: Optional[str] = None
    urgency: str = "normal"  # low, normal, high
    attachments: Optional[List[str]] = []

@router.post("/services", response_model=dict)
async def create_service(
    service: ServiceCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create service catalog item"""
    query = """
        INSERT INTO service_catalog (
            name, description, category, price,
            delivery_time_days, requirements, is_active
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        service.name,
        service.description,
        service.category,
        service.price,
        service.delivery_time_days,
        json.dumps(service.requirements),
        service.is_active
    )

    return {
        **dict(result),
        "id": str(result['id']),
        "requirements": json.loads(result.get('requirements', '[]'))
    }

@router.get("/services", response_model=List[dict])
async def list_services(
    category: Optional[str] = None,
    is_active: bool = True,
    conn: asyncpg.Connection = Depends(get_db)
):
    """List available services"""
    params = [is_active]
    category_clause = ""

    if category:
        params.append(category)
        category_clause = f" AND category = ${len(params)}"

    query = f"""
        SELECT * FROM service_catalog
        WHERE is_active = $1{category_clause}
        ORDER BY category, name
    """

    rows = await conn.fetch(query, *params)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "requirements": json.loads(row.get('requirements', '[]'))
        } for row in rows
    ]

@router.post("/requests", response_model=dict)
async def create_service_request(
    request: ServiceRequestCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create service request"""
    query = """
        INSERT INTO service_requests (
            service_id, customer_id, details, urgency, attachments, status
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(request.service_id),
        uuid.UUID(request.customer_id),
        request.details,
        request.urgency,
        json.dumps(request.attachments),
        'pending'
    )

    return {
        **dict(result),
        "id": str(result['id']),
        "request_number": f"REQ-{result['id'].hex[:8].upper()}"
    }

@router.get("/requests/{request_id}/status", response_model=dict)
async def get_request_status(
    request_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get service request status"""
    query = """
        SELECT
            sr.*,
            sc.name as service_name,
            sc.delivery_time_days
        FROM service_requests sr
        JOIN service_catalog sc ON sr.service_id = sc.id
        WHERE sr.id = $1
    """

    result = await conn.fetchrow(query, uuid.UUID(request_id))
    if not result:
        raise HTTPException(status_code=404, detail="Request not found")

    return {
        **dict(result),
        "id": str(result['id']),
        "estimated_completion": calculate_completion_date(result)
    }

def calculate_completion_date(request) -> Optional[datetime]:
    """Calculate estimated completion date"""
    if request['delivery_time_days'] and request['created_at']:
        from datetime import timedelta
        return request['created_at'] + timedelta(days=request['delivery_time_days'])
    return None
