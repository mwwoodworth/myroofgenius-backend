"""
Job Analytics and Insights
Provides analytical insights and metrics for jobs
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from pydantic import BaseModel, Field

router = APIRouter(prefix="/analytics")

# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class MetricType(str, Enum):
    COMPLETION_RATE = "completion_rate"
    AVERAGE_DURATION = "average_duration"
    COST_VARIANCE = "cost_variance"
    PROFIT_MARGIN = "profit_margin"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    ON_TIME_DELIVERY = "on_time_delivery"
    RESOURCE_UTILIZATION = "resource_utilization"
    TASK_EFFICIENCY = "task_efficiency"

class TrendPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class AnalyticsFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[List[str]] = None
    customer_id: Optional[str] = None
    crew_id: Optional[str] = None
    job_type: Optional[str] = None

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/overview", response_model=Dict[str, Any])
async def get_analytics_overview(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get comprehensive analytics overview"""
    try:
        # Default to last 30 days if no date range provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        # Get job statistics
        job_stats = db.execute(
            text("""
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
                    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_jobs,
                    COUNT(*) FILTER (WHERE status = 'scheduled') as scheduled_jobs,
                    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_jobs,
                    AVG(EXTRACT(DAY FROM (completed_date - created_at))) as avg_duration_days,
                    COUNT(*) FILTER (WHERE completed_date <= scheduled_end) as on_time_count,
                    COUNT(*) FILTER (WHERE completed_date > scheduled_end) as delayed_count
                FROM jobs
                WHERE created_at BETWEEN :start_date AND :end_date
            """),
            params
        ).fetchone()

        # Get financial metrics
        financial = db.execute(
            text("""
                SELECT
                    COALESCE(SUM(estimated_revenue), 0) as total_estimated_revenue,
                    COALESCE(SUM(actual_revenue), 0) as total_actual_revenue,
                    COALESCE(SUM(estimated_cost), 0) as total_estimated_cost,
                    COALESCE(SUM(actual_cost), 0) as total_actual_cost,
                    COALESCE(AVG(
                        CASE
                            WHEN actual_revenue > 0
                            THEN ((actual_revenue - actual_cost) / actual_revenue) * 100
                            ELSE 0
                        END
                    ), 0) as avg_profit_margin,
                    COALESCE(AVG(
                        CASE
                            WHEN estimated_cost > 0
                            THEN ((actual_cost - estimated_cost) / estimated_cost) * 100
                            ELSE 0
                        END
                    ), 0) as avg_cost_variance
                FROM jobs
                WHERE created_at BETWEEN :start_date AND :end_date
            """),
            params
        ).fetchone()

        # Get customer metrics
        customer_metrics = db.execute(
            text("""
                SELECT
                    COUNT(DISTINCT customer_id) as unique_customers,
                    COUNT(*) / NULLIF(COUNT(DISTINCT customer_id), 0) as avg_jobs_per_customer,
                    COUNT(*) FILTER (WHERE customer_rating >= 4) as satisfied_customers,
                    AVG(customer_rating) as avg_customer_rating
                FROM jobs
                WHERE created_at BETWEEN :start_date AND :end_date
            """),
            params
        ).fetchone()

        # Get resource utilization
        resource_stats = db.execute(
            text("""
                SELECT
                    COUNT(DISTINCT crew_id) as active_crews,
                    COUNT(DISTINCT assigned_to) as active_employees,
                    AVG(
                        CASE
                            WHEN scheduled_hours > 0
                            THEN (actual_hours / scheduled_hours) * 100
                            ELSE 0
                        END
                    ) as avg_resource_utilization
                FROM jobs
                WHERE created_at BETWEEN :start_date AND :end_date
            """),
            params
        ).fetchone()

        # Calculate key metrics
        completion_rate = (job_stats.completed_jobs / job_stats.total_jobs * 100) if job_stats.total_jobs > 0 else 0
        on_time_rate = (job_stats.on_time_count / (job_stats.on_time_count + job_stats.delayed_count) * 100) if (job_stats.on_time_count + job_stats.delayed_count) > 0 else 0
        satisfaction_rate = (customer_metrics.satisfied_customers / job_stats.total_jobs * 100) if job_stats.total_jobs > 0 else 0

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "job_metrics": {
                "total_jobs": job_stats.total_jobs,
                "completed": job_stats.completed_jobs,
                "in_progress": job_stats.in_progress_jobs,
                "scheduled": job_stats.scheduled_jobs,
                "cancelled": job_stats.cancelled_jobs,
                "completion_rate": round(completion_rate, 2),
                "avg_duration_days": round(job_stats.avg_duration_days or 0, 1),
                "on_time_delivery_rate": round(on_time_rate, 2)
            },
            "financial_metrics": {
                "total_estimated_revenue": float(financial.total_estimated_revenue),
                "total_actual_revenue": float(financial.total_actual_revenue),
                "total_estimated_cost": float(financial.total_estimated_cost),
                "total_actual_cost": float(financial.total_actual_cost),
                "avg_profit_margin": round(financial.avg_profit_margin, 2),
                "avg_cost_variance": round(financial.avg_cost_variance, 2),
                "total_profit": float(financial.total_actual_revenue - financial.total_actual_cost)
            },
            "customer_metrics": {
                "unique_customers": customer_metrics.unique_customers,
                "avg_jobs_per_customer": round(customer_metrics.avg_jobs_per_customer or 0, 1),
                "satisfaction_rate": round(satisfaction_rate, 2),
                "avg_rating": round(customer_metrics.avg_customer_rating or 0, 1)
            },
            "resource_metrics": {
                "active_crews": resource_stats.active_crews,
                "active_employees": resource_stats.active_employees,
                "utilization_rate": round(resource_stats.avg_resource_utilization or 0, 2)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics overview: {str(e)}"
        )

