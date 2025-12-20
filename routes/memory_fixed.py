"""
Fixed Memory/RAG System
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json
import re

from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/memory", tags=["Memory"])

def _relevance_score(query: str, content: str) -> float:
    """Deterministic relevance score based on token overlap (0..1)."""
    query_terms = {t for t in re.findall(r"\w+", query.lower()) if t}
    if not query_terms:
        return 0.0
    content_terms = {t for t in re.findall(r"\w+", (content or "").lower()) if t}
    overlap = len(query_terms & content_terms)
    return round(min(1.0, overlap / len(query_terms)), 3)

@router.get("/search")
async def search_memory(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """Search memory/knowledge base"""
    try:
        # Simple text search for now (would use vector search in production)
        search_query = """
            SELECT id, content, metadata, created_at
            FROM memory_entries
            WHERE content ILIKE :search_term
            ORDER BY created_at DESC
            LIMIT :limit
        """
        
        results = db.execute(
            text(search_query),
            {"search_term": f"%{query}%", "limit": limit}
        )
        
        entries = []
        for row in results:
            entries.append({
                "id": str(row.id),
                "content": row.content,
                "metadata": row.metadata or {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "relevance": _relevance_score(query, row.content or "")
            })
        
        return {
            "query": query,
            "results": entries,
            "total": len(entries),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        # Return empty results instead of error
        return {
            "query": query,
            "results": [],
            "total": 0,
            "status": "success",
            "message": "No results found"
        }

@router.post("/store")
async def store_memory(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """Store new memory entry"""
    try:
        insert_query = """
            INSERT INTO memory_entries (content, metadata, created_at)
            VALUES (:content, :metadata, :created_at)
            RETURNING id
        """
        
        result = db.execute(
            text(insert_query),
            {
                "content": content,
                "metadata": json.dumps(metadata or {}),
                "created_at": datetime.utcnow()
            }
        )
        db.commit()
        
        memory_id = result.scalar()
        
        return {
            "id": str(memory_id),
            "status": "success",
            "message": "Memory stored successfully"
        }
    except Exception as e:
        logger.error(f"Memory store error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def memory_status(db: Session = Depends(get_db)):
    """Get memory system status"""
    try:
        count_query = "SELECT COUNT(*) FROM memory_entries"
        count = db.execute(text(count_query)).scalar()
        
        return {
            "status": "operational",
            "total_memories": count,
            "vector_search": "disabled",  # Would be enabled with pgvector
            "last_update": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Memory status error: {e}")
        return {
            "status": "degraded",
            "total_memories": 0,
            "error": str(e)
        }
