"""
Real-Time Revenue Dashboard
Track every dollar, optimize every metric
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta, date
from sqlalchemy import text
from sqlalchemy.orm import Session
import json
import uuid

from database import get_db
from core.supabase_auth import get_current_user

router = APIRouter(tags=["Revenue Dashboard"])

def _get_table_columns(db: Session, table: str) -> Set[str]:
    try:
        rows = db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table
                """
            ),
            {"table": table},
        ).fetchall()
        return {row[0] for row in rows}
    except Exception:
        return set()


def _tenant_filter(has_tenant: bool, tenant_id: Optional[uuid.UUID], alias: Optional[str] = None) -> str:
    if not has_tenant or not tenant_id:
        return ""
    column = f\"{alias}.tenant_id\" if alias else \"tenant_id\"
    return f\" AND {column} = :tenant_id\"

@router.get("/dashboard-metrics")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Real-time revenue metrics and KPIs
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")
    
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")

    rt_cols = _get_table_columns(db, "revenue_tracking")
    leads_cols = _get_table_columns(db, "leads")
    subs_cols = _get_table_columns(db, "subscriptions")
    goals_cols = _get_table_columns(db, "revenue_goals")

    rt_has_tenant = "tenant_id" in rt_cols
    leads_has_tenant = "tenant_id" in leads_cols
    subs_has_tenant = "tenant_id" in subs_cols
    goals_has_tenant = "tenant_id" in goals_cols

    amount_expr = "amount_cents / 100.0" if "amount_cents" in rt_cols else "revenue"
    customer_expr = (
        "customer_email"
        if "customer_email" in rt_cols
        else "customer_id"
        if "customer_id" in rt_cols
        else "NULL"
    )
    source_expr = "source" if "source" in rt_cols else "channel" if "channel" in rt_cols else None

    rt_tenant_clause = _tenant_filter(rt_has_tenant, tenant_uuid)
    leads_tenant_clause = _tenant_filter(leads_has_tenant, tenant_uuid)
    subs_tenant_clause = _tenant_filter(subs_has_tenant, tenant_uuid)
    goals_tenant_clause = _tenant_filter(goals_has_tenant, tenant_uuid)

    # Today's revenue
    today_revenue = db.execute(
        text(
            f"""
            SELECT
                COALESCE(SUM({amount_expr}), 0) as revenue,
                COUNT(DISTINCT {customer_expr}) as customers,
                COUNT(*) as transactions
            FROM revenue_tracking
            WHERE DATE(created_at) = CURRENT_DATE {rt_tenant_clause}
            """
        ),
        {"tenant_id": tenant_uuid}
    ).mappings().first() or {"revenue": 0, "customers": 0, "transactions": 0}

    # Week to date
    week_revenue = db.execute(
        text(
            f"""
            SELECT
                COALESCE(SUM({amount_expr}), 0) as revenue,
                COUNT(DISTINCT {customer_expr}) as customers
            FROM revenue_tracking
            WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE) {rt_tenant_clause}
            """
        ),
        {"tenant_id": tenant_uuid}
    ).mappings().first() or {"revenue": 0, "customers": 0}

    # Month to date
    month_revenue = db.execute(
        text(
            f"""
            SELECT
                COALESCE(SUM({amount_expr}), 0) as revenue,
                COUNT(DISTINCT {customer_expr}) as customers
            FROM revenue_tracking
            WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE) {rt_tenant_clause}
            """
        ),
        {"tenant_id": tenant_uuid}
    ).mappings().first() or {"revenue": 0, "customers": 0}

    # MRR calculation
    mrr = None
    for mrr_query in (
        f"""
        SELECT COALESCE(SUM(
            CASE
                WHEN billing_cycle ILIKE 'year%%' THEN amount / 12.0
                WHEN billing_cycle ILIKE 'month%%' THEN amount
                ELSE amount
            END
        ), 0) as mrr
        FROM subscriptions
        WHERE status = 'active' {subs_tenant_clause}
        """,
        f"""
        SELECT COALESCE(SUM(amount_cents) / 100.0, 0) as mrr
        FROM subscriptions
        WHERE status = 'active' {subs_tenant_clause}
        """,
        f"""
        SELECT COALESCE(SUM(amount) , 0) as mrr
        FROM subscriptions
        WHERE status = 'active' {subs_tenant_clause}
        """,
    ):
        try:
            mrr = db.execute(text(mrr_query), {"tenant_id": tenant_uuid}).scalar()
            break
        except Exception:
            mrr = None

    # Lead metrics (schema-aware)
    try:
        if "segment" in leads_cols:
            hot_expr = "COUNT(CASE WHEN segment = 'hot' THEN 1 END)"
        elif "status" in leads_cols:
            hot_expr = "COUNT(CASE WHEN status = 'hot' THEN 1 END)"
        elif "score" in leads_cols:
            hot_expr = "COUNT(CASE WHEN score >= 80 THEN 1 END)"
        else:
            hot_expr = "0"

        if "converted" in leads_cols:
            converted_expr = "COUNT(CASE WHEN converted = true THEN 1 END)"
        elif "converted_date" in leads_cols:
            converted_expr = "COUNT(CASE WHEN converted_date IS NOT NULL THEN 1 END)"
        else:
            converted_expr = "0"

        avg_score_expr = "AVG(score)" if "score" in leads_cols else "0"

        lead_metrics = db.execute(
            text(
                f"""
                SELECT
                    COUNT(*) as total_leads,
                    {hot_expr} as hot_leads,
                    {converted_expr} as converted,
                    {avg_score_expr} as avg_score
                FROM leads
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' {leads_tenant_clause}
                """
            ),
            {"tenant_id": tenant_uuid}
        ).mappings().first()
    except Exception:
        lead_metrics = {"total_leads": 0, "hot_leads": 0, "converted": 0, "avg_score": 0}

    # Conversion funnel (schema-aware)
    try:
        qualified_expr = None
        if "score" in leads_cols:
            qualified_expr = "COUNT(DISTINCT CASE WHEN score >= 60 THEN email END)"
        elif "status" in leads_cols:
            qualified_expr = "COUNT(DISTINCT CASE WHEN status ILIKE 'qualified' THEN email END)"
        else:
            qualified_expr = "0"

        leads_count = db.execute(
            text(
                f"""
                SELECT COUNT(DISTINCT email) as leads
                FROM leads
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' {leads_tenant_clause}
                """
            ),
            {"tenant_id": tenant_uuid}
        ).scalar() or 0

        qualified_count = db.execute(
            text(
                f"""
                SELECT {qualified_expr} as qualified
                FROM leads
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days' {leads_tenant_clause}
                """
            ),
            {"tenant_id": tenant_uuid}
        ).scalar() or 0

        subs_customer_expr = (
            "customer_email"
            if "customer_email" in subs_cols
            else "customer_id"
            if "customer_id" in subs_cols
            else "user_id"
            if "user_id" in subs_cols
            else "id"
        )

        trials_count = db.execute(
            text(
                f"""
                SELECT COUNT(DISTINCT {subs_customer_expr}) as trials
                FROM subscriptions
                WHERE status = 'trialing' {subs_tenant_clause}
                """
            ),
            {"tenant_id": tenant_uuid}
        ).scalar() or 0

        paid_count = db.execute(
            text(
                f"""
                SELECT COUNT(DISTINCT {subs_customer_expr}) as paid
                FROM subscriptions
                WHERE status = 'active' {subs_tenant_clause}
                """
            ),
            {"tenant_id": tenant_uuid}
        ).scalar() or 0

        funnel = {
            "leads": int(leads_count or 0),
            "qualified": int(qualified_count or 0),
            "trials": int(trials_count or 0),
            "paid": int(paid_count or 0),
        }
    except Exception:
        funnel = {"leads": 0, "qualified": 0, "trials": 0, "paid": 0}

    # Revenue by source
    if source_expr:
        revenue_sources = db.execute(
            text(
                f"""
                SELECT
                    {source_expr} as source,
                    COUNT(*) as transactions,
                    COALESCE(SUM({amount_expr}), 0) as revenue
                FROM revenue_tracking
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' {rt_tenant_clause}
                GROUP BY {source_expr}
                ORDER BY revenue DESC
                """
            ),
            {"tenant_id": tenant_uuid}
        ).mappings().all()
    else:
        revenue_sources = []

    # Targets
    target_amount = None
    current_amount = None
    period_start = None
    period_end = None
    days_remaining = None

    try:
        goal = None
        if "period_start" in goals_cols and "period_end" in goals_cols:
            goal = db.execute(
                text(
                    f"""
                    SELECT period_start, period_end, target_cents
                    FROM revenue_goals
                    WHERE period_start <= CURRENT_DATE
                      AND period_end >= CURRENT_DATE
                      {goals_tenant_clause}
                    ORDER BY period_start DESC
                    LIMIT 1
                    """
                ),
                {"tenant_id": tenant_uuid}
            ).mappings().first()
            if goal:
                period_start = goal.get("period_start")
                period_end = goal.get("period_end")
                target_amount = (goal.get("target_cents") or 0) / 100.0 if goal.get("target_cents") is not None else None
        elif "goal_date" in goals_cols:
            goal = db.execute(
                text(
                    f"""
                    SELECT goal_date, target_revenue
                    FROM revenue_goals
                    WHERE goal_date <= CURRENT_DATE
                    {goals_tenant_clause}
                    ORDER BY goal_date DESC
                    LIMIT 1
                    """
                ),
                {"tenant_id": tenant_uuid}
            ).mappings().first()
            if goal:
                period_start = goal.get("goal_date")
                period_end = goal.get("goal_date")
                target_amount = float(goal.get("target_revenue") or 0)

        if period_start and period_end:
            current_amount = db.execute(
                text(
                    f"""
                    SELECT COALESCE(SUM({amount_expr}), 0) as revenue
                    FROM revenue_tracking
                    WHERE created_at >= :start_date
                      AND created_at < (:end_date::date + INTERVAL '1 day')
                      {rt_tenant_clause}
                    """
                ),
                {"start_date": period_start, "end_date": period_end, "tenant_id": tenant_uuid},
            ).scalar()
            days_remaining = max(0, (period_end - date.today()).days)
    except Exception:
        target_amount = None
        current_amount = None

    progress = None
    remaining = None
    daily_needed = None
    if target_amount and current_amount is not None and target_amount > 0:
        progress = round((current_amount / target_amount) * 100, 2)
        remaining = max(0, target_amount - current_amount)
        daily_needed = (remaining / days_remaining) if days_remaining and days_remaining > 0 else remaining

    return {
        "current_metrics": {
            "today": {
                "revenue": today_revenue["revenue"],
                "customers": today_revenue["customers"],
                "transactions": today_revenue["transactions"],
                "avg_order_value": (today_revenue["revenue"] / today_revenue["transactions"]) if today_revenue["transactions"] else 0,
            },
            "week_to_date": {"revenue": week_revenue["revenue"], "customers": week_revenue["customers"]},
            "month_to_date": {"revenue": month_revenue["revenue"], "customers": month_revenue["customers"]},
            "mrr": mrr,
        },
        "targets": {
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
            "target": target_amount,
            "current": current_amount,
            "progress": progress,
            "remaining": remaining,
            "days_remaining": days_remaining,
            "daily_needed": daily_needed,
        },
        "lead_metrics": dict(lead_metrics) if lead_metrics else {},
        "conversion_funnel": dict(funnel) if funnel else {},
        "revenue_by_source": [dict(s) for s in revenue_sources],
        "recommendations": generate_revenue_recommendations(current_amount or week_revenue["revenue"], target_amount, lead_metrics),
    }

