"""
Job Reports Generation
Comprehensive reporting for job analytics and insights
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
import json
import csv
import io

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from pydantic import BaseModel, Field

router = APIRouter(prefix="/reports")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ReportFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    customer_id: Optional[str] = None
    crew_id: Optional[str] = None
    job_type: Optional[str] = None

# ============================================================================
# JOB REPORTS ENDPOINTS
# ============================================================================

@router.get("/summary")
async def get_jobs_summary_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    group_by: str = Query("month", pattern="^(day|week|month|quarter|year)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary report of jobs over time"""
    try:
        # Default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Determine date truncation based on grouping
        date_trunc = {
            "day": "day",
            "week": "week",
            "month": "month",
            "quarter": "quarter",
            "year": "year"
        }[group_by]

        result = db.execute(
            text(f"""
                SELECT
                    DATE_TRUNC(:date_trunc, created_at) as period,
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
                    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_jobs,
                    COUNT(*) FILTER (WHERE status = 'scheduled') as scheduled_jobs,
                    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_jobs,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(AVG(total_amount), 0) as avg_job_value,
                    COALESCE(SUM(total_amount) FILTER (WHERE status = 'completed'), 0) as completed_revenue
                FROM jobs
                WHERE DATE(created_at) BETWEEN :start_date AND :end_date
                GROUP BY DATE_TRUNC(:date_trunc, created_at)
                ORDER BY period DESC
            """),
            {
                "date_trunc": date_trunc,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        periods = []
        for row in result:
            periods.append({
                "period": row.period.isoformat(),
                "total_jobs": row.total_jobs,
                "completed_jobs": row.completed_jobs,
                "in_progress_jobs": row.in_progress_jobs,
                "scheduled_jobs": row.scheduled_jobs,
                "cancelled_jobs": row.cancelled_jobs,
                "total_revenue": float(row.total_revenue),
                "avg_job_value": float(row.avg_job_value),
                "completed_revenue": float(row.completed_revenue),
                "completion_rate": round(row.completed_jobs / row.total_jobs * 100, 1) if row.total_jobs > 0 else 0
            })

        # Get overall statistics
        overall = db.execute(
            text("""
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(AVG(total_amount), 0) as avg_job_value,
                    COALESCE(AVG(
                        EXTRACT(epoch FROM (actual_end - actual_start)) / 3600
                    ) FILTER (WHERE status = 'completed'), 0) as avg_completion_hours
                FROM jobs
                WHERE DATE(created_at) BETWEEN :start_date AND :end_date
            """),
            {"start_date": start_date, "end_date": end_date}
        ).fetchone()

        return {
            "period_data": periods,
            "summary": {
                "total_jobs": overall.total_jobs,
                "completed_jobs": overall.completed_jobs,
                "total_revenue": float(overall.total_revenue),
                "avg_job_value": float(overall.avg_job_value),
                "avg_completion_hours": float(overall.avg_completion_hours),
                "completion_rate": round(overall.completed_jobs / overall.total_jobs * 100, 1) if overall.total_jobs > 0 else 0
            },
            "filters": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "group_by": group_by
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary report: {str(e)}"
        )

@router.get("/performance")
async def get_performance_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics report"""
    try:
        # Default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get crew performance
        crew_result = db.execute(
            text("""
                SELECT
                    j.assigned_crew_id,
                    c.name as crew_name,
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE j.status = 'completed') as completed_jobs,
                    COALESCE(AVG(
                        EXTRACT(epoch FROM (j.actual_end - j.actual_start)) / 3600
                    ) FILTER (WHERE j.status = 'completed'), 0) as avg_completion_hours,
                    COALESCE(SUM(j.total_amount), 0) as total_revenue,
                    COALESCE(AVG(j.total_amount), 0) as avg_revenue_per_job
                FROM jobs j
                LEFT JOIN crews c ON j.assigned_crew_id = c.id
                WHERE DATE(j.created_at) BETWEEN :start_date AND :end_date
                    AND j.assigned_crew_id IS NOT NULL
                GROUP BY j.assigned_crew_id, c.name
                ORDER BY completed_jobs DESC
            """),
            {"start_date": start_date, "end_date": end_date}
        )

        crew_performance = []
        for crew in crew_result:
            crew_performance.append({
                "crew_id": str(crew.assigned_crew_id),
                "crew_name": crew.crew_name,
                "total_jobs": crew.total_jobs,
                "completed_jobs": crew.completed_jobs,
                "avg_completion_hours": float(crew.avg_completion_hours),
                "total_revenue": float(crew.total_revenue),
                "avg_revenue_per_job": float(crew.avg_revenue_per_job),
                "completion_rate": round(crew.completed_jobs / crew.total_jobs * 100, 1) if crew.total_jobs > 0 else 0
            })

        # Get employee performance
        employee_result = db.execute(
            text("""
                SELECT
                    ej.employee_id,
                    e.first_name || ' ' || e.last_name as employee_name,
                    COUNT(DISTINCT ej.job_id) as total_jobs,
                    COALESCE(SUM(ej.hours_worked), 0) as total_hours,
                    COALESCE(AVG(ej.hours_worked), 0) as avg_hours_per_job,
                    COUNT(DISTINCT ej.job_id) FILTER (
                        WHERE EXISTS (
                            SELECT 1 FROM jobs j
                            WHERE j.id = ej.job_id AND j.status = 'completed'
                        )
                    ) as completed_jobs
                FROM employee_jobs ej
                LEFT JOIN employees e ON ej.employee_id = e.id
                WHERE DATE(ej.assigned_at) BETWEEN :start_date AND :end_date
                GROUP BY ej.employee_id, e.first_name, e.last_name
                ORDER BY total_jobs DESC
                LIMIT 20
            """),
            {"start_date": start_date, "end_date": end_date}
        )

        employee_performance = []
        for emp in employee_result:
            employee_performance.append({
                "employee_id": str(emp.employee_id),
                "employee_name": emp.employee_name,
                "total_jobs": emp.total_jobs,
                "total_hours": float(emp.total_hours),
                "avg_hours_per_job": float(emp.avg_hours_per_job),
                "completed_jobs": emp.completed_jobs
            })

        # Get job type performance
        type_result = db.execute(
            text("""
                SELECT
                    job_type,
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
                    COALESCE(AVG(total_amount), 0) as avg_revenue,
                    COALESCE(AVG(
                        EXTRACT(epoch FROM (actual_end - actual_start)) / 3600
                    ) FILTER (WHERE status = 'completed'), 0) as avg_completion_hours
                FROM jobs
                WHERE DATE(created_at) BETWEEN :start_date AND :end_date
                    AND job_type IS NOT NULL
                GROUP BY job_type
                ORDER BY total_jobs DESC
            """),
            {"start_date": start_date, "end_date": end_date}
        )

        job_type_performance = []
        for jt in type_result:
            job_type_performance.append({
                "job_type": jt.job_type,
                "total_jobs": jt.total_jobs,
                "completed_jobs": jt.completed_jobs,
                "avg_revenue": float(jt.avg_revenue),
                "avg_completion_hours": float(jt.avg_completion_hours),
                "completion_rate": round(jt.completed_jobs / jt.total_jobs * 100, 1) if jt.total_jobs > 0 else 0
            })

        return {
            "crew_performance": crew_performance,
            "employee_performance": employee_performance,
            "job_type_performance": job_type_performance,
            "filters": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate performance report: {str(e)}"
        )

@router.get("/financial")
async def get_financial_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get financial report for jobs"""
    try:
        # Default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        # Revenue breakdown by status
        revenue_result = db.execute(
            text("""
                SELECT
                    status,
                    COUNT(*) as job_count,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(SUM(estimated_cost), 0) as total_estimated_cost,
                    COALESCE(SUM(actual_cost), 0) as total_actual_cost
                FROM jobs
                WHERE DATE(created_at) BETWEEN :start_date AND :end_date
                GROUP BY status
                ORDER BY total_revenue DESC
            """),
            {"start_date": start_date, "end_date": end_date}
        )

        revenue_by_status = []
        total_revenue = 0
        total_estimated_cost = 0
        total_actual_cost = 0

        for rev in revenue_result:
            revenue_by_status.append({
                "status": rev.status,
                "job_count": rev.job_count,
                "total_revenue": float(rev.total_revenue),
                "total_estimated_cost": float(rev.total_estimated_cost),
                "total_actual_cost": float(rev.total_actual_cost),
                "profit_margin": round(
                    (rev.total_revenue - rev.total_actual_cost) / rev.total_revenue * 100, 1
                ) if rev.total_revenue > 0 else 0
            })
            total_revenue += rev.total_revenue
            total_estimated_cost += rev.total_estimated_cost
            total_actual_cost += rev.total_actual_cost

        # Cost breakdown
        cost_result = db.execute(
            text("""
                SELECT
                    'Materials' as category,
                    COALESCE(SUM(total_cost), 0) as amount
                FROM job_material_usage
                WHERE job_id IN (
                    SELECT id FROM jobs
                    WHERE DATE(created_at) BETWEEN :start_date AND :end_date
                )
                UNION ALL
                SELECT
                    'Labor' as category,
                    COALESCE(SUM(total_cost), 0) as amount
                FROM job_labor_entries
                WHERE job_id IN (
                    SELECT id FROM jobs
                    WHERE DATE(created_at) BETWEEN :start_date AND :end_date
                )
                UNION ALL
                SELECT
                    'Expenses' as category,
                    COALESCE(SUM(total_amount), 0) as amount
                FROM job_expenses
                WHERE job_id IN (
                    SELECT id FROM jobs
                    WHERE DATE(created_at) BETWEEN :start_date AND :end_date
                )
            """),
            {"start_date": start_date, "end_date": end_date}
        )

        cost_breakdown = []
        total_costs = 0
        for cost in cost_result:
            cost_breakdown.append({
                "category": cost.category,
                "amount": float(cost.amount)
            })
            total_costs += cost.amount

        # Monthly trend
        trend_result = db.execute(
            text("""
                SELECT
                    DATE_TRUNC('month', created_at) as month,
                    COALESCE(SUM(total_amount), 0) as revenue,
                    COALESCE(SUM(actual_cost), 0) as costs,
                    COUNT(*) as job_count
                FROM jobs
                WHERE DATE(created_at) BETWEEN :start_date AND :end_date
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY month
            """),
            {"start_date": start_date, "end_date": end_date}
        )

        monthly_trend = []
        for trend in trend_result:
            monthly_trend.append({
                "month": trend.month.strftime("%Y-%m"),
                "revenue": float(trend.revenue),
                "costs": float(trend.costs),
                "profit": float(trend.revenue - trend.costs),
                "job_count": trend.job_count,
                "profit_margin": round(
                    (trend.revenue - trend.costs) / trend.revenue * 100, 1
                ) if trend.revenue > 0 else 0
            })

        return {
            "summary": {
                "total_revenue": float(total_revenue),
                "total_estimated_cost": float(total_estimated_cost),
                "total_actual_cost": float(total_actual_cost),
                "total_profit": float(total_revenue - total_actual_cost),
                "profit_margin": round(
                    (total_revenue - total_actual_cost) / total_revenue * 100, 1
                ) if total_revenue > 0 else 0
            },
            "revenue_by_status": revenue_by_status,
            "cost_breakdown": cost_breakdown,
            "monthly_trend": monthly_trend,
            "filters": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate financial report: {str(e)}"
        )

@router.get("/export/csv")
async def export_jobs_report_csv(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export jobs report as CSV"""
    try:
        # Build query
        query = """
            SELECT
                j.id as job_id,
                c.name as customer_name,
                j.status,
                j.job_type,
                j.total_amount,
                j.estimated_cost,
                j.actual_cost,
                j.scheduled_start,
                j.scheduled_end,
                j.actual_start,
                j.actual_end,
                j.created_at,
                cr.name as crew_name
            FROM jobs j
            LEFT JOIN customers c ON j.customer_id = c.id
            LEFT JOIN crews cr ON j.assigned_crew_id = cr.id
            WHERE 1=1
        """
        params = {}

        if start_date:
            query += " AND DATE(j.created_at) >= :start_date"
            params["start_date"] = start_date

        if end_date:
            query += " AND DATE(j.created_at) <= :end_date"
            params["end_date"] = end_date

        if status:
            query += " AND j.status = :status"
            params["status"] = status

        query += " ORDER BY j.created_at DESC"

        result = db.execute(text(query), params)

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow([
            "Job ID", "Customer", "Status", "Type", "Revenue",
            "Estimated Cost", "Actual Cost", "Profit", "Profit Margin %",
            "Scheduled Start", "Scheduled End", "Actual Start", "Actual End",
            "Created Date", "Crew"
        ])

        # Write data
        for row in result:
            profit = (row.total_amount or 0) - (row.actual_cost or 0)
            profit_margin = round(profit / row.total_amount * 100, 1) if row.total_amount and row.total_amount > 0 else 0

            writer.writerow([
                row.job_id,
                row.customer_name,
                row.status,
                row.job_type or "N/A",
                row.total_amount or 0,
                row.estimated_cost or 0,
                row.actual_cost or 0,
                profit,
                profit_margin,
                row.scheduled_start.strftime("%Y-%m-%d") if row.scheduled_start else "",
                row.scheduled_end.strftime("%Y-%m-%d") if row.scheduled_end else "",
                row.actual_start.strftime("%Y-%m-%d") if row.actual_start else "",
                row.actual_end.strftime("%Y-%m-%d") if row.actual_end else "",
                row.created_at.strftime("%Y-%m-%d"),
                row.crew_name or "Unassigned"
            ])

        # Return CSV response
        output.seek(0)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=jobs_report_{date.today().isoformat()}.csv"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export report: {str(e)}"
        )

@router.get("/dashboard")
async def get_dashboard_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get key metrics for dashboard"""
    try:
        # Get current period metrics (last 30 days)
        current_metrics = db.execute(
            text("""
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_jobs,
                    COUNT(*) FILTER (WHERE status = 'in_progress') as active_jobs,
                    COUNT(*) FILTER (WHERE status = 'scheduled') as scheduled_jobs,
                    COALESCE(SUM(total_amount), 0) as total_revenue,
                    COALESCE(SUM(total_amount) FILTER (WHERE status = 'completed'), 0) as completed_revenue
                FROM jobs
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
        ).fetchone()

        # Get previous period for comparison
        previous_metrics = db.execute(
            text("""
                SELECT
                    COUNT(*) as total_jobs,
                    COALESCE(SUM(total_amount), 0) as total_revenue
                FROM jobs
                WHERE created_at >= NOW() - INTERVAL '60 days'
                    AND created_at < NOW() - INTERVAL '30 days'
            """)
        ).fetchone()

        # Calculate growth rates
        job_growth = round(
            (current_metrics.total_jobs - previous_metrics.total_jobs) / previous_metrics.total_jobs * 100, 1
        ) if previous_metrics.total_jobs > 0 else 0

        revenue_growth = round(
            (current_metrics.total_revenue - previous_metrics.total_revenue) / previous_metrics.total_revenue * 100, 1
        ) if previous_metrics.total_revenue > 0 else 0

        # Get top customers
        top_customers = db.execute(
            text("""
                SELECT
                    c.id,
                    c.name,
                    COUNT(j.id) as job_count,
                    COALESCE(SUM(j.total_amount), 0) as total_revenue
                FROM customers c
                LEFT JOIN jobs j ON c.id = j.customer_id
                WHERE j.created_at >= NOW() - INTERVAL '30 days'
                GROUP BY c.id, c.name
                ORDER BY total_revenue DESC
                LIMIT 5
            """)
        )

        customers = []
        for customer in top_customers:
            customers.append({
                "id": str(customer.id),
                "name": customer.name,
                "job_count": customer.job_count,
                "total_revenue": float(customer.total_revenue)
            })

        return {
            "current_period": {
                "total_jobs": current_metrics.total_jobs,
                "completed_jobs": current_metrics.completed_jobs,
                "active_jobs": current_metrics.active_jobs,
                "scheduled_jobs": current_metrics.scheduled_jobs,
                "total_revenue": float(current_metrics.total_revenue),
                "completed_revenue": float(current_metrics.completed_revenue),
                "completion_rate": round(
                    current_metrics.completed_jobs / current_metrics.total_jobs * 100, 1
                ) if current_metrics.total_jobs > 0 else 0
            },
            "growth": {
                "job_growth_rate": job_growth,
                "revenue_growth_rate": revenue_growth
            },
            "top_customers": customers
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )