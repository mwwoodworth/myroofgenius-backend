"""
Proposal Generation Module - Task 65
Complete proposal creation and management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
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
class ProposalCreate(BaseModel):
    proposal_title: str
    opportunity_id: Optional[str] = None
    quote_id: Optional[str] = None
    customer_id: Optional[str] = None
    template_id: Optional[str] = None
    executive_summary: str
    problem_statement: str
    proposed_solution: str
    scope_of_work: str
    deliverables: List[str]
    timeline: str
    investment_summary: str
    valid_until: date
    prepared_by: str

class ProposalResponse(BaseModel):
    id: str
    proposal_number: str
    proposal_title: str
    status: str
    executive_summary: str
    valid_until: Optional[date]
    prepared_by: str
    version: int
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=ProposalResponse)
async def create_proposal(
    proposal: ProposalCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new proposal"""
    # Generate proposal number
    count = await conn.fetchval("SELECT COUNT(*) FROM proposals")
    proposal_number = f"P-{datetime.utcnow().year}-{(count or 0) + 1:05d}"

    query = """
        INSERT INTO proposals (
            proposal_number, proposal_title, opportunity_id, quote_id,
            customer_id, template_id, status, executive_summary,
            problem_statement, proposed_solution, scope_of_work,
            deliverables, timeline, investment_summary, valid_until,
            prepared_by, version
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
            $13, $14, $15, $16, $17
        ) RETURNING *
    """

    result = await conn.fetchrow(
        query,
        proposal_number,
        proposal.proposal_title,
        uuid.UUID(proposal.opportunity_id) if proposal.opportunity_id else None,
        uuid.UUID(proposal.quote_id) if proposal.quote_id else None,
        uuid.UUID(proposal.customer_id) if proposal.customer_id else None,
        uuid.UUID(proposal.template_id) if proposal.template_id else None,
        'draft',
        proposal.executive_summary,
        proposal.problem_statement,
        proposal.proposed_solution,
        proposal.scope_of_work,
        proposal.deliverables,
        proposal.timeline,
        proposal.investment_summary,
        proposal.valid_until,
        proposal.prepared_by,
        1
    )

    return {
        **dict(result),
        "id": str(result['id'])
    }

@router.get("/", response_model=List[ProposalResponse])
async def list_proposals(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List proposals with filters"""
    conditions = []
    params = []

    if status:
        params.append(status)
        conditions.append(f"status = ${len(params)}")

    if customer_id:
        params.append(uuid.UUID(customer_id))
        conditions.append(f"customer_id = ${len(params)}")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, skip])

    query = f"""
        SELECT * FROM proposals
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [{**dict(row), "id": str(row['id'])} for row in rows]
