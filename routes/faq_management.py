"""
FAQ Management Module - Task 88
Frequently asked questions system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json
from core.supabase_auth import get_authenticated_user

router = APIRouter()

async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str
    tags: List[str] = []
    order_index: Optional[int] = 0
    is_published: bool = True

@router.post("/", response_model=dict)
async def create_faq(
    faq: FAQCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create FAQ entry"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    query = """
        INSERT INTO faqs (
            tenant_id, question, answer, category, tags,
            order_index, is_published
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        tenant_id,
        faq.question,
        faq.answer,
        faq.category,
        json.dumps(faq.tags),
        faq.order_index,
        faq.is_published
    )

    return {
        **dict(result),
        "id": str(result['id']),
        "tags": json.loads(result.get('tags', '[]'))
    }

@router.get("/", response_model=List[dict])
async def list_faqs(
    category: Optional[str] = None,
    search: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List FAQs"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    params = [tenant_id]
    conditions = ["tenant_id = $1", "is_published = true"]

    if category:
        params.append(category)
        conditions.append(f"category = ${len(params)}")

    if search:
        params.append(f"%{search}%")
        conditions.append(f"(question ILIKE ${len(params)} OR answer ILIKE ${len(params)})")

    where_clause = " WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT * FROM faqs
        {where_clause}
        ORDER BY category, order_index, question
    """

    rows = await conn.fetch(query, *params)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "tags": json.loads(row.get('tags', '[]')),
            "views": row.get('views', 0)
        } for row in rows
    ]

@router.get("/categories", response_model=List[dict])
async def get_faq_categories(
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get FAQ categories with counts"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    query = """
        SELECT
            category,
            COUNT(*) as count
        FROM faqs
        WHERE tenant_id = $1 AND is_published = true
        GROUP BY category
        ORDER BY category
    """

    rows = await conn.fetch(query, tenant_id)
    return [dict(row) for row in rows]

@router.post("/{faq_id}/view")
async def track_faq_view(
    faq_id: str,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Track FAQ view"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    query = """
        UPDATE faqs
        SET views = COALESCE(views, 0) + 1
        WHERE id = $1 AND tenant_id = $2
        RETURNING views
    """

    result = await conn.fetchrow(query, uuid.UUID(faq_id), tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="FAQ not found")

    return {"views": result['views']}
