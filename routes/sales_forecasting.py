"""
Sales Forecasting Module - Task 68
Complete sales forecasting and prediction system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncpg
import uuid
import json

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

# Models
class ForecastCreate(BaseModel):
    forecast_name: str
    forecast_period: str
    start_date: date
    end_date: date
    forecast_type: str = "quarterly"
    sales_rep: Optional[str] = None
    territory_id: Optional[str] = None
    team_id: Optional[str] = None
    quota_amount: float
    assumptions: Optional[str] = None
    risks: Optional[str] = None
    notes: Optional[str] = None

class ForecastResponse(BaseModel):
    id: str
    forecast_name: str
    forecast_period: str
    start_date: date
    end_date: date
    forecast_type: str
    pipeline_coverage: float
    committed_amount: float
    best_case_amount: float
    most_likely_amount: float
    worst_case_amount: float
    closed_amount: float
    quota_amount: float
    attainment_percentage: float
    opportunities_count: int
    created_at: datetime

# Endpoints
@router.post("/", response_model=ForecastResponse)
async def create_forecast(
    forecast: ForecastCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create sales forecast"""
    # Calculate initial forecast amounts (would be more complex in reality)
    pipeline_coverage = forecast.quota_amount * 3
    committed_amount = forecast.quota_amount * 0.8
    best_case_amount = forecast.quota_amount * 1.2
    most_likely_amount = forecast.quota_amount * 0.95
    worst_case_amount = forecast.quota_amount * 0.6

    query = """
        INSERT INTO sales_forecasts (
            forecast_name, forecast_period, start_date, end_date,
            forecast_type, sales_rep, territory_id, team_id,
            pipeline_coverage, committed_amount, best_case_amount,
            most_likely_amount, worst_case_amount, closed_amount,
            quota_amount, attainment_percentage, opportunities_count,
            assumptions, risks, notes, created_by
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
            $13, $14, $15, $16, $17, $18, $19, $20, $21
        ) RETURNING *
    """

    result = await conn.fetchrow(
        query,
        forecast.forecast_name,
        forecast.forecast_period,
        forecast.start_date,
        forecast.end_date,
        forecast.forecast_type,
        forecast.sales_rep,
        uuid.UUID(forecast.territory_id) if forecast.territory_id else None,
        uuid.UUID(forecast.team_id) if forecast.team_id else None,
        pipeline_coverage,
        committed_amount,
        best_case_amount,
        most_likely_amount,
        worst_case_amount,
        0,  # closed_amount starts at 0
        forecast.quota_amount,
        0,  # attainment_percentage starts at 0
        0,  # opportunities_count starts at 0
        forecast.assumptions,
        forecast.risks,
        forecast.notes,
        "system"
    )

    return {
        **dict(result),
        "id": str(result['id']),
        "territory_id": str(result['territory_id']) if result['territory_id'] else None,
        "team_id": str(result['team_id']) if result['team_id'] else None
    }

@router.get("/", response_model=List[ForecastResponse])
async def list_forecasts(
    forecast_type: Optional[str] = None,
    sales_rep: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List sales forecasts with filters"""
    conditions = []
    params = []

    if forecast_type:
        params.append(forecast_type)
        conditions.append(f"forecast_type = ${len(params)}")

    if sales_rep:
        params.append(sales_rep)
        conditions.append(f"sales_rep = ${len(params)}")

    if start_date:
        params.append(start_date)
        conditions.append(f"start_date >= ${len(params)}")

    if end_date:
        params.append(end_date)
        conditions.append(f"end_date <= ${len(params)}")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, skip])

    query = f"""
        SELECT * FROM sales_forecasts
        {where_clause}
        ORDER BY start_date DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "territory_id": str(row['territory_id']) if row['territory_id'] else None,
            "team_id": str(row['team_id']) if row['team_id'] else None
        }
        for row in rows
    ]