@router.get("/trends", response_model=Dict[str, Any])
async def get_trend_analysis(
    metric: MetricType,
    period: TrendPeriod = TrendPeriod.MONTHLY,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get trend analysis for specific metrics"""
    try:
        # Default to last 6 months if no date range provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=180)

        # Determine grouping based on period
        date_trunc = {
            TrendPeriod.DAILY: "day",
            TrendPeriod.WEEKLY: "week",
            TrendPeriod.MONTHLY: "month",
            TrendPeriod.QUARTERLY: "quarter",
            TrendPeriod.YEARLY: "year"
        }[period]

        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        # Build query based on metric type
        if metric == MetricType.COMPLETION_RATE:
            query = f"""
                SELECT
                    DATE_TRUNC('{date_trunc}', created_at) as period,
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    (COUNT(*) FILTER (WHERE status = 'completed')::float / NULLIF(COUNT(*), 0)) * 100 as metric_value
                FROM jobs
                WHERE created_at BETWEEN :start_date AND :end_date
                GROUP BY DATE_TRUNC('{date_trunc}', created_at)
                ORDER BY period
            """
        elif metric == MetricType.AVERAGE_DURATION:
            query = f"""
                SELECT
                    DATE_TRUNC('{date_trunc}', created_at) as period,
                    COUNT(*) as total_jobs,
                    AVG(EXTRACT(DAY FROM (completed_date - created_at))) as metric_value
                FROM jobs
                WHERE created_at BETWEEN :start_date AND :end_date
                    AND completed_date IS NOT NULL
                GROUP BY DATE_TRUNC('{date_trunc}', created_at)
                ORDER BY period
            """
        elif metric == MetricType.PROFIT_MARGIN:
            query = f"""
                SELECT
                    DATE_TRUNC('{date_trunc}', created_at) as period,
                    COUNT(*) as total_jobs,
                    AVG(
                        CASE
                            WHEN actual_revenue > 0
                            THEN ((actual_revenue - actual_cost) / actual_revenue) * 100
                            ELSE 0
                        END
                    ) as metric_value
                FROM jobs
                WHERE created_at BETWEEN :start_date AND :end_date
                GROUP BY DATE_TRUNC('{date_trunc}', created_at)
                ORDER BY period
            """
        elif metric == MetricType.ON_TIME_DELIVERY:
            query = f"""
                SELECT
                    DATE_TRUNC('{date_trunc}', created_at) as period,
                    COUNT(*) as total_jobs,
                    (COUNT(*) FILTER (WHERE completed_date <= scheduled_end)::float /
                     NULLIF(COUNT(*) FILTER (WHERE completed_date IS NOT NULL), 0)) * 100 as metric_value
                FROM jobs
                WHERE created_at BETWEEN :start_date AND :end_date
                GROUP BY DATE_TRUNC('{date_trunc}', created_at)
                ORDER BY period
            """
        else:
            # Default to cost variance
            query = f"""
                SELECT
                    DATE_TRUNC('{date_trunc}', created_at) as period,
                    COUNT(*) as total_jobs,
                    AVG(
                        CASE
                            WHEN estimated_cost > 0
                            THEN ((actual_cost - estimated_cost) / estimated_cost) * 100
                            ELSE 0
                        END
                    ) as metric_value
                FROM jobs
                WHERE created_at BETWEEN :start_date AND :end_date
                GROUP BY DATE_TRUNC('{date_trunc}', created_at)
                ORDER BY period
            """

        result = db.execute(text(query), params)

        data_points = []
        for row in result:
            data_points.append({
                "period": row.period.isoformat(),
                "value": round(row.metric_value or 0, 2),
                "total_jobs": row.total_jobs
            })

        # Calculate trend direction
        if len(data_points) >= 2:
            first_value = data_points[0]["value"]
            last_value = data_points[-1]["value"]
            trend_direction = "up" if last_value > first_value else "down" if last_value < first_value else "stable"
            trend_percentage = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
        else:
            trend_direction = "insufficient_data"
            trend_percentage = 0

        return {
            "metric": metric.value,
            "period_type": period.value,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "data_points": data_points,
            "trend": {
                "direction": trend_direction,
                "percentage_change": round(trend_percentage, 2)
            },
            "summary": {
                "total_periods": len(data_points),
                "average_value": round(sum(p["value"] for p in data_points) / len(data_points), 2) if data_points else 0,
                "min_value": min((p["value"] for p in data_points), default=0),
                "max_value": max((p["value"] for p in data_points), default=0)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trend analysis: {str(e)}"
        )

@router.get("/performance/crews", response_model=Dict[str, Any])
async def get_crew_performance(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get performance metrics by crew"""
    try:
        # Default to last 30 days
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        result = db.execute(
            text("""
                SELECT
                    c.id as crew_id,
                    c.name as crew_name,
                    COUNT(j.id) as total_jobs,
                    COUNT(j.id) FILTER (WHERE j.status = 'completed') as completed_jobs,
                    AVG(EXTRACT(DAY FROM (j.completed_date - j.created_at))) as avg_completion_time,
                    COUNT(j.id) FILTER (WHERE j.completed_date <= j.scheduled_end) as on_time_jobs,
                    AVG(j.customer_rating) as avg_rating,
                    SUM(j.actual_revenue) as total_revenue,
                    SUM(j.actual_revenue - j.actual_cost) as total_profit,
                    AVG(
                        CASE
                            WHEN j.actual_revenue > 0
                            THEN ((j.actual_revenue - j.actual_cost) / j.actual_revenue) * 100
                            ELSE 0
                        END
                    ) as avg_profit_margin
                FROM crews c
                LEFT JOIN jobs j ON c.id = j.crew_id
                    AND j.created_at BETWEEN :start_date AND :end_date
                GROUP BY c.id, c.name
                HAVING COUNT(j.id) > 0
                ORDER BY total_jobs DESC
                LIMIT :limit
            """),
            {
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit
            }
        )

        crews = []
        for row in result:
            on_time_rate = (row.on_time_jobs / row.completed_jobs * 100) if row.completed_jobs > 0 else 0
            completion_rate = (row.completed_jobs / row.total_jobs * 100) if row.total_jobs > 0 else 0

            crews.append({
                "crew_id": str(row.crew_id),
                "crew_name": row.crew_name,
                "metrics": {
                    "total_jobs": row.total_jobs,
                    "completed_jobs": row.completed_jobs,
                    "completion_rate": round(completion_rate, 2),
                    "avg_completion_time_days": round(row.avg_completion_time or 0, 1),
                    "on_time_rate": round(on_time_rate, 2),
                    "avg_customer_rating": round(row.avg_rating or 0, 1),
                    "total_revenue": float(row.total_revenue or 0),
                    "total_profit": float(row.total_profit or 0),
                    "profit_margin": round(row.avg_profit_margin or 0, 2)
                }
            })

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "crews": crews,
            "count": len(crews)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get crew performance: {str(e)}"
        )

