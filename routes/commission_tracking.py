"""
Commission Tracking Module - Task 67
Complete sales commission management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import asyncpg
import uuid

router = APIRouter()

# Database connection
async def get_db(request: Request):
    """Yield a database connection from the shared asyncpg pool."""
    pool = getattr(request.app.state, "db_pool", None)
    if pool is None:
        raise HTTPException(status_code=503, detail="Database connection not available")

    async with pool.acquire() as conn:
        yield conn


# Models
class CommissionCreate(BaseModel):
    sales_rep: str
    period_start: date
    period_end: date
    opportunity_id: Optional[str] = None
    sale_amount: float
    commission_rate: float
    bonus_amount: float = 0
    notes: Optional[str] = None

class CommissionResponse(BaseModel):
    id: str
    sales_rep: str
    period_start: date
    period_end: date
    sale_amount: float
    commission_amount: float
    bonus_amount: float
    total_commission: float
    status: str
    created_at: datetime

# Endpoints
@router.post("/", response_model=CommissionResponse)
async def create_commission(
    commission: CommissionCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create commission record"""
    commission_amount = commission.sale_amount * (commission.commission_rate / 100)
    total_commission = commission_amount + commission.bonus_amount

    query = """
        INSERT INTO commissions (
            sales_rep, period_start, period_end, opportunity_id,
            sale_amount, commission_rate, commission_amount,
            bonus_amount, total_commission, status, notes
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        ) RETURNING *
    """

    result = await conn.fetchrow(
        query,
        commission.sales_rep,
        commission.period_start,
        commission.period_end,
        uuid.UUID(commission.opportunity_id) if commission.opportunity_id else None,
        commission.sale_amount,
        commission.commission_rate,
        commission_amount,
        commission.bonus_amount,
        total_commission,
        'pending',
        commission.notes
    )

    return {
        **dict(result),
        "id": str(result['id']),
        "opportunity_id": str(result['opportunity_id']) if result['opportunity_id'] else None
    }

@router.get("/", response_model=List[CommissionResponse])
async def list_commissions(
    sales_rep: Optional[str] = None,
    status: Optional[str] = None,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List commissions with filters"""
    conditions = []
    params = []

    if sales_rep:
        params.append(sales_rep)
        conditions.append(f"sales_rep = ${len(params)}")

    if status:
        params.append(status)
        conditions.append(f"status = ${len(params)}")

    if period_start:
        params.append(period_start)
        conditions.append(f"period_start >= ${len(params)}")

    if period_end:
        params.append(period_end)
        conditions.append(f"period_end <= ${len(params)}")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, skip])

    query = f"""
        SELECT * FROM commissions
        {where_clause}
        ORDER BY period_start DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "opportunity_id": str(row['opportunity_id']) if row['opportunity_id'] else None
        }
        for row in rows
    ]

@router.get("/summary/{sales_rep}")
async def get_commission_summary(
    sales_rep: str,
    year: int = Query(datetime.now().year),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get commission summary for a sales rep"""
    query = """
        SELECT
            SUM(sale_amount) as total_sales,
            SUM(commission_amount) as total_commission,
            SUM(bonus_amount) as total_bonus,
            SUM(total_commission) as total_earnings,
            COUNT(*) as deals_count,
            AVG(commission_rate) as avg_rate
        FROM commissions
        WHERE sales_rep = $1
        AND EXTRACT(YEAR FROM period_start) = $2
    """

    result = await conn.fetchrow(query, sales_rep, year)

    return {
        "sales_rep": sales_rep,
        "year": year,
        "total_sales": float(result['total_sales'] or 0),
        "total_commission": float(result['total_commission'] or 0),
        "total_bonus": float(result['total_bonus'] or 0),
        "total_earnings": float(result['total_earnings'] or 0),
        "deals_count": result['deals_count'] or 0,
        "avg_rate": float(result['avg_rate'] or 0)
    }
