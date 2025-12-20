"""
Task 106: Legal Management
Legal case management and documentation
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks, Request
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
import asyncpg
import json
import asyncio
from decimal import Decimal

router = APIRouter()

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


@router.get("/cases")
async def list_legal_cases(
    status: Optional[str] = None,
    case_type: Optional[str] = None,
    db=Depends(get_db)
):
    """List legal cases"""
    query = """
        SELECT id, case_number, title, case_type, status,
               filing_date, next_hearing_date
        FROM legal_cases
        WHERE ($1::text IS NULL OR status = $1)
        AND ($2::text IS NULL OR case_type = $2)
        ORDER BY created_at DESC
    """
    rows = await db.fetch(query, status, case_type)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/cases")
async def create_legal_case(
    case_data: Dict[str, Any],
    db=Depends(get_db)
):
    """Create legal case"""
    case_id = str(uuid4())
    case_number = f"CASE-{datetime.now().strftime('%Y')}-{case_id[:8]}"

    query = """
        INSERT INTO legal_cases (id, case_number, title, case_type,
                                description, parties, status)
        VALUES ($1, $2, $3, $4, $5, $6, 'open')
        RETURNING id, case_number
    """

    result = await db.fetchrow(
        query, case_id, case_number, case_data['title'],
        case_data.get('case_type', 'general'),
        case_data.get('description'),
        json.dumps(case_data.get('parties', []))
    )

    return dict(result)

@router.post("/cases/{case_id}/documents")
async def add_case_documents(
    case_id: str,
    document: Dict[str, Any],
    db=Depends(get_db)
):
    """Add documents to case"""
    doc_id = str(uuid4())

    query = """
        INSERT INTO legal_documents (id, case_id, document_type,
                                    title, file_path, confidentiality)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
    """

    await db.execute(
        query, doc_id, case_id, document['document_type'],
        document['title'], document.get('file_path'),
        document.get('confidentiality', 'internal')
    )

    return {"document_id": doc_id, "status": "uploaded"}

@router.get("/intellectual-property")
async def list_ip_assets(db=Depends(get_db)):
    """List intellectual property assets"""
    query = """
        SELECT id, ip_type, title, registration_number,
               filing_date, expiry_date, status
        FROM intellectual_property
        ORDER BY filing_date DESC
    """
    rows = await db.fetch(query)
    if not rows:
        return []

    return {
        "total_assets": len(rows),
        "assets": [dict(row) for row in rows],
        "by_type": {
            "patents": len([r for r in rows if r['ip_type'] == 'patent']),
            "trademarks": len([r for r in rows if r['ip_type'] == 'trademark']),
            "copyrights": len([r for r in rows if r['ip_type'] == 'copyright'])
        }
    }
