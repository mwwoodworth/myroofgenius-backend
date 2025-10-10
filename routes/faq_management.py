"""
FAQ Management Module - Task 88
Frequently asked questions system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

router = APIRouter()

async def get_db():
    conn = await asyncpg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        user="postgres.yomagoqdmxszqtdwuhab",
        password="Brain0ps2O2S",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

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
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create FAQ entry"""
    query = """
        INSERT INTO faqs (
            question, answer, category, tags,
            order_index, is_published
        ) VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
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
    conn: asyncpg.Connection = Depends(get_db)
):
    """List FAQs"""
    params = []
    conditions = ["is_published = true"]

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
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get FAQ categories with counts"""
    query = """
        SELECT
            category,
            COUNT(*) as count
        FROM faqs
        WHERE is_published = true
        GROUP BY category
        ORDER BY category
    """

    rows = await conn.fetch(query)
    return [dict(row) for row in rows]

@router.post("/{faq_id}/view")
async def track_faq_view(
    faq_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Track FAQ view"""
    query = """
        UPDATE faqs
        SET views = COALESCE(views, 0) + 1
        WHERE id = $1
        RETURNING views
    """

    result = await conn.fetchrow(query, uuid.UUID(faq_id))
    if not result:
        raise HTTPException(status_code=404, detail="FAQ not found")

    return {"views": result['views']}