@router.get("/performance/employees", response_model=Dict[str, Any])
async def get_employee_performance(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get performance metrics by employee"""
    try:
        # Default to last 30 days
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        result = db.execute(
            text("""
                SELECT
                    u.id as employee_id,
                    u.email as employee_email,
                    u.full_name as employee_name,
                    COUNT(j.id) as total_jobs,
                    COUNT(j.id) FILTER (WHERE j.status = 'completed') as completed_jobs,
                    COUNT(DISTINCT jt.id) as total_tasks,
                    COUNT(DISTINCT jt.id) FILTER (WHERE jt.is_complete = true) as completed_tasks,
                    SUM(jt.estimated_hours) as total_hours,
                    AVG(j.customer_rating) as avg_rating
                FROM users u
                LEFT JOIN jobs j ON u.id = j.assigned_to
                    AND j.created_at BETWEEN :start_date AND :end_date
                LEFT JOIN job_tasks jt ON u.id = jt.assigned_to
                    AND jt.created_at BETWEEN :start_date AND :end_date
                WHERE u.role IN ('technician', 'supervisor', 'manager')
                GROUP BY u.id, u.email, u.full_name
                HAVING COUNT(j.id) > 0 OR COUNT(jt.id) > 0
                ORDER BY total_jobs DESC
                LIMIT :limit
            """),
            {
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit
            }
        )

        employees = []
        for row in result:
            job_completion_rate = (row.completed_jobs / row.total_jobs * 100) if row.total_jobs > 0 else 0
            task_completion_rate = (row.completed_tasks / row.total_tasks * 100) if row.total_tasks > 0 else 0

            employees.append({
                "employee_id": str(row.employee_id),
                "employee_email": row.employee_email,
                "employee_name": row.employee_name,
                "metrics": {
                    "total_jobs": row.total_jobs,
                    "completed_jobs": row.completed_jobs,
                    "job_completion_rate": round(job_completion_rate, 2),
                    "total_tasks": row.total_tasks,
                    "completed_tasks": row.completed_tasks,
                    "task_completion_rate": round(task_completion_rate, 2),
                    "total_hours": float(row.total_hours or 0),
                    "avg_customer_rating": round(row.avg_rating or 0, 1)
                }
            })

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "employees": employees,
            "count": len(employees)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get employee performance: {str(e)}"
        )

@router.get("/customer-insights", response_model=Dict[str, Any])
async def get_customer_insights(
    customer_id: Optional[str] = None,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get insights about customer behavior and patterns"""
    try:
        # Default to last 90 days
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        # Build query
        base_query = """
            SELECT
                c.id as customer_id,
                c.name as customer_name,
                COUNT(j.id) as total_jobs,
                COUNT(j.id) FILTER (WHERE j.status = 'completed') as completed_jobs,
                MIN(j.created_at) as first_job_date,
                MAX(j.created_at) as last_job_date,
                AVG(j.customer_rating) as avg_rating,
                SUM(j.actual_revenue) as total_revenue,
                AVG(j.actual_revenue) as avg_job_value,
                STRING_AGG(DISTINCT j.job_type, ', ') as job_types,
                COUNT(j.id) FILTER (WHERE j.is_recurring = true) as recurring_jobs,
                EXTRACT(DAY FROM (MAX(j.created_at) - MIN(j.created_at))) / NULLIF(COUNT(j.id) - 1, 0) as avg_days_between_jobs
            FROM customers c
            LEFT JOIN jobs j ON c.id = j.customer_id
                AND j.created_at BETWEEN :start_date AND :end_date
        """

        if customer_id:
            base_query += " WHERE c.id = :customer_id"
            params["customer_id"] = customer_id

        base_query += " GROUP BY c.id, c.name"

        if not customer_id:
            base_query += " HAVING COUNT(j.id) > 0 ORDER BY total_revenue DESC LIMIT 20"

        result = db.execute(text(base_query), params)

        customers = []
        for row in result:
            # Calculate customer lifetime value prediction
            if row.avg_days_between_jobs and row.avg_days_between_jobs > 0:
                predicted_jobs_per_year = 365 / row.avg_days_between_jobs
                predicted_annual_value = predicted_jobs_per_year * (row.avg_job_value or 0)
            else:
                predicted_annual_value = row.avg_job_value or 0

            customers.append({
                "customer_id": str(row.customer_id),
                "customer_name": row.customer_name,
                "summary": {
                    "total_jobs": row.total_jobs,
                    "completed_jobs": row.completed_jobs,
                    "first_job_date": row.first_job_date.isoformat() if row.first_job_date else None,
                    "last_job_date": row.last_job_date.isoformat() if row.last_job_date else None,
                    "avg_rating": round(row.avg_rating or 0, 1),
                    "total_revenue": float(row.total_revenue or 0),
                    "avg_job_value": float(row.avg_job_value or 0),
                    "job_types": row.job_types or "",
                    "recurring_jobs": row.recurring_jobs,
                    "avg_days_between_jobs": round(row.avg_days_between_jobs or 0, 1),
                    "predicted_annual_value": round(predicted_annual_value, 2)
                }
            })

        # Get overall insights
        overall = db.execute(
            text("""
                SELECT
                    COUNT(DISTINCT c.id) as total_customers,
                    COUNT(DISTINCT c.id) FILTER (WHERE job_count > 1) as repeat_customers,
                    AVG(job_count) as avg_jobs_per_customer,
                    AVG(total_revenue) as avg_customer_value
                FROM (
                    SELECT
                        c.id,
                        COUNT(j.id) as job_count,
                        SUM(j.actual_revenue) as total_revenue
                    FROM customers c
                    LEFT JOIN jobs j ON c.id = j.customer_id
                        AND j.created_at BETWEEN :start_date AND :end_date
                    GROUP BY c.id
                    HAVING COUNT(j.id) > 0
                ) as customer_stats
            """),
            params
        ).fetchone()

        retention_rate = (overall.repeat_customers / overall.total_customers * 100) if overall.total_customers > 0 else 0

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "overall_insights": {
                "total_customers": overall.total_customers,
                "repeat_customers": overall.repeat_customers,
                "retention_rate": round(retention_rate, 2),
                "avg_jobs_per_customer": round(overall.avg_jobs_per_customer or 0, 1),
                "avg_customer_value": float(overall.avg_customer_value or 0)
            },
            "customers": customers
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer insights: {str(e)}"
        )

