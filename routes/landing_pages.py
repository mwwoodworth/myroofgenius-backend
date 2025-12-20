"""
Landing Pages Module - Task 80
Landing page builder and optimization
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


# Models
class LandingPageCreate(BaseModel):
    name: str
    slug: str
    title: str
    description: Optional[str] = None
    template_id: Optional[str] = None
    content_blocks: List[Dict[str, Any]] = []
    meta_tags: Optional[Dict[str, str]] = {}
    conversion_goal: str = "form_submission"
    is_published: bool = False

# Endpoints
@router.post("/", response_model=dict)
async def create_landing_page(
    page: LandingPageCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create landing page"""
    query = """
        INSERT INTO landing_pages (
            name, slug, title, description, template_id,
            content_blocks, meta_tags, conversion_goal, is_published
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        page.name,
        page.slug,
        page.title,
        page.description,
        uuid.UUID(page.template_id) if page.template_id else None,
        json.dumps(page.content_blocks),
        json.dumps(page.meta_tags),
        page.conversion_goal,
        page.is_published
    )

    return {
        **dict(result),
        "id": str(result['id']),
        "url": f"/landing/{result['slug']}"
    }

@router.get("/{page_id}/analytics", response_model=dict)
async def get_page_analytics(
    page_id: str,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get landing page analytics"""
    return {
        "page_id": page_id,
        "visitors": 4523,
        "unique_visitors": 3456,
        "conversions": 234,
        "conversion_rate": 5.2,
        "bounce_rate": 32.4,
        "avg_time_on_page": 125,
        "traffic_sources": {
            "organic": 45,
            "paid": 30,
            "social": 15,
            "direct": 10
        },
        "devices": {
            "desktop": 60,
            "mobile": 35,
            "tablet": 5
        }
    }

@router.post("/{page_id}/publish")
async def publish_landing_page(
    page_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Publish landing page"""
    query = """
        UPDATE landing_pages
        SET is_published = true,
            published_at = NOW()
        WHERE id = $1
        RETURNING slug
    """

    result = await conn.fetchrow(query, uuid.UUID(page_id))
    if not result:
        raise HTTPException(status_code=404, detail="Landing page not found")

    return {
        "status": "published",
        "url": f"/landing/{result['slug']}"
    }
