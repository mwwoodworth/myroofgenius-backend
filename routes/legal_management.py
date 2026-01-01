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
from core.supabase_auth import get_authenticated_user

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
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List legal cases"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    query = """
        SELECT id, case_number, title, case_type, status,
               filing_date, next_hearing_date
        FROM legal_cases
        WHERE tenant_id = $1
        AND ($2::text IS NULL OR status = $2)
        AND ($3::text IS NULL OR case_type = $3)
        ORDER BY created_at DESC
    """
    rows = await db.fetch(query, tenant_id, status, case_type)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/cases")
async def create_legal_case(
    case_data: Dict[str, Any],
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Create legal case"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    case_id = str(uuid4())
    case_number = f"CASE-{datetime.now().strftime('%Y')}-{case_id[:8]}"

    query = """
        INSERT INTO legal_cases (id, tenant_id, case_number, title, case_type,
                                description, parties, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'open')
        RETURNING id, case_number
    """

    result = await db.fetchrow(
        query, case_id, tenant_id, case_number, case_data['title'],
        case_data.get('case_type', 'general'),
        case_data.get('description'),
        json.dumps(case_data.get('parties', []))
    )

    return dict(result)

@router.post("/cases/{case_id}/documents")
async def add_case_documents(
    case_id: str,
    document: Dict[str, Any],
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Add documents to case"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    # Verify case belongs to tenant
    case_check = await db.fetchrow(
        "SELECT id FROM legal_cases WHERE id = $1 AND tenant_id = $2",
        case_id, tenant_id
    )
    if not case_check:
        raise HTTPException(status_code=404, detail="Legal case not found")

    doc_id = str(uuid4())

    query = """
        INSERT INTO legal_documents (id, tenant_id, case_id, document_type,
                                    title, file_path, confidentiality)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
    """

    await db.execute(
        query, doc_id, tenant_id, case_id, document['document_type'],
        document['title'], document.get('file_path'),
        document.get('confidentiality', 'internal')
    )

    return {"document_id": doc_id, "status": "uploaded"}

@router.get("/intellectual-property")
async def list_ip_assets(
    db=Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """List intellectual property assets"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required")

    query = """
        SELECT id, ip_type, title, registration_number,
               filing_date, expiry_date, status
        FROM intellectual_property
        WHERE tenant_id = $1
        ORDER BY filing_date DESC
    """
    rows = await db.fetch(query, tenant_id)
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
