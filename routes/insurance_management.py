"""
Task 107: Insurance Management
Policy management and claims processing
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
import asyncpg
import json
import asyncio
from decimal import Decimal

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

@router.get("/policies")
async def list_insurance_policies(
    policy_type: Optional[str] = None,
    status: Optional[str] = None,
    db=Depends(get_db)
):
    """List insurance policies"""
    query = """
        SELECT id, policy_number, policy_type, insurer, coverage_amount,
               premium, start_date, end_date, status
        FROM insurance_policies
        WHERE ($1::text IS NULL OR policy_type = $1)
        AND ($2::text IS NULL OR status = $2)
        ORDER BY end_date
    """
    rows = await db.fetch(query, policy_type, status)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/claims")
async def file_insurance_claim(
    claim_data: Dict[str, Any],
    db=Depends(get_db)
):
    """File insurance claim"""
    claim_id = str(uuid4())
    claim_number = f"CLM-{datetime.now().strftime('%Y%m%d')}-{claim_id[:8]}"

    query = """
        INSERT INTO insurance_claims (id, claim_number, policy_id,
                                     claim_type, incident_date, claim_amount,
                                     description, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'submitted')
        RETURNING id, claim_number
    """

    result = await db.fetchrow(
        query, claim_id, claim_number, claim_data['policy_id'],
        claim_data.get('claim_type', 'general'),
        claim_data['incident_date'], claim_data['claim_amount'],
        claim_data.get('description')
    )

    return dict(result)

@router.get("/coverage")
async def analyze_coverage(db=Depends(get_db)):
    """Analyze insurance coverage"""
    query = """
        SELECT
            policy_type,
            COUNT(*) as policy_count,
            SUM(coverage_amount) as total_coverage,
            SUM(premium) as total_premium
        FROM insurance_policies
        WHERE status = 'active'
        GROUP BY policy_type
    """
    rows = await db.fetch(query)
    if not rows:
        return []

    # Get claims summary
    claims_query = """
        SELECT
            COUNT(*) as total_claims,
            SUM(claim_amount) as total_claimed,
            SUM(CASE WHEN status = 'approved' THEN claim_amount ELSE 0 END) as approved_amount,
            AVG(claim_amount) as avg_claim
        FROM insurance_claims
        WHERE incident_date >= CURRENT_DATE - INTERVAL '1 year'
    """
    claims = await db.fetchrow(claims_query)

    return {
        "coverage_by_type": [dict(row) for row in rows],
        "total_coverage": sum(float(row['total_coverage'] or 0) for row in rows),
        "annual_premium": sum(float(row['total_premium'] or 0) for row in rows),
        "claims_summary": dict(claims) if claims else {},
        "loss_ratio": 0.65  # Would calculate from actual data
    }
