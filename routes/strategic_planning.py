"""
Task 110: Strategic Planning
Business strategy and planning tools
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

@router.get("/plans")
async def list_strategic_plans(
    status: Optional[str] = None,
    timeframe: Optional[str] = None,
    db=Depends(get_db)
):
    """List strategic plans"""
    query = """
        SELECT id, plan_name, timeframe, status, start_date, end_date,
               objectives, created_at
        FROM strategic_plans
        WHERE ($1::text IS NULL OR status = $1)
        AND ($2::text IS NULL OR timeframe = $2)
        ORDER BY start_date DESC
    """
    rows = await db.fetch(query, status, timeframe)
    if not rows:
        return []
    return [dict(row) for row in rows]

@router.post("/plans")
async def create_strategic_plan(
    plan: Dict[str, Any],
    db=Depends(get_db)
):
    """Create strategic plan"""
    plan_id = str(uuid4())

    query = """
        INSERT INTO strategic_plans (id, plan_name, vision, mission,
                                    timeframe, objectives, strategies,
                                    start_date, end_date, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'draft')
        RETURNING id
    """

    await db.execute(
        query, plan_id, plan['plan_name'], plan.get('vision'),
        plan.get('mission'), plan.get('timeframe', 'annual'),
        json.dumps(plan.get('objectives', [])),
        json.dumps(plan.get('strategies', [])),
        plan['start_date'], plan['end_date']
    )

    return {"plan_id": plan_id, "status": "created"}

@router.get("/okrs")
async def get_okrs(
    quarter: Optional[str] = None,
    department: Optional[str] = None,
    db=Depends(get_db)
):
    """Get OKRs tracking"""
    query = """
        SELECT id, objective, key_results, owner, department,
               quarter, progress, status
        FROM okrs
        WHERE ($1::text IS NULL OR quarter = $1)
        AND ($2::text IS NULL OR department = $2)
        ORDER BY created_at DESC
    """
    rows = await db.fetch(query, quarter, department)
    if not rows:
        return []

    # Calculate overall progress
    okrs = []
    for row in rows:
        okr = dict(row)
        key_results = json.loads(row['key_results']) if row['key_results'] else []
        completed = sum(1 for kr in key_results if kr.get('completed', False))
        okr['completion_rate'] = (completed / len(key_results) * 100) if key_results else 0
        okrs.append(okr)

    return {
        "okrs": okrs,
        "overall_progress": sum(o['completion_rate'] for o in okrs) / len(okrs) if okrs else 0,
        "by_department": {}  # Would group by department
    }

@router.post("/swot")
async def create_swot_analysis(
    swot: Dict[str, Any],
    db=Depends(get_db)
):
    """Create SWOT analysis"""
    swot_id = str(uuid4())

    query = """
        INSERT INTO swot_analyses (id, analysis_name, strengths,
                                  weaknesses, opportunities, threats,
                                  recommendations, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        RETURNING id
    """

    await db.execute(
        query, swot_id, swot.get('analysis_name', f"SWOT {date.today()}"),
        json.dumps(swot.get('strengths', [])),
        json.dumps(swot.get('weaknesses', [])),
        json.dumps(swot.get('opportunities', [])),
        json.dumps(swot.get('threats', [])),
        json.dumps(swot.get('recommendations', []))
    )

    return {"swot_id": swot_id, "status": "created"}

@router.get("/scorecard")
async def get_balanced_scorecard(db=Depends(get_db)):
    """Get balanced scorecard"""

    # Financial perspective
    financial_query = """
        SELECT metric_name, current_value, target_value,
               (current_value / NULLIF(target_value, 0) * 100) as achievement
        FROM scorecard_metrics
        WHERE perspective = 'financial'
    """
    financial = await db.fetch(financial_query)

    # Customer perspective
    customer_query = """
        SELECT metric_name, current_value, target_value,
               (current_value / NULLIF(target_value, 0) * 100) as achievement
        FROM scorecard_metrics
        WHERE perspective = 'customer'
    """
    customer = await db.fetch(customer_query)

    # Internal process perspective
    process_query = """
        SELECT metric_name, current_value, target_value,
               (current_value / NULLIF(target_value, 0) * 100) as achievement
        FROM scorecard_metrics
        WHERE perspective = 'internal_process'
    """
    process = await db.fetch(process_query)

    # Learning & growth perspective
    learning_query = """
        SELECT metric_name, current_value, target_value,
               (current_value / NULLIF(target_value, 0) * 100) as achievement
        FROM scorecard_metrics
        WHERE perspective = 'learning_growth'
    """
    learning = await db.fetch(learning_query)

    return {
        "financial": [dict(row) for row in financial],
        "customer": [dict(row) for row in customer],
        "internal_process": [dict(row) for row in process],
        "learning_growth": [dict(row) for row in learning],
        "overall_score": 82.5  # Would calculate from actual metrics
    }
