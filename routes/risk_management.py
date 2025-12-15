"""
Task 104: Risk Management
Risk assessment, mitigation, and monitoring
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

@router.get("/")
async def list_risks(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    db=Depends(get_db)
):
    """List identified risks"""
    query = """
        SELECT id, risk_title, category, severity, likelihood,
               impact_score, risk_score, status
        FROM risks
        WHERE ($1::text IS NULL OR category = $1)
        AND ($2::text IS NULL OR severity = $2)
        ORDER BY risk_score DESC
    """
    rows = await db.fetch(query, category, severity)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/")
async def create_risk_assessment(
    risk_data: Dict[str, Any],
    db=Depends(get_db)
):
    """Create risk assessment"""
    risk_id = str(uuid4())

    # Calculate risk score
    likelihood = risk_data.get('likelihood', 3)
    impact = risk_data.get('impact', 3)
    risk_score = likelihood * impact

    query = """
        INSERT INTO risks (id, risk_title, description, category,
                         likelihood, impact_score, risk_score, severity)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id, risk_score
    """

    # Determine severity based on risk score
    severity = 'critical' if risk_score >= 20 else 'high' if risk_score >= 12 else 'medium' if risk_score >= 6 else 'low'

    result = await db.fetchrow(
        query, risk_id, risk_data['risk_title'],
        risk_data.get('description'), risk_data.get('category', 'operational'),
        likelihood, impact, risk_score, severity
    )

    return dict(result)

@router.get("/matrix")
async def risk_matrix(db=Depends(get_db)):
    """Get risk matrix visualization data"""
    query = """
        SELECT
            likelihood,
            impact_score,
            COUNT(*) as risk_count,
            ARRAY_AGG(risk_title) as risks
        FROM risks
        WHERE status = 'active'
        GROUP BY likelihood, impact_score
    """
    rows = await db.fetch(query)
    if not rows:
        return []

    # Build 5x5 matrix
    matrix = [[0 for _ in range(5)] for _ in range(5)]
    risk_details = {}

    for row in rows:
        l = min(max(int(row['likelihood']) - 1, 0), 4)
        i = min(max(int(row['impact_score']) - 1, 0), 4)
        matrix[l][i] = row['risk_count']
        risk_details[f"{l}_{i}"] = row['risks']

    return {
        "matrix": matrix,
        "details": risk_details,
        "legend": {
            "likelihood": ["Very Low", "Low", "Medium", "High", "Very High"],
            "impact": ["Negligible", "Minor", "Moderate", "Major", "Severe"]
        }
    }

@router.put("/{risk_id}/mitigate")
async def add_mitigation_plan(
    risk_id: str,
    mitigation: Dict[str, Any],
    db=Depends(get_db)
):
    """Add mitigation plan for a risk"""
    mitigation_id = str(uuid4())

    query = """
        INSERT INTO risk_mitigations (id, risk_id, strategy, actions,
                                     responsible_party, timeline, cost_estimate)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
    """

    await db.execute(
        query, mitigation_id, risk_id,
        mitigation['strategy'], json.dumps(mitigation.get('actions', [])),
        mitigation.get('responsible_party'),
        mitigation.get('timeline'), mitigation.get('cost_estimate', 0)
    )

    # Update risk status
    await db.execute(
        "UPDATE risks SET status = 'mitigated' WHERE id = $1", risk_id
    )

    return {"mitigation_id": mitigation_id, "status": "plan_added"}
