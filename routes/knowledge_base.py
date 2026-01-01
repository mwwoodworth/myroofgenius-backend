"""
Knowledge Base Module - Task 82
Self-service knowledge base system
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


class ArticleCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: List[str] = []
    is_public: bool = True
    author: str

class ArticleResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    is_public: bool
    author: str
    views: int
    helpful_count: int
    created_at: datetime
    updated_at: datetime

@router.post("/articles", response_model=ArticleResponse)
async def create_article(
    article: ArticleCreate,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create knowledge base article"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    query = """
        INSERT INTO knowledge_base_articles (
            tenant_id, title, content, category, tags, is_public, author
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        tenant_id,
        article.title,
        article.content,
        article.category,
        json.dumps(article.tags),
        article.is_public,
        article.author
    )

    return format_article_response(result)

@router.get("/articles/search", response_model=List[ArticleResponse])
async def search_articles(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Search knowledge base articles"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    params = [tenant_id, f"%{q}%"]
    category_clause = ""

    if category:
        params.append(category)
        category_clause = f" AND category = ${len(params)}"

    query = f"""
        SELECT * FROM knowledge_base_articles
        WHERE tenant_id = $1 AND is_public = true
        AND (title ILIKE $2 OR content ILIKE $2){category_clause}
        ORDER BY views DESC, helpful_count DESC
        LIMIT 20
    """

    rows = await conn.fetch(query, *params)
    return [format_article_response(row) for row in rows]

@router.post("/articles/{article_id}/helpful")
async def mark_helpful(
    article_id: str,
    helpful: bool,
    conn: asyncpg.Connection = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Mark article as helpful/not helpful"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    if helpful:
        query = """
            UPDATE knowledge_base_articles
            SET helpful_count = helpful_count + 1
            WHERE id = $1 AND tenant_id = $2
            RETURNING helpful_count
        """
    else:
        query = """
            UPDATE knowledge_base_articles
            SET not_helpful_count = not_helpful_count + 1
            WHERE id = $1 AND tenant_id = $2
            RETURNING not_helpful_count
        """

    result = await conn.fetchrow(query, uuid.UUID(article_id), tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Article not found")

    return {"status": "updated", "article_id": article_id}

def format_article_response(row: dict) -> dict:
    return {
        **dict(row),
        "id": str(row['id']),
        "tags": json.loads(row.get('tags', '[]')),
        "views": row.get('views', 0),
        "helpful_count": row.get('helpful_count', 0)
    }
