"""
Task 105: Compliance Tracking
Regulatory compliance and audit management
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
        password="Brain0ps2O2S",
        database="postgres"
    )
    try:
        yield conn
    finally:
        await conn.close()

@router.get("/requirements")
async def list_compliance_requirements(
    regulation: Optional[str] = None,
    status: Optional[str] = None,
    db=Depends(get_db)
):
    """List compliance requirements"""
    query = """
        SELECT id, regulation, requirement_name, description,
               compliance_status, due_date
        FROM compliance_requirements
        WHERE ($1::text IS NULL OR regulation = $1)
        AND ($2::text IS NULL OR compliance_status = $2)
        ORDER BY due_date
    """
    rows = await db.fetch(query, regulation, status)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/audits")
async def schedule_audit(
    audit_data: Dict[str, Any],
    db=Depends(get_db)
):
    """Schedule compliance audit"""
    audit_id = str(uuid4())

    query = """
        INSERT INTO compliance_audits (id, audit_type, scope,
                                      scheduled_date, auditor, status)
        VALUES ($1, $2, $3, $4, $5, 'scheduled')
        RETURNING id
    """

    await db.execute(
        query, audit_id, audit_data['audit_type'],
        json.dumps(audit_data.get('scope', [])),
        audit_data['scheduled_date'],
        audit_data.get('auditor')
    )

    return {"audit_id": audit_id, "status": "scheduled"}

@router.post("/audits/{audit_id}/findings")
async def add_audit_findings(
    audit_id: str,
    findings: Dict[str, Any],
    db=Depends(get_db)
):
    """Add findings to an audit"""
    finding_id = str(uuid4())

    query = """
        INSERT INTO audit_findings (id, audit_id, finding_type,
                                   severity, description, recommendation)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
    """

    await db.execute(
        query, finding_id, audit_id,
        findings['finding_type'], findings.get('severity', 'medium'),
        findings['description'], findings.get('recommendation')
    )

    return {"finding_id": finding_id, "status": "added"}

@router.get("/dashboard")
async def compliance_dashboard(db=Depends(get_db)):
    """Get compliance status dashboard"""

    # Get compliance by regulation
    reg_query = """
        SELECT regulation, COUNT(*) as total,
               SUM(CASE WHEN compliance_status = 'compliant' THEN 1 ELSE 0 END) as compliant,
               SUM(CASE WHEN compliance_status = 'non-compliant' THEN 1 ELSE 0 END) as non_compliant
        FROM compliance_requirements
        GROUP BY regulation
    """
    regulations = await db.fetch(reg_query)

    # Get upcoming audits
    audit_query = """
        SELECT id, audit_type, scheduled_date
        FROM compliance_audits
        WHERE scheduled_date >= CURRENT_DATE
        AND status = 'scheduled'
        ORDER BY scheduled_date
        LIMIT 5
    """
    audits = await db.fetch(audit_query)

    # Get recent violations
    violation_query = """
        SELECT id, violation_type, severity, reported_date
        FROM compliance_violations
        WHERE status = 'open'
        ORDER BY reported_date DESC
        LIMIT 5
    """
    violations = await db.fetch(violation_query)

    return {
        "regulations": [dict(row) for row in regulations],
        "upcoming_audits": [dict(row) for row in audits],
        "recent_violations": [dict(row) for row in violations],
        "overall_compliance_rate": 85.5  # Would calculate from actual data
    }
