"""
Financial Reporting System
Task 39: Comprehensive financial reporting and analytics
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import uuid
import asyncpg
import logging
from decimal import Decimal
import json
import csv
import io
from dateutil.relativedelta import relativedelta

from database import get_db_connection
from core.supabase_auth import get_authenticated_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Enums for reporting
class ReportType(str, Enum):
    PROFIT_LOSS = "profit_loss"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    ACCOUNTS_PAYABLE = "accounts_payable"
    REVENUE = "revenue"
    EXPENSES = "expenses"
    TAX = "tax"
    PAYROLL = "payroll"
    CUSTOM = "custom"

class ReportPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"
    HTML = "html"

class ComparisonType(str, Enum):
    PERIOD_OVER_PERIOD = "period_over_period"
    YEAR_OVER_YEAR = "year_over_year"
    MONTH_OVER_MONTH = "month_over_month"
    BUDGET_VS_ACTUAL = "budget_vs_actual"
    FORECAST_VS_ACTUAL = "forecast_vs_actual"

# Pydantic models
class ReportRequest(BaseModel):
    report_type: ReportType
    period: ReportPeriod
    start_date: date
    end_date: Optional[date] = None
    comparison: Optional[ComparisonType] = None
    filters: Optional[Dict[str, Any]] = None
    format: ReportFormat = ReportFormat.JSON
    include_details: bool = False

class FinancialSummary(BaseModel):
    period: str
    revenue: float
    expenses: float
    gross_profit: float
    gross_margin: float
    net_profit: float
    net_margin: float
    ebitda: float
    cash_flow: float
    accounts_receivable: float
    accounts_payable: float

    model_config = ConfigDict(from_attributes=True)

class RevenueBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float
    count: int
    average_value: float
    growth_rate: Optional[float] = None

class ExpenseBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float
    count: int
    budget_amount: Optional[float] = None
    variance: Optional[float] = None

class CashFlowStatement(BaseModel):
    period: str
    beginning_cash: float
    operating_activities: float
    investing_activities: float
    financing_activities: float
    net_change: float
    ending_cash: float

class AccountsReceivableAging(BaseModel):
    current: float
    days_1_30: float
    days_31_60: float
    days_61_90: float
    days_over_90: float
    total: float
    average_days_outstanding: float

class ProfitLossStatement(BaseModel):
    period: str
    revenue: Dict[str, float]
    cost_of_goods_sold: Dict[str, float]
    gross_profit: float
    operating_expenses: Dict[str, float]
    operating_income: float
    other_income: float
    other_expenses: float
    ebit: float
    interest_expense: float
    tax_expense: float
    net_income: float

class BalanceSheet(BaseModel):
    as_of_date: date
    assets: Dict[str, Any]
    liabilities: Dict[str, Any]
    equity: Dict[str, Any]
    total_assets: float
    total_liabilities: float
    total_equity: float

class TaxReport(BaseModel):
    period: str
    taxable_income: float
    federal_tax: float
    state_tax: float
    local_tax: float
    sales_tax_collected: float
    sales_tax_paid: float
    payroll_tax: float
    total_tax_liability: float
    tax_payments_made: float
    tax_due: float

class KPIMetrics(BaseModel):
    revenue_growth_rate: float
    customer_acquisition_cost: float
    customer_lifetime_value: float
    gross_margin: float
    operating_margin: float
    net_margin: float
    return_on_assets: float
    return_on_equity: float
    current_ratio: float
    quick_ratio: float
    debt_to_equity: float
    days_sales_outstanding: float
    inventory_turnover: float
    employee_productivity: float

# Helper functions
async def calculate_period_dates(period: ReportPeriod, base_date: date) -> tuple[date, date]:
    """Calculate start and end dates for a period"""
    if period == ReportPeriod.DAILY:
        return base_date, base_date
    elif period == ReportPeriod.WEEKLY:
        start = base_date - timedelta(days=base_date.weekday())
        end = start + timedelta(days=6)
        return start, end
    elif period == ReportPeriod.MONTHLY:
        start = base_date.replace(day=1)
        end = (start + relativedelta(months=1)) - timedelta(days=1)
        return start, end
    elif period == ReportPeriod.QUARTERLY:
        quarter = (base_date.month - 1) // 3
        start = date(base_date.year, quarter * 3 + 1, 1)
        end = (start + relativedelta(months=3)) - timedelta(days=1)
        return start, end
    elif period == ReportPeriod.YEARLY:
        start = date(base_date.year, 1, 1)
        end = date(base_date.year, 12, 31)
        return start, end
    else:
        return base_date, base_date

async def get_revenue_data(conn, start_date: date, end_date: date, tenant_id: str = None) -> Dict[str, Any]:
    """Get revenue data for period"""
    if tenant_id:
        result = await conn.fetchrow("""
            SELECT
                COUNT(*) as transaction_count,
                SUM(total_amount) as total_revenue,
                SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) as collected_revenue,
                SUM(CASE WHEN status != 'paid' THEN total_amount ELSE 0 END) as pending_revenue,
                AVG(total_amount) as avg_transaction_value
            FROM invoices
            WHERE created_at >= $1 AND created_at <= $2
                AND status != 'cancelled'
                AND tenant_id = $3
        """, datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()),
            uuid.UUID(tenant_id))

        # Get revenue by category
        categories = await conn.fetch("""
            SELECT
                COALESCE(j.job_type, 'Other') as category,
                COUNT(i.id) as count,
                SUM(i.total_amount) as amount
            FROM invoices i
            LEFT JOIN jobs j ON i.job_id = j.id
            WHERE i.created_at >= $1 AND i.created_at <= $2
                AND i.status != 'cancelled'
                AND i.tenant_id = $3
            GROUP BY j.job_type
        """, datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()),
            uuid.UUID(tenant_id))
    else:
        result = await conn.fetchrow("""
            SELECT
                COUNT(*) as transaction_count,
                SUM(total_amount) as total_revenue,
                SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) as collected_revenue,
                SUM(CASE WHEN status != 'paid' THEN total_amount ELSE 0 END) as pending_revenue,
                AVG(total_amount) as avg_transaction_value
            FROM invoices
            WHERE created_at >= $1 AND created_at <= $2
                AND status != 'cancelled'
        """, datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()))

        # Get revenue by category
        categories = await conn.fetch("""
            SELECT
                COALESCE(j.job_type, 'Other') as category,
                COUNT(i.id) as count,
                SUM(i.total_amount) as amount
            FROM invoices i
            LEFT JOIN jobs j ON i.job_id = j.id
            WHERE i.created_at >= $1 AND i.created_at <= $2
                AND i.status != 'cancelled'
            GROUP BY j.job_type
        """, datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()))

    return {
        "total": float(result["total_revenue"]) if result["total_revenue"] else 0,
        "collected": float(result["collected_revenue"]) if result["collected_revenue"] else 0,
        "pending": float(result["pending_revenue"]) if result["pending_revenue"] else 0,
        "transaction_count": result["transaction_count"] or 0,
        "avg_value": float(result["avg_transaction_value"]) if result["avg_transaction_value"] else 0,
        "by_category": [
            {
                "category": cat["category"],
                "count": cat["count"],
                "amount": float(cat["amount"]) if cat["amount"] else 0
            }
            for cat in categories
        ]
    }

async def get_expense_data(conn, start_date: date, end_date: date, tenant_id: str = None) -> Dict[str, Any]:
    """Get expense data for period"""
    # Get job costs as expenses
    if tenant_id:
        result = await conn.fetchrow("""
            SELECT
                COUNT(*) as expense_count,
                SUM(material_cost + labor_cost + other_costs) as total_expenses,
                SUM(material_cost) as material_expenses,
                SUM(labor_cost) as labor_expenses,
                SUM(other_costs) as other_expenses
            FROM job_costs
            WHERE created_at >= $1 AND created_at <= $2 AND tenant_id = $3
        """, datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()),
            uuid.UUID(tenant_id))
    else:
        result = await conn.fetchrow("""
            SELECT
                COUNT(*) as expense_count,
                SUM(material_cost + labor_cost + other_costs) as total_expenses,
                SUM(material_cost) as material_expenses,
                SUM(labor_cost) as labor_expenses,
                SUM(other_costs) as other_expenses
            FROM job_costs
            WHERE created_at >= $1 AND created_at <= $2
        """, datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date, datetime.max.time()))

    return {
        "total": float(result["total_expenses"]) if result["total_expenses"] else 0,
        "materials": float(result["material_expenses"]) if result["material_expenses"] else 0,
        "labor": float(result["labor_expenses"]) if result["labor_expenses"] else 0,
        "other": float(result["other_expenses"]) if result["other_expenses"] else 0,
        "count": result["expense_count"] or 0
    }

async def calculate_kpis(conn, start_date: date, end_date: date) -> KPIMetrics:
    """Calculate key performance indicators"""
    # Get current period data
    current_revenue = await get_revenue_data(conn, start_date, end_date)
    current_expenses = await get_expense_data(conn, start_date, end_date)

    # Get previous period for comparison
    period_days = (end_date - start_date).days
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_days)
    prev_revenue = await get_revenue_data(conn, prev_start, prev_end)

    # Calculate metrics
    revenue_growth = ((current_revenue["total"] - prev_revenue["total"]) / prev_revenue["total"] * 100) if prev_revenue["total"] > 0 else 0
    gross_profit = current_revenue["total"] - current_expenses["materials"]
    gross_margin = (gross_profit / current_revenue["total"] * 100) if current_revenue["total"] > 0 else 0
    operating_profit = gross_profit - current_expenses["labor"] - current_expenses["other"]
    operating_margin = (operating_profit / current_revenue["total"] * 100) if current_revenue["total"] > 0 else 0
    net_margin = operating_margin  # Simplified, would include taxes

    # Get AR/AP data
    ar_data = await conn.fetchrow("""
        SELECT
            SUM(balance_cents) / 100.0 as total_ar,
            AVG(CURRENT_DATE - due_date) as avg_days_outstanding
        FROM invoices
        WHERE status NOT IN ('paid', 'cancelled')
    """)

    return KPIMetrics(
        revenue_growth_rate=round(revenue_growth, 2),
        customer_acquisition_cost=0,  # Would need marketing spend data
        customer_lifetime_value=0,  # Would need customer history
        gross_margin=round(gross_margin, 2),
        operating_margin=round(operating_margin, 2),
        net_margin=round(net_margin, 2),
        return_on_assets=0,  # Would need asset data
        return_on_equity=0,  # Would need equity data
        current_ratio=0,  # Would need current assets/liabilities
        quick_ratio=0,  # Would need liquid assets
        debt_to_equity=0,  # Would need debt/equity data
        days_sales_outstanding=float(ar_data["avg_days_outstanding"]) if ar_data["avg_days_outstanding"] else 0,
        inventory_turnover=0,  # Would need inventory data
        employee_productivity=0  # Would need employee data
    )

# API Endpoints
@router.post("/reports/generate")
async def generate_report(
    request: ReportRequest,
    response: Response,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Generate financial report"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        # Set end date if not provided
        if not request.end_date:
            request.end_date = request.start_date

        # Generate report based on type
        if request.report_type == ReportType.PROFIT_LOSS:
            report_data = await generate_profit_loss(conn, request.start_date, request.end_date, tenant_id=tenant_id)
        elif request.report_type == ReportType.REVENUE:
            report_data = await generate_revenue_report(conn, request.start_date, request.end_date, tenant_id=tenant_id)
        elif request.report_type == ReportType.EXPENSES:
            report_data = await generate_expense_report(conn, request.start_date, request.end_date, tenant_id=tenant_id)
        elif request.report_type == ReportType.ACCOUNTS_RECEIVABLE:
            report_data = await generate_ar_report(conn, request.end_date, tenant_id=tenant_id)
        elif request.report_type == ReportType.CASH_FLOW:
            report_data = await generate_cash_flow(conn, request.start_date, request.end_date, tenant_id=tenant_id)
        else:
            raise HTTPException(status_code=400, detail=f"Report type {request.report_type} not yet implemented")

        # Format output
        if request.format == ReportFormat.CSV:
            csv_content = convert_to_csv(report_data)
            response.headers["Content-Type"] = "text/csv"
            response.headers["Content-Disposition"] = f"attachment; filename={request.report_type}_{request.start_date}.csv"
            return Response(content=csv_content, media_type="text/csv")
        else:
            return report_data

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/summary", response_model=FinancialSummary)
async def get_financial_summary(
    period: ReportPeriod = ReportPeriod.MONTHLY,
    report_date: Optional[date] = None,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get financial summary for period"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        if not report_date:
            report_date = datetime.now().date()

        start_date, end_date = await calculate_period_dates(period, report_date)

        # Get revenue and expense data
        revenue_data = await get_revenue_data(conn, start_date, end_date, tenant_id)
        expense_data = await get_expense_data(conn, start_date, end_date, tenant_id)

        # Calculate metrics
        revenue = revenue_data["total"]
        expenses = expense_data["total"]
        gross_profit = revenue - expense_data["materials"]
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
        net_profit = revenue - expenses
        net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
        ebitda = net_profit  # Simplified

        # Get AR/AP
        ar_result = await conn.fetchrow("""
            SELECT SUM(balance_cents) / 100.0 as total_ar
            FROM invoices
            WHERE status NOT IN ('paid', 'cancelled') AND tenant_id = $1
        """, uuid.UUID(tenant_id))

        return FinancialSummary(
            period=f"{start_date} to {end_date}",
            revenue=revenue,
            expenses=expenses,
            gross_profit=gross_profit,
            gross_margin=round(gross_margin, 2),
            net_profit=net_profit,
            net_margin=round(net_margin, 2),
            ebitda=ebitda,
            cash_flow=revenue_data["collected"] - expenses,
            accounts_receivable=float(ar_result["total_ar"]) if ar_result["total_ar"] else 0,
            accounts_payable=0  # Would need AP data
        )

    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/profit-loss")
async def get_profit_loss(
    start_date: date,
    end_date: date,
    comparison: Optional[ComparisonType] = None,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get profit & loss statement"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        return await generate_profit_loss(conn, start_date, end_date, comparison, tenant_id=tenant_id)
    except Exception as e:
        logger.error(f"Error generating P&L: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/revenue")
async def get_revenue_report(
    start_date: date,
    end_date: date,
    group_by: Optional[str] = "category",
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get revenue report"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        return await generate_revenue_report(conn, start_date, end_date, group_by, tenant_id=tenant_id)
    except Exception as e:
        logger.error(f"Error generating revenue report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/expenses")
async def get_expense_report(
    start_date: date,
    end_date: date,
    group_by: Optional[str] = "category",
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get expense report"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        return await generate_expense_report(conn, start_date, end_date, group_by, tenant_id=tenant_id)
    except Exception as e:
        logger.error(f"Error generating expense report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/accounts-receivable")
async def get_ar_aging(
    as_of_date: Optional[date] = None,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get accounts receivable aging report"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        if not as_of_date:
            as_of_date = datetime.now().date()

        return await generate_ar_report(conn, as_of_date, tenant_id=tenant_id)

    except Exception as e:
        logger.error(f"Error generating AR report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/cash-flow")
async def get_cash_flow(
    start_date: date,
    end_date: date,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get cash flow statement"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        return await generate_cash_flow(conn, start_date, end_date, tenant_id=tenant_id)
    except Exception as e:
        logger.error(f"Error generating cash flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/kpi", response_model=KPIMetrics)
async def get_kpi_metrics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get key performance indicators"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date.replace(day=1)

        return await calculate_kpis(conn, start_date, end_date, tenant_id=tenant_id)

    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/tax")
async def get_tax_report(
    year: int,
    quarter: Optional[int] = None,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get tax report"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        if quarter:
            start_date = date(year, (quarter - 1) * 3 + 1, 1)
            end_date = (start_date + relativedelta(months=3)) - timedelta(days=1)
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        # Get revenue
        revenue_data = await get_revenue_data(conn, start_date, end_date, tenant_id)
        expense_data = await get_expense_data(conn, start_date, end_date, tenant_id)

        taxable_income = revenue_data["total"] - expense_data["total"]

        # Calculate taxes (simplified)
        federal_rate = 0.21  # Corporate rate
        state_rate = 0.05  # Example state rate

        federal_tax = taxable_income * federal_rate if taxable_income > 0 else 0
        state_tax = taxable_income * state_rate if taxable_income > 0 else 0

        # Get sales tax data (would need actual sales tax tables)
        sales_tax = revenue_data["total"] * 0.08  # Example 8% sales tax

        return TaxReport(
            period=f"{start_date} to {end_date}",
            taxable_income=taxable_income,
            federal_tax=federal_tax,
            state_tax=state_tax,
            local_tax=0,
            sales_tax_collected=sales_tax,
            sales_tax_paid=0,
            payroll_tax=expense_data["labor"] * 0.0765,  # FICA rate
            total_tax_liability=federal_tax + state_tax + sales_tax,
            tax_payments_made=0,
            tax_due=federal_tax + state_tax + sales_tax
        )

    except Exception as e:
        logger.error(f"Error generating tax report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/trends")
async def get_financial_trends(
    periods: int = 12,
    period_type: ReportPeriod = ReportPeriod.MONTHLY,
    conn = Depends(get_db_connection),
    current_user: Dict[str, Any] = Depends(get_authenticated_user)
):
    """Get financial trends over multiple periods"""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant assignment required")

    try:
        trends = []
        current_date = datetime.now().date()

        for i in range(periods):
            if period_type == ReportPeriod.MONTHLY:
                period_date = current_date - relativedelta(months=i)
            elif period_type == ReportPeriod.QUARTERLY:
                period_date = current_date - relativedelta(months=i*3)
            elif period_type == ReportPeriod.YEARLY:
                period_date = current_date - relativedelta(years=i)
            else:
                period_date = current_date - timedelta(days=i*7)

            start_date, end_date = await calculate_period_dates(period_type, period_date)

            revenue_data = await get_revenue_data(conn, start_date, end_date, tenant_id)
            expense_data = await get_expense_data(conn, start_date, end_date, tenant_id)

            trends.append({
                "period": f"{start_date}",
                "revenue": revenue_data["total"],
                "expenses": expense_data["total"],
                "profit": revenue_data["total"] - expense_data["total"],
                "transactions": revenue_data["transaction_count"]
            })

        return {
            "period_type": period_type,
            "periods": periods,
            "data": list(reversed(trends))
        }

    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/custom")
async def create_custom_report(
    name: str,
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    conn = Depends(get_db_connection)
):
    """Create custom financial report"""
    try:
        # Validate query (basic safety check)
        if any(keyword in query.upper() for keyword in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]):
            raise HTTPException(status_code=400, detail="Query contains prohibited operations")

        # Execute query
        if parameters:
            results = await conn.fetch(query, *parameters.values())
        else:
            results = await conn.fetch(query)

        return {
            "report_name": name,
            "generated_at": datetime.now(),
            "row_count": len(results),
            "data": [dict(row) for row in results]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating custom report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/scheduled")
async def get_scheduled_reports(
    conn = Depends(get_db_connection)
):
    """Get list of scheduled reports"""
    try:
        reports = await conn.fetch("""
            SELECT id, report_name, report_type, schedule, recipients,
                   last_run, next_run, is_active
            FROM scheduled_reports
            WHERE is_active = true
            ORDER BY next_run
        """)

        return [dict(row) for row in reports]

    except Exception as e:
        logger.error(f"Error fetching scheduled reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Report generation functions
async def generate_profit_loss(conn, start_date: date, end_date: date, comparison: Optional[ComparisonType] = None) -> Dict:
    """Generate P&L statement"""
    revenue_data = await get_revenue_data(conn, start_date, end_date)
    expense_data = await get_expense_data(conn, start_date, end_date)

    # Build revenue breakdown
    revenue_breakdown = {}
    for cat in revenue_data["by_category"]:
        revenue_breakdown[cat["category"]] = cat["amount"]

    # Build expense breakdown
    expense_breakdown = {
        "Materials": expense_data["materials"],
        "Labor": expense_data["labor"],
        "Other": expense_data["other"]
    }

    gross_profit = revenue_data["total"] - expense_data["materials"]
    operating_income = gross_profit - expense_data["labor"] - expense_data["other"]

    pl_statement = ProfitLossStatement(
        period=f"{start_date} to {end_date}",
        revenue=revenue_breakdown,
        cost_of_goods_sold={"Materials": expense_data["materials"]},
        gross_profit=gross_profit,
        operating_expenses=expense_breakdown,
        operating_income=operating_income,
        other_income=0,
        other_expenses=0,
        ebit=operating_income,
        interest_expense=0,
        tax_expense=operating_income * 0.21 if operating_income > 0 else 0,
        net_income=operating_income * 0.79 if operating_income > 0 else operating_income
    )

    result = {"current_period": pl_statement.dict()}

    # Add comparison if requested
    if comparison:
        if comparison == ComparisonType.PERIOD_OVER_PERIOD:
            period_days = (end_date - start_date).days
            prev_end = start_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=period_days)
            prev_pl = await generate_profit_loss(conn, prev_start, prev_end)
            result["previous_period"] = prev_pl["current_period"]
            result["variance"] = calculate_variance(pl_statement.dict(), prev_pl["current_period"])

    return result

async def generate_revenue_report(conn, start_date: date, end_date: date, group_by: str = "category") -> Dict:
    """Generate revenue report"""
    revenue_data = await get_revenue_data(conn, start_date, end_date)

    breakdown = []
    total = revenue_data["total"]

    for cat in revenue_data["by_category"]:
        breakdown.append(RevenueBreakdown(
            category=cat["category"],
            amount=cat["amount"],
            percentage=(cat["amount"] / total * 100) if total > 0 else 0,
            count=cat["count"],
            average_value=cat["amount"] / cat["count"] if cat["count"] > 0 else 0
        ).dict())

    return {
        "period": f"{start_date} to {end_date}",
        "total_revenue": total,
        "collected_revenue": revenue_data["collected"],
        "pending_revenue": revenue_data["pending"],
        "transaction_count": revenue_data["transaction_count"],
        "average_transaction": revenue_data["avg_value"],
        "breakdown": breakdown
    }

async def generate_expense_report(conn, start_date: date, end_date: date, group_by: str = "category") -> Dict:
    """Generate expense report"""
    expense_data = await get_expense_data(conn, start_date, end_date)

    total = expense_data["total"]
    breakdown = [
        ExpenseBreakdown(
            category="Materials",
            amount=expense_data["materials"],
            percentage=(expense_data["materials"] / total * 100) if total > 0 else 0,
            count=expense_data["count"]
        ).dict(),
        ExpenseBreakdown(
            category="Labor",
            amount=expense_data["labor"],
            percentage=(expense_data["labor"] / total * 100) if total > 0 else 0,
            count=expense_data["count"]
        ).dict(),
        ExpenseBreakdown(
            category="Other",
            amount=expense_data["other"],
            percentage=(expense_data["other"] / total * 100) if total > 0 else 0,
            count=expense_data["count"]
        ).dict()
    ]

    return {
        "period": f"{start_date} to {end_date}",
        "total_expenses": total,
        "expense_count": expense_data["count"],
        "breakdown": breakdown
    }

async def generate_ar_report(conn, as_of_date: date) -> Dict:
    """Generate accounts receivable aging report"""
    result = await conn.fetchrow("""
        SELECT
            SUM(CASE WHEN CURRENT_DATE - due_date <= 0 THEN balance_cents ELSE 0 END) / 100.0 as current,
            SUM(CASE WHEN CURRENT_DATE - due_date BETWEEN 1 AND 30 THEN balance_cents ELSE 0 END) / 100.0 as days_1_30,
            SUM(CASE WHEN CURRENT_DATE - due_date BETWEEN 31 AND 60 THEN balance_cents ELSE 0 END) / 100.0 as days_31_60,
            SUM(CASE WHEN CURRENT_DATE - due_date BETWEEN 61 AND 90 THEN balance_cents ELSE 0 END) / 100.0 as days_61_90,
            SUM(CASE WHEN CURRENT_DATE - due_date > 90 THEN balance_cents ELSE 0 END) / 100.0 as days_over_90,
            SUM(balance_cents) / 100.0 as total,
            AVG(CURRENT_DATE - due_date) as avg_days
        FROM invoices
        WHERE status NOT IN ('paid', 'cancelled')
            AND created_at <= $1
    """, datetime.combine(as_of_date, datetime.max.time()))

    aging = AccountsReceivableAging(
        current=float(result["current"]) if result["current"] else 0,
        days_1_30=float(result["days_1_30"]) if result["days_1_30"] else 0,
        days_31_60=float(result["days_31_60"]) if result["days_31_60"] else 0,
        days_61_90=float(result["days_61_90"]) if result["days_61_90"] else 0,
        days_over_90=float(result["days_over_90"]) if result["days_over_90"] else 0,
        total=float(result["total"]) if result["total"] else 0,
        average_days_outstanding=float(result["avg_days"]) if result["avg_days"] else 0
    )

    return {
        "as_of_date": as_of_date,
        "aging": aging.dict(),
        "percentage_current": (aging.current / aging.total * 100) if aging.total > 0 else 0,
        "percentage_overdue": ((aging.total - aging.current) / aging.total * 100) if aging.total > 0 else 0
    }

async def generate_cash_flow(conn, start_date: date, end_date: date) -> Dict:
    """Generate cash flow statement"""
    # Get cash collections
    collections = await conn.fetchrow("""
        SELECT SUM(amount) as total
        FROM invoice_payments
        WHERE payment_date >= $1 AND payment_date <= $2
    """, start_date, end_date)

    # Get cash payments (simplified)
    payments = await conn.fetchrow("""
        SELECT SUM(material_cost + labor_cost + other_costs) as total
        FROM job_costs
        WHERE DATE(created_at) >= $1 AND DATE(created_at) <= $2
    """, start_date, end_date)

    operating_cash = float(collections["total"]) if collections["total"] else 0
    operating_payments = float(payments["total"]) if payments["total"] else 0

    cash_flow = CashFlowStatement(
        period=f"{start_date} to {end_date}",
        beginning_cash=0,  # Would need bank data
        operating_activities=operating_cash - operating_payments,
        investing_activities=0,  # Would need capital expense data
        financing_activities=0,  # Would need loan data
        net_change=operating_cash - operating_payments,
        ending_cash=operating_cash - operating_payments
    )

    return cash_flow.dict()

def calculate_variance(current: Dict, previous: Dict) -> Dict:
    """Calculate variance between periods"""
    variance = {}
    for key in current:
        if isinstance(current[key], (int, float)) and key in previous:
            if isinstance(previous[key], (int, float)):
                variance[key] = {
                    "amount": current[key] - previous[key],
                    "percentage": ((current[key] - previous[key]) / previous[key] * 100) if previous[key] != 0 else 0
                }
    return variance

def convert_to_csv(data: Dict) -> str:
    """Convert report data to CSV format"""
    output = io.StringIO()

    # Flatten nested dictionaries
    flat_data = []

    def flatten_dict(d, parent_key=''):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(flatten_dict(item, f"{new_key}[{i}]"))
                    else:
                        items.append((f"{new_key}[{i}]", v))
            else:
                items.append((new_key, v))
        return items

    flat_items = flatten_dict(data)

    if flat_items:
        writer = csv.writer(output)
        writer.writerow(["Field", "Value"])
        for key, value in flat_items:
            writer.writerow([key, value])

    return output.getvalue()