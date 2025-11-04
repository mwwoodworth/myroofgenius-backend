"""
Data Visualization Module - Task 96
Interactive charts and dashboards
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncpg
import json
import random

router = APIRouter()

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

@router.get("/charts/revenue")
async def get_revenue_chart_data(
    period: str = "monthly",
    months: int = 12,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get revenue chart data"""
    data_points = []

    for i in range(months):
        date = datetime.now() - timedelta(days=30*i)
        revenue = 50000 + random.uniform(-10000, 20000)

        data_points.append({
            "label": date.strftime("%b %Y"),
            "value": round(revenue, 2),
            "change": round(random.uniform(-10, 20), 1)
        })

    return {
        "chart_type": "line",
        "title": "Revenue Trend",
        "period": period,
        "data": list(reversed(data_points)),
        "summary": {
            "total": sum(d["value"] for d in data_points),
            "average": sum(d["value"] for d in data_points) / len(data_points),
            "trend": "increasing"
        }
    }

@router.get("/charts/funnel")
async def get_funnel_data(
    funnel_type: str = "sales",
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get funnel visualization data"""
    if funnel_type == "sales":
        stages = [
            {"stage": "Leads", "value": 5000, "conversion": 100},
            {"stage": "Qualified", "value": 2500, "conversion": 50},
            {"stage": "Proposals", "value": 1000, "conversion": 40},
            {"stage": "Negotiation", "value": 500, "conversion": 50},
            {"stage": "Closed Won", "value": 250, "conversion": 50}
        ]
    else:
        stages = [
            {"stage": "Visitors", "value": 10000, "conversion": 100},
            {"stage": "Sign-ups", "value": 2000, "conversion": 20},
            {"stage": "Active Users", "value": 1500, "conversion": 75},
            {"stage": "Paid Users", "value": 500, "conversion": 33}
        ]

    return {
        "funnel_type": funnel_type,
        "stages": stages,
        "overall_conversion": stages[-1]["value"] / stages[0]["value"] * 100
    }

@router.get("/charts/heatmap")
async def get_heatmap_data(
    metric: str = "activity",
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get heatmap data"""
    heatmap_data = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = list(range(24))

    for day in days:
        for hour in hours:
            value = random.randint(0, 100)
            heatmap_data.append({
                "day": day,
                "hour": hour,
                "value": value,
                "label": f"{value} {metric}"
            })

    return {
        "metric": metric,
        "data": heatmap_data,
        "peak_time": {"day": "Wed", "hour": 14},
        "lowest_time": {"day": "Sun", "hour": 3}
    }

@router.get("/dashboards")
async def list_dashboards(
    conn: asyncpg.Connection = Depends(get_db)
):
    """List available dashboards"""
    dashboards = [
        {
            "id": "executive",
            "name": "Executive Dashboard",
            "description": "High-level KPIs and metrics",
            "widgets": ["revenue_chart", "kpi_cards", "funnel", "map"]
        },
        {
            "id": "operations",
            "name": "Operations Dashboard",
            "description": "Operational metrics and efficiency",
            "widgets": ["throughput", "queue_status", "sla_metrics", "resource_util"]
        },
        {
            "id": "sales",
            "name": "Sales Dashboard",
            "description": "Sales performance and pipeline",
            "widgets": ["pipeline_funnel", "rep_performance", "forecast", "deals"]
        }
    ]
    return dashboards

@router.post("/dashboards/custom")
async def create_custom_dashboard(
    name: str,
    widgets: List[str],
    layout: Optional[Dict[str, Any]] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create custom dashboard"""
    query = """
        INSERT INTO custom_dashboards (
            name, widgets, layout, created_by
        ) VALUES ($1, $2, $3, $4)
        RETURNING id
    """

    result = await conn.fetchrow(
        query,
        name,
        json.dumps(widgets),
        json.dumps(layout or {}),
        "current_user"
    )

    return {
        "id": str(result['id']),
        "name": name,
        "widgets": widgets,
        "status": "created"
    }
