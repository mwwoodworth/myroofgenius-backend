"""
Quote Management Module - Task 64
Complete quote generation and tracking system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
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
class QuoteCreate(BaseModel):
    quote_name: str
    opportunity_id: Optional[str] = None
    customer_id: Optional[str] = None
    valid_from: date
    valid_until: date
    subtotal: float
    discount_percentage: float = 0
    tax_rate: float = 0
    shipping_amount: float = 0
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    prepared_by: str

class QuoteResponse(BaseModel):
    id: str
    quote_number: str
    quote_name: str
    status: str
    valid_from: date
    valid_until: date
    subtotal: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total_amount: float
    currency_code: str
    payment_terms: Optional[str]
    delivery_terms: Optional[str]
    prepared_by: str
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=QuoteResponse)
async def create_quote(
    quote: QuoteCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new quote"""
    # Generate quote number
    count = await conn.fetchval("SELECT COUNT(*) FROM quotes")
    quote_number = f"Q-{datetime.utcnow().year}-{(count or 0) + 1:05d}"

    # Calculate amounts
    discount_amount = quote.subtotal * (quote.discount_percentage / 100)
    tax_amount = (quote.subtotal - discount_amount) * (quote.tax_rate / 100)
    total_amount = quote.subtotal - discount_amount + tax_amount + quote.shipping_amount

    query = """
        INSERT INTO quotes (
            quote_number, quote_name, opportunity_id, customer_id,
            status, valid_from, valid_until, subtotal,
            discount_percentage, discount_amount, tax_rate, tax_amount,
            shipping_amount, total_amount, payment_terms, delivery_terms,
            notes, internal_notes, terms_and_conditions, prepared_by
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
            $13, $14, $15, $16, $17, $18, $19, $20
        ) RETURNING *
    """

    result = await conn.fetchrow(
        query,
        quote_number,
        quote.quote_name,
        uuid.UUID(quote.opportunity_id) if quote.opportunity_id else None,
        uuid.UUID(quote.customer_id) if quote.customer_id else None,
        'draft',
        quote.valid_from,
        quote.valid_until,
        quote.subtotal,
        quote.discount_percentage,
        discount_amount,
        quote.tax_rate,
        tax_amount,
        quote.shipping_amount,
        total_amount,
        quote.payment_terms,
        quote.delivery_terms,
        quote.notes,
        quote.internal_notes,
        quote.terms_and_conditions,
        quote.prepared_by
    )

    return {
        **dict(result),
        "id": str(result['id']),
        "opportunity_id": str(result['opportunity_id']) if result['opportunity_id'] else None,
        "customer_id": str(result['customer_id']) if result['customer_id'] else None
    }

@router.get("/", response_model=List[QuoteResponse])
async def list_quotes(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List quotes with filters"""
    conditions = []
    params = []

    if status:
        params.append(status)
        conditions.append(f"status = ${len(params)}")

    if customer_id:
        params.append(uuid.UUID(customer_id))
        conditions.append(f"customer_id = ${len(params)}")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, skip])

    query = f"""
        SELECT * FROM quotes
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "opportunity_id": str(row['opportunity_id']) if row['opportunity_id'] else None,
            "customer_id": str(row['customer_id']) if row['customer_id'] else None
        }
        for row in rows
    ]
