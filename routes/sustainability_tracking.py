"""
Task 108: Sustainability Tracking
Environmental, social, and governance (ESG) metrics
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

@router.get("/metrics")
async def get_esg_metrics(
    period: Optional[str] = Query("monthly", description="Period for metrics"),
    db=Depends(get_db)
):
    """Get ESG metrics"""
    query = """
        SELECT metric_category, metric_name, value, unit,
               measurement_date
        FROM sustainability_metrics
        WHERE measurement_date >= CURRENT_DATE - INTERVAL '1 year'
        ORDER BY measurement_date DESC
    """
    rows = await db.fetch(query)
    if not rows:
        return []

    # Group by category
    metrics = {
        "environmental": [],
        "social": [],
        "governance": []
    }

    for row in rows:
        category = row['metric_category'].lower()
        if category in metrics:
            metrics[category].append({
                "name": row['metric_name'],
                "value": float(row['value'] or 0),
                "unit": row['unit'],
                "date": str(row['measurement_date'])
            })

    return metrics

@router.get("/carbon")
async def get_carbon_footprint(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db=Depends(get_db)
):
    """Get carbon footprint data"""
    if not start_date:
        start_date = date.today() - timedelta(days=365)
    if not end_date:
        end_date = date.today()

    query = """
        SELECT
            emission_source,
            SUM(co2_equivalent) as total_emissions,
            AVG(co2_equivalent) as avg_emissions
        FROM carbon_emissions
        WHERE emission_date BETWEEN $1 AND $2
        GROUP BY emission_source
    """
    rows = await db.fetch(query, start_date, end_date)
    if not rows:
        return []

    total = sum(float(row['total_emissions'] or 0) for row in rows)

    return {
        "period": {"start": str(start_date), "end": str(end_date)},
        "total_emissions": total,
        "by_source": [dict(row) for row in rows],
        "reduction_target": total * 0.8,  # 20% reduction target
        "offset_required": max(0, total - (total * 0.8))
    }

@router.post("/initiatives")
async def add_sustainability_initiative(
    initiative: Dict[str, Any],
    db=Depends(get_db)
):
    """Add sustainability initiative"""
    init_id = str(uuid4())

    query = """
        INSERT INTO sustainability_initiatives (id, name, category,
                                               description, goals,
                                               start_date, target_date)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
    """

    await db.execute(
        query, init_id, initiative['name'], initiative.get('category', 'environmental'),
        initiative.get('description'), json.dumps(initiative.get('goals', [])),
        initiative.get('start_date', date.today()),
        initiative.get('target_date')
    )

    return {"initiative_id": init_id, "status": "created"}