@router.get("/predictive/revenue-forecast", response_model=Dict[str, Any])
async def get_revenue_forecast(
    forecast_months: int = Query(3, ge=1, le=12),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Generate revenue forecast based on historical data"""
    try:
        # Get historical revenue data for trend analysis
        historical = db.execute(
            text("""
                SELECT
                    DATE_TRUNC('month', created_at) as month,
                    COUNT(*) as job_count,
                    SUM(actual_revenue) as total_revenue,
                    AVG(actual_revenue) as avg_revenue
                FROM jobs
                WHERE created_at >= NOW() - INTERVAL '12 months'
                    AND actual_revenue IS NOT NULL
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month
            """)
        )

        historical_data = []
        for row in historical:
            historical_data.append({
                "month": row.month.isoformat(),
                "job_count": row.job_count,
                "total_revenue": float(row.total_revenue or 0),
                "avg_revenue": float(row.avg_revenue or 0)
            })

        if len(historical_data) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient historical data for forecasting"
            )

        # Simple linear regression for forecasting
        # Calculate growth rate
        recent_months = historical_data[-3:]
        growth_rate = 0
        if len(recent_months) >= 2:
            first_revenue = recent_months[0]["total_revenue"]
            last_revenue = recent_months[-1]["total_revenue"]
            if first_revenue > 0:
                growth_rate = (last_revenue - first_revenue) / first_revenue / len(recent_months)

        # Generate forecast
        last_month_revenue = historical_data[-1]["total_revenue"]
        last_month_job_count = historical_data[-1]["job_count"]
        forecast = []

        for i in range(1, forecast_months + 1):
            forecast_date = date.today() + timedelta(days=30 * i)
            forecast_revenue = last_month_revenue * (1 + growth_rate * i)
            forecast_jobs = int(last_month_job_count * (1 + growth_rate * i * 0.5))  # Jobs grow slower

            forecast.append({
                "month": forecast_date.strftime("%Y-%m"),
                "predicted_revenue": round(forecast_revenue, 2),
                "predicted_jobs": forecast_jobs,
                "confidence": max(0.5, 0.9 - (i * 0.1))  # Confidence decreases over time
            })

        return {
            "historical_data": historical_data,
            "forecast": forecast,
            "analysis": {
                "monthly_growth_rate": round(growth_rate * 100, 2),
                "forecast_period_months": forecast_months,
                "total_predicted_revenue": round(sum(f["predicted_revenue"] for f in forecast), 2),
                "total_predicted_jobs": sum(f["predicted_jobs"] for f in forecast)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate revenue forecast: {str(e)}"
        )