def generate_revenue_recommendations(current_revenue, target, lead_metrics):
    """Generate actionable recommendations based on performance"""
    recommendations = []
    
    if not target or target <= 0:
        return recommendations

    gap = target - (current_revenue or 0)
    if gap > 0:
        recommendations.append({
            "priority": "high",
            "action": f"Need ${gap:.2f} more to hit target",
            "suggestion": "Increase ad spend and launch flash promotion"
        })
    
    if lead_metrics and isinstance(lead_metrics, dict) and lead_metrics.get("hot_leads", 0) < 10:
        recommendations.append({
            "priority": "high",
            "action": "Low hot lead count",
            "suggestion": "Increase urgency messaging in ads"
        })
    
    if lead_metrics and isinstance(lead_metrics, dict) and lead_metrics.get("avg_score", 0) < 60:
        recommendations.append({
            "priority": "medium",
            "action": "Lead quality below target",
            "suggestion": "Refine targeting and qualify better"
        })
    
    return recommendations

@router.get("/live-feed")
def get_live_revenue_feed(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Real-time feed of revenue events
    """
    tenant_id = current_user.get("tenant_id")
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None

    rt_cols = _get_table_columns(db, "revenue_tracking")
    leads_cols = _get_table_columns(db, "leads")
    rt_tenant_clause = _tenant_filter("tenant_id" in rt_cols, tenant_uuid)
    leads_tenant_clause = _tenant_filter("tenant_id" in leads_cols, tenant_uuid)

    amount_expr = "amount_cents / 100.0" if "amount_cents" in rt_cols else "revenue"
    source_expr = "source" if "source" in rt_cols else "channel" if "channel" in rt_cols else "NULL"
    lead_score_expr = "score" if "score" in leads_cols else "0"
    lead_segment_expr = (
        "segment"
        if "segment" in leads_cols
        else "status"
        if "status" in leads_cols
        else "NULL"
    )

    events = db.execute(
        text(
            f"""
            SELECT 
                'revenue' as type,
                customer_email,
                {amount_expr} as amount,
                {source_expr} as source,
                product_name,
                created_at
            FROM revenue_tracking
            WHERE created_at >= NOW() - INTERVAL '24 hours' {rt_tenant_clause}
            
            UNION ALL
            
            SELECT 
                'lead' as type,
                email as customer_email,
                {lead_score_expr} as amount,
                source,
                {lead_segment_expr} as product_name,
                created_at
            FROM leads
            WHERE created_at >= NOW() - INTERVAL '24 hours' {leads_tenant_clause}
            
            ORDER BY created_at DESC
            LIMIT 50
            """
        ),
        {"tenant_id": tenant_uuid}
    ).fetchall()
    
    return {
        "events": [
            {
                "type": e.type,
                "customer": e.customer_email[:3] + "***" if e.customer_email else "Anonymous",
                "amount": e.amount,
                "source": e.source,
                "product": e.product_name,
                "time_ago": format_time_ago(e.created_at)
            }
            for e in events
        ]
    }

def format_time_ago(timestamp):
    """Format timestamp as time ago"""
    if not timestamp:
        return "Unknown"
    
    diff = datetime.utcnow() - timestamp
    
    if diff.seconds < 60:
        return "Just now"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60} min ago"
    elif diff.seconds < 86400:
        return f"{diff.seconds // 3600} hours ago"
    else:
        return f"{diff.days} days ago"

@router.get("/hourly-performance")
def get_hourly_performance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Hourly revenue performance for today
    """
    tenant_id = current_user.get("tenant_id")
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None

    rt_cols = _get_table_columns(db, "revenue_tracking")
    rt_tenant_clause = _tenant_filter("tenant_id" in rt_cols, tenant_uuid)
    amount_expr = "amount_cents / 100.0" if "amount_cents" in rt_cols else "revenue"
    customer_expr = (
        "customer_email"
        if "customer_email" in rt_cols
        else "customer_id"
        if "customer_id" in rt_cols
        else "NULL"
    )

    hourly = db.execute(
        text(
            f"""
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as transactions,
                COALESCE(SUM({amount_expr}), 0) as revenue,
                COUNT(DISTINCT {customer_expr}) as unique_customers
            FROM revenue_tracking
            WHERE DATE(created_at) = CURRENT_DATE {rt_tenant_clause}
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
            """
        ),
        {"tenant_id": tenant_uuid}
    ).fetchall()
    
    # Fill in missing hours
    hourly_data = {int(h.hour): dict(h._mapping) for h in hourly}
    current_hour = datetime.utcnow().hour
    
    complete_hourly = []
    for hour in range(24):
        if hour <= current_hour:
            data = hourly_data.get(hour, {
                "hour": hour,
                "transactions": 0,
                "revenue": 0,
                "unique_customers": 0
            })
            complete_hourly.append(data)
    
    return {
        "hourly_data": complete_hourly,
        "peak_hour": max(complete_hourly, key=lambda x: x["revenue"])["hour"] if complete_hourly else None,
        "total_today": sum(h["revenue"] for h in complete_hourly)
    }

@router.get("/campaign-roi")
def get_campaign_roi(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    ROI analysis by marketing campaign
    """
    tenant_id = current_user.get("tenant_id")
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None

    campaign_cols = _get_table_columns(db, "ad_campaigns")
    perf_cols = _get_table_columns(db, "ad_performance")
    rt_cols = _get_table_columns(db, "revenue_tracking")

    campaign_tenant_clause = _tenant_filter("tenant_id" in campaign_cols, tenant_uuid, "c")
    perf_tenant_clause = _tenant_filter("tenant_id" in perf_cols, tenant_uuid, "p")
    rt_tenant_clause = _tenant_filter("tenant_id" in rt_cols, tenant_uuid)

    budget_expr = "c.budget_daily_cents / 100.0" if "budget_daily_cents" in campaign_cols else "c.budget"
    spend_cents_expr = "SUM(p.spend_cents)" if "spend_cents" in perf_cols else "SUM(p.spend) * 100.0"
    amount_expr = "amount_cents" if "amount_cents" in rt_cols else "revenue"
    source_expr = "source" if "source" in rt_cols else "channel" if "channel" in rt_cols else "NULL"

    campaigns = db.execute(
        text(
            f"""
            SELECT 
                c.name as campaign,
                {budget_expr} as daily_budget,
                COALESCE({spend_cents_expr}, 0) / 100.0 as total_spend,
                COALESCE(SUM(p.conversions), 0) as conversions,
                COALESCE(SUM(r.revenue_cents) / 100.0, 0) as revenue,
                CASE 
                    WHEN COALESCE({spend_cents_expr}, 0) > 0
                    THEN ((COALESCE(SUM(r.revenue_cents), 0) - COALESCE({spend_cents_expr}, 0))::float / COALESCE({spend_cents_expr}, 1)) * 100
                    ELSE 0 
                END as roi_percentage
            FROM ad_campaigns c
            LEFT JOIN ad_performance p ON c.id = p.campaign_id {perf_tenant_clause}
            LEFT JOIN (
                SELECT 
                    CASE 
                        WHEN {source_expr} LIKE '%google%' THEN 'Google Ads'
                        WHEN {source_expr} LIKE '%facebook%' THEN 'Facebook'
                        ELSE {source_expr}
                    END as campaign_source,
                    SUM({amount_expr}) * 100.0 as revenue_cents
                FROM revenue_tracking
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' {rt_tenant_clause}
                GROUP BY campaign_source
            ) r ON c.name LIKE '%' || r.campaign_source || '%'
            WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days' {campaign_tenant_clause}
            GROUP BY c.name, {budget_expr}
            ORDER BY roi_percentage DESC
            """
        ),
        {"tenant_id": tenant_uuid}
    ).fetchall()
    
    return {
        "campaigns": [dict(c._mapping) for c in campaigns],
        "best_performer": dict(campaigns[0]._mapping) if campaigns else None,
        "total_roi": sum(c.roi_percentage for c in campaigns) / len(campaigns) if campaigns else 0
    }

@router.get("/customer-ltv")
def get_customer_ltv_analysis(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Customer lifetime value analysis
    """
    tenant_id = current_user.get("tenant_id")
    tenant_uuid = uuid.UUID(tenant_id) if tenant_id else None

    ltv_cols = _get_table_columns(db, "customer_ltv")
    ltv_tenant_clause = _tenant_filter("tenant_id" in ltv_cols, tenant_uuid)

    try:
        ltv_segments = db.execute(
            text(
                """
                SELECT 
                    CASE 
                        WHEN total_revenue_cents >= 100000 THEN 'whale'
                        WHEN total_revenue_cents >= 50000 THEN 'high_value'
                        WHEN total_revenue_cents >= 10000 THEN 'medium_value'
                        ELSE 'low_value'
                    END as segment,
                    COUNT(*) as customer_count,
                    AVG(total_revenue_cents) / 100.0 as avg_ltv,
                    SUM(total_revenue_cents) / 100.0 as total_revenue,
                    AVG(order_count) as avg_orders
                FROM customer_ltv
                WHERE 1=1 {ltv_tenant_clause}
                GROUP BY segment
                ORDER BY avg_ltv DESC
                """
            ),
            {"tenant_id": tenant_uuid}
        ).fetchall()
        
        # Churn risk
        at_risk = db.execute(
            text(
                f"""
                SELECT 
                    COUNT(*) as at_risk_count,
                    AVG(total_revenue_cents) / 100.0 as avg_value
                FROM customer_ltv
                WHERE last_purchase_at < NOW() - INTERVAL '30 days'
                {ltv_tenant_clause}
                """
            ),
            {"tenant_id": tenant_uuid}
        ).fetchone()
        
        return {
            "segments": [dict(s._mapping) for s in ltv_segments],
            "at_risk_customers": dict(at_risk._mapping) if at_risk else {},
            "retention_opportunity": float(at_risk.at_risk_count * at_risk.avg_value) if at_risk and at_risk.avg_value else 0
        }
    except Exception:
        return {"segments": [], "at_risk_customers": {}, "retention_opportunity": 0}

@router.get("/dashboard", response_class=HTMLResponse)
def revenue_dashboard_ui():
    """
    Visual revenue dashboard
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revenue Dashboard - MyRoofGenius</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            @keyframes pulse-green {
                0%, 100% { background-color: #10b981; }
                50% { background-color: #34d399; }
            }
            .pulse-green { animation: pulse-green 2s infinite; }
        </style>
    </head>
    <body class="bg-gray-900 text-white">
        <div class="container mx-auto p-6">
            <!-- Header -->
            <div class="flex justify-between items-center mb-8">
                <h1 class="text-4xl font-bold">💰 Revenue Command Center</h1>
                <div class="text-2xl font-mono" id="clock"></div>
            </div>
            
            <!-- Top KPIs -->
            <div class="grid grid-cols-4 gap-6 mb-8">
                <div class="bg-gray-800 rounded-lg p-6">
                    <div class="text-gray-400 text-sm">Today's Revenue</div>
                    <div class="text-3xl font-bold text-green-400" id="todayRevenue">$0</div>
                    <div class="text-sm text-gray-500" id="todayTrend">Loading...</div>
                </div>
                <div class="bg-gray-800 rounded-lg p-6">
                    <div class="text-gray-400 text-sm">Week Target Progress</div>
                    <div class="text-3xl font-bold text-blue-400" id="weekProgress">0%</div>
                    <div class="w-full bg-gray-700 rounded-full h-2 mt-2">
                        <div class="bg-blue-400 h-2 rounded-full" id="progressBar" style="width: 0%"></div>
                    </div>
                </div>
                <div class="bg-gray-800 rounded-lg p-6">
                    <div class="text-gray-400 text-sm">MRR</div>
                    <div class="text-3xl font-bold text-purple-400" id="mrr">$0</div>
                    <div class="text-sm text-gray-500">Monthly Recurring</div>
                </div>
                <div class="bg-gray-800 rounded-lg p-6">
                    <div class="text-gray-400 text-sm">Hot Leads</div>
                    <div class="text-3xl font-bold text-red-400" id="hotLeads">0</div>
                    <div class="text-sm text-gray-500">Ready to convert</div>
                </div>
            </div>
            
            <!-- Charts Row -->
            <div class="grid grid-cols-2 gap-6 mb-8">
                <!-- Hourly Revenue Chart -->
                <div class="bg-gray-800 rounded-lg p-6">
                    <h3 class="text-xl font-semibold mb-4">Hourly Revenue</h3>
                    <canvas id="hourlyChart"></canvas>
                </div>
                
                <!-- Conversion Funnel -->
                <div class="bg-gray-800 rounded-lg p-6">
                    <h3 class="text-xl font-semibold mb-4">Conversion Funnel</h3>
                    <canvas id="funnelChart"></canvas>
                </div>
            </div>
            
            <!-- Live Feed -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-xl font-semibold mb-4">🔴 Live Revenue Feed</h3>
                <div id="liveFeed" class="space-y-2 max-h-64 overflow-y-auto">
                    <!-- Live events will be inserted here -->
                </div>
            </div>
            
            <!-- Recommendations -->
            <div class="bg-yellow-900 bg-opacity-50 rounded-lg p-6 mt-6">
                <h3 class="text-xl font-semibold mb-4 text-yellow-400">⚡ Action Required</h3>
                <div id="recommendations" class="space-y-2">
                    <!-- Recommendations will be inserted here -->
                </div>
            </div>
        </div>
        
        <script>
            // Update clock
            setInterval(() => {
                document.getElementById('clock').innerText = new Date().toLocaleTimeString();
            }, 1000);
            
            // Fetch and update dashboard data
            async function updateDashboard() {
                const response = await fetch('/api/v1/revenue/dashboard-metrics');
                const data = await response.json();
                
                // Update KPIs
                document.getElementById('todayRevenue').innerText = '$' + data.current_metrics.today.revenue.toFixed(2);
                document.getElementById('weekProgress').innerText = data.targets.progress + '%';
                document.getElementById('progressBar').style.width = data.targets.progress + '%';
                document.getElementById('mrr').innerText = '$' + data.current_metrics.mrr.toFixed(2);
                document.getElementById('hotLeads').innerText = data.lead_metrics.hot_leads || 0;
                
                // Update recommendations
                const recsDiv = document.getElementById('recommendations');
                recsDiv.innerHTML = data.recommendations.map(rec => 
                    `<div class="flex items-center space-x-2">
                        <span class="text-yellow-400">→</span>
                        <span>${rec.action}: ${rec.suggestion}</span>
                    </div>`
                ).join('');
            }
            
            // Fetch hourly data and create chart
            async function updateHourlyChart() {
                const response = await fetch('/api/v1/revenue/hourly-performance');
                const data = await response.json();
                
                const ctx = document.getElementById('hourlyChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.hourly_data.map(h => h.hour + ':00'),
                        datasets: [{
                            label: 'Revenue',
                            data: data.hourly_data.map(h => h.revenue),
                            borderColor: 'rgb(34, 197, 94)',
                            backgroundColor: 'rgba(34, 197, 94, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: { color: '#9CA3AF' },
                                grid: { color: '#374151' }
                            },
                            x: {
                                ticks: { color: '#9CA3AF' },
                                grid: { color: '#374151' }
                            }
                        }
                    }
                });
            }
            
            // Update live feed
            async function updateLiveFeed() {
                const response = await fetch('/api/v1/revenue/live-feed');
                const data = await response.json();
                
                const feedDiv = document.getElementById('liveFeed');
                feedDiv.innerHTML = data.events.map(event => {
                    const icon = event.type === 'revenue' ? '💵' : '👤';
                    const color = event.type === 'revenue' ? 'text-green-400' : 'text-blue-400';
                    return `
                        <div class="flex justify-between items-center p-2 bg-gray-700 rounded">
                            <div class="flex items-center space-x-2">
                                <span>${icon}</span>
                                <span class="${color}">${event.customer}</span>
                                <span class="text-gray-400">${event.product}</span>
                            </div>
                            <div class="flex items-center space-x-4">
                                <span class="font-bold">$${event.amount}</span>
                                <span class="text-xs text-gray-500">${event.time_ago}</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            // Initial load and refresh
            updateDashboard();
            updateHourlyChart();
            updateLiveFeed();
            
            // Auto-refresh
            setInterval(updateDashboard, 30000);  // Every 30 seconds
            setInterval(updateLiveFeed, 10000);   // Every 10 seconds
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
