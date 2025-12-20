"""
Data Visualization Module - Task 96
Interactive charts and dashboards backed by real database metrics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import asyncpg
import json

from core.supabase_auth import get_authenticated_user

router = APIRouter()

async def get_db_pool(request: Request) -> asyncpg.Pool:
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return pool

@router.get("/charts/revenue")
async def get_revenue_chart_data(
    request: Request,
    period: str = "monthly",
    months: int = 12,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Get revenue chart data"""
    if months < 1 or months > 60:
        raise HTTPException(status_code=400, detail="months must be between 1 and 60")

    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            WITH months AS (
                SELECT date_trunc('month', NOW()) - (interval '1 month' * gs) AS month_start
                FROM generate_series(0, $2::int - 1) AS gs
            ),
            revenue AS (
                SELECT date_trunc('month', created_at) AS month_start,
                       SUM(COALESCE(total_amount, 0)) AS revenue
                FROM invoices
                WHERE tenant_id = $1
                  AND (status = 'paid' OR payment_status = 'paid')
                  AND created_at >= date_trunc('month', NOW()) - (interval '1 month' * ($2::int - 1))
                GROUP BY 1
            )
            SELECT m.month_start, COALESCE(r.revenue, 0) AS revenue
            FROM months m
            LEFT JOIN revenue r USING (month_start)
            ORDER BY m.month_start
            """,
            tenant_id,
            months,
        )

    data_points: List[Dict[str, Any]] = []
    prev_value: Optional[float] = None
    for row in rows:
        value = float(row["revenue"] or 0)
        change = None
        if prev_value is not None and prev_value != 0:
            change = round(((value - prev_value) / prev_value) * 100, 1)
        data_points.append(
            {
                "label": row["month_start"].strftime("%b %Y"),
                "value": round(value, 2),
                "change": change,
            }
        )
        prev_value = value

    return {
        "chart_type": "line",
        "title": "Revenue Trend",
        "period": period,
        "data": data_points,
        "summary": {
            "total": round(sum(d["value"] for d in data_points), 2),
            "average": round(sum(d["value"] for d in data_points) / len(data_points), 2)
            if data_points
            else 0,
        }
    }

@router.get("/charts/funnel")
async def get_funnel_data(
    request: Request,
    funnel_type: str = "sales",
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Get funnel visualization data"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    stages: List[Dict[str, Any]] = []

    async with pool.acquire() as conn:
        if funnel_type == "sales":
            leads = qualified = proposals = negotiation = won = None
            try:
                leads = await conn.fetchval("SELECT COUNT(*) FROM leads WHERE tenant_id = $1", tenant_id)
            except Exception:
                leads = None
            try:
                qualified = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM leads
                    WHERE tenant_id = $1
                      AND (status = 'qualified' OR score >= 70)
                    """,
                    tenant_id,
                )
            except Exception:
                qualified = None
            try:
                proposals = await conn.fetchval(
                    "SELECT COUNT(*) FROM estimates WHERE tenant_id = $1", tenant_id
                )
            except Exception:
                proposals = None
            try:
                negotiation = await conn.fetchval(
                    "SELECT COUNT(*) FROM estimates WHERE tenant_id = $1 AND status = 'sent'", tenant_id
                )
            except Exception:
                negotiation = None
            try:
                won = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM invoices
                    WHERE tenant_id = $1 AND (status = 'paid' OR payment_status = 'paid')
                    """,
                    tenant_id,
                )
            except Exception:
                won = None

            stages = [
                {"stage": "Leads", "value": leads},
                {"stage": "Qualified", "value": qualified},
                {"stage": "Proposals", "value": proposals},
                {"stage": "Negotiation", "value": negotiation},
                {"stage": "Closed Won", "value": won},
            ]
        else:
            signups = active_users = paid_users = None
            try:
                signups = await conn.fetchval(
                    "SELECT COUNT(*) FROM customers WHERE tenant_id = $1", tenant_id
                )
            except Exception:
                signups = None
            try:
                active_users = await conn.fetchval(
                    """
                    SELECT COUNT(DISTINCT user_id)
                    FROM user_sessions
                    WHERE tenant_id = $1
                      AND created_at >= NOW() - INTERVAL '30 days'
                    """,
                    tenant_id,
                )
            except Exception:
                active_users = None
            try:
                paid_users = await conn.fetchval(
                    "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'",  # no tenant scoping available in all schemas
                )
            except Exception:
                paid_users = None

            stages = [
                {"stage": "Visitors", "value": None},
                {"stage": "Sign-ups", "value": signups},
                {"stage": "Active Users", "value": active_users},
                {"stage": "Paid Users", "value": paid_users},
            ]

    # Compute step conversions without fabricating missing values.
    prior = stages[0].get("value")
    for stage in stages:
        value = stage.get("value")
        if prior in (None, 0) or value is None:
            stage["conversion"] = None
        else:
            stage["conversion"] = round((value / prior) * 100, 2)
        if value is not None:
            prior = value

    return {
        "funnel_type": funnel_type,
        "stages": stages,
        "overall_conversion": stages[-1]["conversion"],
    }

@router.get("/charts/heatmap")
async def get_heatmap_data(
    request: Request,
    metric: str = "activity",
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Get heatmap data"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    metric_map: Dict[str, Tuple[str, str]] = {
        "jobs": ("jobs", "created_at"),
        "invoices": ("invoices", "created_at"),
        "leads": ("leads", "created_at"),
    }

    if metric not in metric_map:
        raise HTTPException(status_code=400, detail=f"Unsupported metric '{metric}'")

    table, ts_col = metric_map[metric]
    start_time = datetime.now() - timedelta(days=30)

    heatmap_data: List[Dict[str, Any]] = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Build a complete 7x24 grid; fill from DB counts where possible.
    counts: Dict[Tuple[int, int], int] = {}
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                f"""
                SELECT EXTRACT(DOW FROM {ts_col})::int AS dow,
                       EXTRACT(HOUR FROM {ts_col})::int AS hour,
                       COUNT(*)::int AS value
                FROM {table}
                WHERE tenant_id = $1
                  AND {ts_col} >= $2
                GROUP BY 1, 2
                """,
                tenant_id,
                start_time,
            )
            for row in rows:
                counts[(row["dow"], row["hour"])] = row["value"]
        except Exception:
            return {"metric": metric, "data": [], "available": False}

    # Postgres DOW: Sunday=0 ... Saturday=6. Convert to Mon=0..Sun=6.
    def _dow_to_index(dow: int) -> int:
        return (dow - 1) % 7

    peak = {"day": None, "hour": None, "value": None}
    low = {"day": None, "hour": None, "value": None}

    for day_index, day_name in enumerate(days):
        for hour in range(24):
            # Convert day_index back to postgres dow for lookup.
            pg_dow = (day_index + 1) % 7
            value = int(counts.get((pg_dow, hour), 0))
            heatmap_data.append(
                {"day": day_name, "hour": hour, "value": value, "label": f"{value} {metric}"}
            )
            if peak["value"] is None or value > peak["value"]:
                peak = {"day": day_name, "hour": hour, "value": value}
            if low["value"] is None or value < low["value"]:
                low = {"day": day_name, "hour": hour, "value": value}

    return {"metric": metric, "data": heatmap_data, "peak_time": peak, "lowest_time": low}

@router.get("/dashboards")
async def list_dashboards(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
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
    request: Request,
    name: str,
    widgets: List[str],
    layout: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
    pool: asyncpg.Pool = Depends(get_db_pool),
):
    """Create custom dashboard"""
    user_id = current_user.get("id") or "unknown"
    query = """
        INSERT INTO custom_dashboards (
            name, widgets, layout, created_by
        ) VALUES ($1, $2, $3, $4)
        RETURNING id
    """

    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            query,
            name,
            json.dumps(widgets),
            json.dumps(layout or {}),
            user_id,
        )

    return {
        "id": str(result['id']),
        "name": name,
        "widgets": widgets,
        "status": "created"
    }
