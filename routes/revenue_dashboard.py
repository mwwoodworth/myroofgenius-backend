"""
Real-Time Revenue Dashboard
Track every dollar, optimize every metric
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine, text
import os
import json

router = APIRouter(tags=["Revenue Dashboard"])

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
)

def get_db():
    engine = create_engine(DATABASE_URL)
    return engine

@router.get("/dashboard-metrics")
async def get_dashboard_metrics():
    """
    Real-time revenue metrics and KPIs
    """
    with get_db().connect() as conn:
        # Today's revenue
        today_revenue = conn.execute(text("""
            SELECT 
                COALESCE(SUM(amount_cents) / 100.0, 0) as revenue,
                COUNT(DISTINCT customer_email) as customers,
                COUNT(*) as transactions
            FROM revenue_tracking
            WHERE DATE(created_at) = CURRENT_DATE
        """)).fetchone()
        
        # Week to date
        week_revenue = conn.execute(text("""
            SELECT 
                COALESCE(SUM(amount_cents) / 100.0, 0) as revenue,
                COUNT(DISTINCT customer_email) as customers
            FROM revenue_tracking
            WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
        """)).fetchone()
        
        # Month to date
        month_revenue = conn.execute(text("""
            SELECT 
                COALESCE(SUM(amount_cents) / 100.0, 0) as revenue,
                COUNT(DISTINCT customer_email) as customers
            FROM revenue_tracking
            WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
        """)).fetchone()
        
        # MRR calculation
        mrr = conn.execute(text("""
            SELECT COALESCE(SUM(
                CASE 
                    WHEN plan_tier = 'basic' THEN 4999
                    WHEN plan_tier = 'pro' THEN 9999
                    WHEN plan_tier = 'enterprise' THEN 49900
                    ELSE 0
                END
            ) / 100.0, 0) as mrr
            FROM subscriptions
            WHERE status = 'active'
        """)).scalar()
        
        # Lead metrics
        lead_metrics = conn.execute(text("""
            SELECT 
                COUNT(*) as total_leads,
                COUNT(CASE WHEN segment = 'hot' THEN 1 END) as hot_leads,
                COUNT(CASE WHEN converted = true THEN 1 END) as converted,
                AVG(score) as avg_score
            FROM leads
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
        """)).fetchone()
        
        # Conversion funnel
        funnel = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN email END) as leads,
                COUNT(DISTINCT CASE WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' AND score >= 60 THEN email END) as qualified,
                COUNT(DISTINCT CASE WHEN status = 'trialing' THEN customer_email END) as trials,
                COUNT(DISTINCT CASE WHEN status = 'active' THEN customer_email END) as paid
            FROM (
                SELECT email, score, NULL as customer_email, NULL as status, created_at FROM leads
                UNION ALL
                SELECT NULL, NULL, customer_email, status, created_at FROM subscriptions
            ) combined
        """)).fetchone()
        
        # Revenue by source
        revenue_sources = conn.execute(text("""
            SELECT 
                source,
                COUNT(*) as transactions,
                SUM(amount_cents) / 100.0 as revenue
            FROM revenue_tracking
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY source
            ORDER BY revenue DESC
        """)).fetchall()
        
        # Calculate progress toward targets
        days_into_week = (datetime.utcnow().weekday() + 1)
        week_1_target = 2500
        week_2_target = 7500
        week_4_target = 25000
        
        current_week = (datetime.utcnow() - datetime(2025, 8, 18)).days // 7 + 1
        
        if current_week == 1:
            target = week_1_target
            progress = (week_revenue["revenue"] / target * 100) if target > 0 else 0
        elif current_week == 2:
            target = week_2_target
            progress = (week_revenue["revenue"] / target * 100) if target > 0 else 0
        else:
            target = week_4_target
            progress = (month_revenue["revenue"] / target * 100) if target > 0 else 0
        
        return {
            "current_metrics": {
                "today": {
                    "revenue": today_revenue["revenue"],
                    "customers": today_revenue["customers"],
                    "transactions": today_revenue["transactions"],
                    "avg_order_value": today_revenue["revenue"] / today_revenue["transactions"] if today_revenue["transactions"] > 0 else 0
                },
                "week_to_date": {
                    "revenue": week_revenue["revenue"],
                    "customers": week_revenue["customers"]
                },
                "month_to_date": {
                    "revenue": month_revenue["revenue"],
                    "customers": month_revenue["customers"]
                },
                "mrr": mrr
            },
            "targets": {
                "current_week": current_week,
                "target": target,
                "progress": round(progress, 2),
                "remaining": max(0, target - week_revenue["revenue"]),
                "daily_needed": max(0, (target - week_revenue["revenue"]) / (7 - days_into_week)) if days_into_week < 7 else 0
            },
            "lead_metrics": dict(lead_metrics._mapping) if lead_metrics else {},
            "conversion_funnel": dict(funnel._mapping) if funnel else {},
            "revenue_by_source": [dict(s._mapping) for s in revenue_sources],
            "recommendations": generate_revenue_recommendations(week_revenue["revenue"], target, lead_metrics)
        }

