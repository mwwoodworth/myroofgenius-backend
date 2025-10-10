"""
Sales Analytics Module - Task 70
Complete sales performance analytics system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import asyncpg
import uuid

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

# Endpoints
@router.get("/dashboard")
async def get_sales_dashboard(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sales_rep: Optional[str] = None,
    territory_id: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get comprehensive sales dashboard data"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    # Build conditions
    conditions = ["created_at >= $1 AND created_at <= $2"]
    params = [start_date, end_date + timedelta(days=1)]

    if sales_rep:
        params.append(sales_rep)
        conditions.append(f"assigned_to = ${len(params)}")

    if territory_id:
        params.append(uuid.UUID(territory_id))
        conditions.append(f"territory_id = ${len(params)}")

    where_clause = " AND ".join(conditions)

    # Get key metrics
    metrics_query = f"""
        SELECT
            COUNT(DISTINCT l.id) as total_leads,
            COUNT(DISTINCT o.id) as total_opportunities,
            COUNT(DISTINCT CASE WHEN o.is_won THEN o.id END) as won_deals,
            COUNT(DISTINCT CASE WHEN o.is_closed AND NOT o.is_won THEN o.id END) as lost_deals,
            COALESCE(SUM(CASE WHEN o.is_won THEN o.amount ELSE 0 END), 0) as revenue,
            COALESCE(SUM(CASE WHEN NOT o.is_closed THEN o.amount ELSE 0 END), 0) as pipeline_value,
            COALESCE(AVG(o.amount), 0) as avg_deal_size,
            COALESCE(AVG(CASE WHEN o.is_closed THEN
                EXTRACT(DAY FROM o.closed_date - o.created_at)
            END), 0) as avg_sales_cycle
        FROM leads l
        LEFT JOIN opportunities o ON l.id = o.lead_id
        WHERE l.{where_clause}
    """

    metrics = await conn.fetchrow(metrics_query, *params)

    # Get conversion rates
    total_leads = metrics['total_leads'] or 0
    total_opportunities = metrics['total_opportunities'] or 0
    won_deals = metrics['won_deals'] or 0
    lost_deals = metrics['lost_deals'] or 0

    lead_to_opp_rate = (total_opportunities / total_leads * 100) if total_leads > 0 else 0
    win_rate = (won_deals / (won_deals + lost_deals) * 100) if (won_deals + lost_deals) > 0 else 0

    # Get pipeline stages
    pipeline_query = f"""
        SELECT
            stage,
            COUNT(*) as count,
            SUM(amount) as value
        FROM opportunities
        WHERE NOT is_closed AND {where_clause}
        GROUP BY stage
    """

    pipeline_stages = await conn.fetch(pipeline_query, *params)

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "metrics": {
            "total_leads": total_leads,
            "total_opportunities": total_opportunities,
            "won_deals": won_deals,
            "lost_deals": lost_deals,
            "revenue": float(metrics['revenue']),
            "pipeline_value": float(metrics['pipeline_value']),
            "avg_deal_size": float(metrics['avg_deal_size']),
            "avg_sales_cycle_days": float(metrics['avg_sales_cycle'])
        },
        "conversion_rates": {
            "lead_to_opportunity": round(lead_to_opp_rate, 2),
            "win_rate": round(win_rate, 2)
        },
        "pipeline_stages": [
            {
                "stage": row['stage'],
                "count": row['count'],
                "value": float(row['value'])
            }
            for row in pipeline_stages
        ]
    }

@router.get("/performance/{sales_rep}")
async def get_sales_rep_performance(
    sales_rep: str,
    year: int = Query(datetime.now().year),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get performance metrics for a sales rep"""
    # Monthly performance
    monthly_query = """
        SELECT
            EXTRACT(MONTH FROM created_at) as month,
            COUNT(*) as deals,
            SUM(CASE WHEN is_won THEN amount ELSE 0 END) as revenue,
            COUNT(CASE WHEN is_won THEN 1 END) as won_deals
        FROM opportunities
        WHERE assigned_to = $1
        AND EXTRACT(YEAR FROM created_at) = $2
        GROUP BY EXTRACT(MONTH FROM created_at)
        ORDER BY month
    """

    monthly_data = await conn.fetch(monthly_query, sales_rep, year)

    # Year-to-date stats
    ytd_query = """
        SELECT
            COUNT(*) as total_opportunities,
            COUNT(CASE WHEN is_won THEN 1 END) as won_deals,
            COUNT(CASE WHEN is_closed AND NOT is_won THEN 1 END) as lost_deals,
            SUM(CASE WHEN is_won THEN amount ELSE 0 END) as total_revenue,
            SUM(CASE WHEN NOT is_closed THEN amount ELSE 0 END) as pipeline_value,
            AVG(amount) as avg_deal_size
        FROM opportunities
        WHERE assigned_to = $1
        AND EXTRACT(YEAR FROM created_at) = $2
    """

    ytd_stats = await conn.fetchrow(ytd_query, sales_rep, year)

    # Calculate win rate
    total_closed = (ytd_stats['won_deals'] or 0) + (ytd_stats['lost_deals'] or 0)
    win_rate = ((ytd_stats['won_deals'] or 0) / total_closed * 100) if total_closed > 0 else 0

    return {
        "sales_rep": sales_rep,
        "year": year,
        "monthly_performance": [
            {
                "month": int(row['month']),
                "deals": row['deals'],
                "revenue": float(row['revenue'] or 0),
                "won_deals": row['won_deals']
            }
            for row in monthly_data
        ],
        "ytd_stats": {
            "total_opportunities": ytd_stats['total_opportunities'] or 0,
            "won_deals": ytd_stats['won_deals'] or 0,
            "lost_deals": ytd_stats['lost_deals'] or 0,
            "total_revenue": float(ytd_stats['total_revenue'] or 0),
            "pipeline_value": float(ytd_stats['pipeline_value'] or 0),
            "avg_deal_size": float(ytd_stats['avg_deal_size'] or 0),
            "win_rate": round(win_rate, 2)
        }
    }

@router.get("/trends")
async def get_sales_trends(
    period: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly)$"),
    months: int = Query(6, ge=1, le=24),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get sales trends over time"""
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)

    # Determine grouping based on period
    if period == "daily":
        date_trunc = "day"
    elif period == "weekly":
        date_trunc = "week"
    elif period == "quarterly":
        date_trunc = "quarter"
    else:
        date_trunc = "month"

    query = f"""
        SELECT
            DATE_TRUNC('{date_trunc}', created_at) as period,
            COUNT(*) as opportunities,
            COUNT(CASE WHEN is_won THEN 1 END) as won_deals,
            SUM(amount) as total_value,
            SUM(CASE WHEN is_won THEN amount ELSE 0 END) as revenue,
            AVG(amount) as avg_deal_size
        FROM opportunities
        WHERE created_at >= $1 AND created_at <= $2
        GROUP BY DATE_TRUNC('{date_trunc}', created_at)
        ORDER BY period
    """

    rows = await conn.fetch(query, start_date, end_date)

    return {
        "period_type": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "trends": [
            {
                "period": row['period'].isoformat(),
                "opportunities": row['opportunities'],
                "won_deals": row['won_deals'],
                "total_value": float(row['total_value'] or 0),
                "revenue": float(row['revenue'] or 0),
                "avg_deal_size": float(row['avg_deal_size'] or 0),
                "win_rate": round((row['won_deals'] / row['opportunities'] * 100) if row['opportunities'] > 0 else 0, 2)
            }
            for row in rows
        ]
    }
