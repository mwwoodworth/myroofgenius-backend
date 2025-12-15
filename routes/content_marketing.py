"""
Content Marketing Module - Task 75
Content creation and distribution management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection
async def get_db():
    conn = await asyncpg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        user="postgres.yomagoqdmxszqtdwuhab",
        password="<DB_PASSWORD_REDACTED>",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

# Models
class ContentCreate(BaseModel):
    title: str
    content_type: str = "blog"  # blog, video, infographic, whitepaper, case_study
    content_body: str
    author: str
    tags: List[str] = []
    seo_keywords: Optional[List[str]] = []
    publish_date: Optional[datetime] = None
    status: str = "draft"

# Endpoints
@router.post("/", response_model=dict)
async def create_content(
    content: ContentCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create content piece"""
    query = """
        INSERT INTO content_marketing (
            title, content_type, content_body, author,
            tags, seo_keywords, publish_date, status
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        content.title,
        content.content_type,
        content.content_body,
        content.author,
        json.dumps(content.tags),
        json.dumps(content.seo_keywords),
        content.publish_date,
        content.status
    )

    return {**dict(result), "id": str(result['id'])}

@router.get("/calendar", response_model=List[dict])
async def get_content_calendar(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2024, le=2030),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get content calendar"""
    query = """
        SELECT * FROM content_marketing
        WHERE EXTRACT(MONTH FROM publish_date) = $1
        AND EXTRACT(YEAR FROM publish_date) = $2
        ORDER BY publish_date
    """

    rows = await conn.fetch(query, month, year)
    return [{**dict(row), "id": str(row['id'])} for row in rows]