def generate_revenue_recommendations(current_revenue, target, lead_metrics):
    """Generate actionable recommendations based on performance"""
    recommendations = []
    
    gap = target - current_revenue
    if gap > 0:
        recommendations.append({
            "priority": "high",
            "action": f"Need ${gap:.2f} more to hit target",
            "suggestion": "Increase ad spend and launch flash promotion"
        })
    
    if lead_metrics and lead_metrics["hot_leads"] < 10:
        recommendations.append({
            "priority": "high",
            "action": "Low hot lead count",
            "suggestion": "Increase urgency messaging in ads"
        })
    
    if lead_metrics and lead_metrics["avg_score"] < 60:
        recommendations.append({
            "priority": "medium",
            "action": "Lead quality below target",
            "suggestion": "Refine targeting and qualify better"
        })
    
    return recommendations

@router.get("/live-feed")
async def get_live_revenue_feed():
    """
    Real-time feed of revenue events
    """
    with get_db().connect() as conn:
        events = conn.execute(text("""
            SELECT 
                'revenue' as type,
                customer_email,
                amount_cents / 100.0 as amount,
                source,
                product_name,
                created_at
            FROM revenue_tracking
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            
            UNION ALL
            
            SELECT 
                'lead' as type,
                email as customer_email,
                score as amount,
                source,
                segment as product_name,
                created_at
            FROM leads
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            
            ORDER BY created_at DESC
            LIMIT 50
        """)).fetchall()
        
        return {
            "events": [
                {
                    "type": e["type"],
                    "customer": e["customer_email"][:3] + "***" if e["customer_email"] else "Anonymous",
                    "amount": e["amount"],
                    "source": e["source"],
                    "product": e["product_name"],
                    "time_ago": format_time_ago(e["created_at"])
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
async def get_hourly_performance():
    """
    Hourly revenue performance for today
    """
    with get_db().connect() as conn:
        hourly = conn.execute(text("""
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as transactions,
                SUM(amount_cents) / 100.0 as revenue,
                COUNT(DISTINCT customer_email) as unique_customers
            FROM revenue_tracking
            WHERE DATE(created_at) = CURRENT_DATE
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
        """)).fetchall()
        
        # Fill in missing hours
        hourly_data = {int(h["hour"]): dict(h._mapping) for h in hourly}
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
async def get_campaign_roi():
    """
    ROI analysis by marketing campaign
    """
    with get_db().connect() as conn:
        campaigns = conn.execute(text("""
            SELECT 
                c.name as campaign,
                c.budget_daily_cents / 100.0 as daily_budget,
                COALESCE(SUM(p.spend_cents) / 100.0, 0) as total_spend,
                COALESCE(SUM(p.conversions), 0) as conversions,
                COALESCE(SUM(r.revenue_cents) / 100.0, 0) as revenue,
                CASE 
                    WHEN SUM(p.spend_cents) > 0 
                    THEN ((SUM(r.revenue_cents) - SUM(p.spend_cents))::float / SUM(p.spend_cents)) * 100
                    ELSE 0 
                END as roi_percentage
            FROM ad_campaigns c
            LEFT JOIN ad_performance p ON c.campaign_id = p.campaign_id
            LEFT JOIN (
                SELECT 
                    CASE 
                        WHEN source LIKE '%google%' THEN 'Google Ads'
                        WHEN source LIKE '%facebook%' THEN 'Facebook'
                        ELSE source 
                    END as campaign_source,
                    SUM(amount_cents) as revenue_cents
                FROM revenue_tracking
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY campaign_source
            ) r ON c.name LIKE '%' || r.campaign_source || '%'
            WHERE c.created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY c.name, c.budget_daily_cents
            ORDER BY roi_percentage DESC
        """)).fetchall()
        
        return {
            "campaigns": [dict(c._mapping) for c in campaigns],
            "best_performer": dict(campaigns[0]._mapping) if campaigns else None,
            "total_roi": sum(c["roi_percentage"] for c in campaigns) / len(campaigns) if campaigns else 0
        }

@router.get("/customer-ltv")
async def get_customer_ltv_analysis():
    """
    Customer lifetime value analysis
    """
    with get_db().connect() as conn:
        ltv_segments = conn.execute(text("""
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
            GROUP BY segment
            ORDER BY avg_ltv DESC
        """)).fetchall()
        
        # Churn risk
        at_risk = conn.execute(text("""
            SELECT 
                COUNT(*) as at_risk_count,
                AVG(total_revenue_cents) / 100.0 as avg_value
            FROM customer_ltv
            WHERE churn_risk_score > 0.7
            AND last_purchase_at < NOW() - INTERVAL '30 days'
        """)).fetchone()
        
        return {
            "segments": [dict(s._mapping) for s in ltv_segments],
            "at_risk_customers": dict(at_risk._mapping) if at_risk else {},
            "retention_opportunity": at_risk["at_risk_count"] * at_risk["avg_value"] if at_risk and at_risk["avg_value"] else 0
        }

@router.get("/dashboard", response_class=HTMLResponse)
async def revenue_dashboard_ui():
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