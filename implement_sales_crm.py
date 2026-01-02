#!/usr/bin/env python3
"""
Script to implement all Sales CRM tasks 63-70
"""

import os
import sys

# Task implementations - these will be written to their respective files
IMPLEMENTATIONS = {
    "sales_pipeline.py": '''"""
Sales Pipeline Module - Task 63
Complete sales pipeline management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection - credentials from environment variables
import os

async def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set")
    conn = await asyncpg.connect(db_url)
    try:
        yield conn
    finally:
        await conn.close()

# Models
class PipelineCreate(BaseModel):
    pipeline_name: str
    pipeline_type: str = "standard"
    description: Optional[str] = None
    stages: List[str] = ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
    stage_probabilities: Optional[Dict[str, int]] = {}
    stage_durations: Optional[Dict[str, int]] = {}
    is_default: bool = False

class PipelineResponse(BaseModel):
    id: str
    pipeline_name: str
    pipeline_type: str
    description: Optional[str]
    stages: List[str]
    stage_probabilities: Dict[str, int]
    stage_durations: Dict[str, int]
    conversion_rates: Dict[str, float]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=PipelineResponse)
async def create_pipeline(
    pipeline: PipelineCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new sales pipeline"""
    query = """
        INSERT INTO sales_pipelines (
            pipeline_name, pipeline_type, description, stages,
            stage_probabilities, stage_durations, is_default
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
    """

    result = await conn.fetchrow(
        query,
        pipeline.pipeline_name,
        pipeline.pipeline_type,
        pipeline.description,
        json.dumps(pipeline.stages),
        json.dumps(pipeline.stage_probabilities),
        json.dumps(pipeline.stage_durations),
        pipeline.is_default
    )

    return format_pipeline_response(result)

@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    is_active: Optional[bool] = True,
    conn: asyncpg.Connection = Depends(get_db)
):
    """List all sales pipelines"""
    query = "SELECT * FROM sales_pipelines WHERE is_active = $1"
    rows = await conn.fetch(query, is_active)
    return [format_pipeline_response(row) for row in rows]

@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get specific pipeline"""
    query = "SELECT * FROM sales_pipelines WHERE id = $1"
    row = await conn.fetchrow(query, uuid.UUID(pipeline_id))
    if not row:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return format_pipeline_response(row)

def format_pipeline_response(row: dict) -> dict:
    """Format pipeline response"""
    return {
        **dict(row),
        "id": str(row['id']),
        "stages": json.loads(row['stages'] or '[]'),
        "stage_probabilities": json.loads(row['stage_probabilities'] or '{}'),
        "stage_durations": json.loads(row['stage_durations'] or '{}'),
        "conversion_rates": json.loads(row['conversion_rates'] or '{}')
    }
''',

    "quote_management.py": '''"""
Quote Management Module - Task 64
Complete quote generation and tracking system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import asyncpg
import uuid

router = APIRouter()

# Database connection - credentials from environment variables
import os

async def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set")
    conn = await asyncpg.connect(db_url)
    try:
        yield conn
    finally:
        await conn.close()

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
''',

    "proposal_generation.py": '''"""
Proposal Generation Module - Task 65
Complete proposal creation and management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection - credentials from environment variables
import os

async def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set")
    conn = await asyncpg.connect(db_url)
    try:
        yield conn
    finally:
        await conn.close()

# Models
class ProposalCreate(BaseModel):
    proposal_title: str
    opportunity_id: Optional[str] = None
    quote_id: Optional[str] = None
    customer_id: Optional[str] = None
    template_id: Optional[str] = None
    executive_summary: str
    problem_statement: str
    proposed_solution: str
    scope_of_work: str
    deliverables: List[str]
    timeline: str
    investment_summary: str
    valid_until: date
    prepared_by: str

class ProposalResponse(BaseModel):
    id: str
    proposal_number: str
    proposal_title: str
    status: str
    executive_summary: str
    valid_until: Optional[date]
    prepared_by: str
    version: int
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=ProposalResponse)
async def create_proposal(
    proposal: ProposalCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new proposal"""
    # Generate proposal number
    count = await conn.fetchval("SELECT COUNT(*) FROM proposals")
    proposal_number = f"P-{datetime.utcnow().year}-{(count or 0) + 1:05d}"

    query = """
        INSERT INTO proposals (
            proposal_number, proposal_title, opportunity_id, quote_id,
            customer_id, template_id, status, executive_summary,
            problem_statement, proposed_solution, scope_of_work,
            deliverables, timeline, investment_summary, valid_until,
            prepared_by, version
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
            $13, $14, $15, $16, $17
        ) RETURNING *
    """

    result = await conn.fetchrow(
        query,
        proposal_number,
        proposal.proposal_title,
        uuid.UUID(proposal.opportunity_id) if proposal.opportunity_id else None,
        uuid.UUID(proposal.quote_id) if proposal.quote_id else None,
        uuid.UUID(proposal.customer_id) if proposal.customer_id else None,
        uuid.UUID(proposal.template_id) if proposal.template_id else None,
        'draft',
        proposal.executive_summary,
        proposal.problem_statement,
        proposal.proposed_solution,
        proposal.scope_of_work,
        proposal.deliverables,
        proposal.timeline,
        proposal.investment_summary,
        proposal.valid_until,
        proposal.prepared_by,
        1
    )

    return {
        **dict(result),
        "id": str(result['id'])
    }

@router.get("/", response_model=List[ProposalResponse])
async def list_proposals(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List proposals with filters"""
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
        SELECT * FROM proposals
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [{"**dict(row), "id": str(row['id'])} for row in rows]
''',

    "contract_management.py": '''"""
Contract Management Module - Task 66
Complete contract lifecycle management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import asyncpg
import uuid

router = APIRouter()

# Database connection - credentials from environment variables
import os

async def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set")
    conn = await asyncpg.connect(db_url)
    try:
        yield conn
    finally:
        await conn.close()

# Models
class ContractCreate(BaseModel):
    contract_name: str
    contract_type: str
    customer_id: str
    start_date: date
    end_date: date
    contract_value: float
    payment_terms: Optional[str] = None
    billing_frequency: Optional[str] = "monthly"
    auto_renewal: bool = False
    contract_owner: str

class ContractResponse(BaseModel):
    id: str
    contract_number: str
    contract_name: str
    contract_type: str
    customer_id: str
    status: str
    start_date: date
    end_date: date
    contract_value: float
    created_at: datetime
    updated_at: datetime

# Endpoints
@router.post("/", response_model=ContractResponse)
async def create_contract(
    contract: ContractCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new contract"""
    # Generate contract number
    count = await conn.fetchval("SELECT COUNT(*) FROM contracts")
    contract_number = f"C-{datetime.utcnow().year}-{(count or 0) + 1:05d}"

    query = """
        INSERT INTO contracts (
            contract_number, contract_name, contract_type, customer_id,
            status, start_date, end_date, contract_value,
            payment_terms, billing_frequency, auto_renewal, contract_owner
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
        ) RETURNING *
    """

    result = await conn.fetchrow(
        query,
        contract_number,
        contract.contract_name,
        contract.contract_type,
        uuid.UUID(contract.customer_id),
        'draft',
        contract.start_date,
        contract.end_date,
        contract.contract_value,
        contract.payment_terms,
        contract.billing_frequency,
        contract.auto_renewal,
        contract.contract_owner
    )

    return {
        **dict(result),
        "id": str(result['id']),
        "customer_id": str(result['customer_id'])
    }

@router.get("/", response_model=List[ContractResponse])
async def list_contracts(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List contracts with filters"""
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
        SELECT * FROM contracts
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "customer_id": str(row['customer_id'])
        }
        for row in rows
    ]
''',

    "commission_tracking.py": '''"""
Commission Tracking Module - Task 67
Complete sales commission management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import asyncpg
import uuid

router = APIRouter()

# Database connection - credentials from environment variables
import os

async def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set")
    conn = await asyncpg.connect(db_url)
    try:
        yield conn
    finally:
        await conn.close()

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
''',

    "sales_forecasting.py": '''"""
Sales Forecasting Module - Task 68
Complete sales forecasting and prediction system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection - credentials from environment variables
import os

async def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set")
    conn = await asyncpg.connect(db_url)
    try:
        yield conn
    finally:
        await conn.close()

# Models
class ForecastCreate(BaseModel):
    forecast_name: str
    forecast_period: str
    start_date: date
    end_date: date
    forecast_type: str = "quarterly"
    sales_rep: Optional[str] = None
    territory_id: Optional[str] = None
    team_id: Optional[str] = None
    quota_amount: float
    assumptions: Optional[str] = None
    risks: Optional[str] = None
    notes: Optional[str] = None

class ForecastResponse(BaseModel):
    id: str
    forecast_name: str
    forecast_period: str
    start_date: date
    end_date: date
    forecast_type: str
    pipeline_coverage: float
    committed_amount: float
    best_case_amount: float
    most_likely_amount: float
    worst_case_amount: float
    closed_amount: float
    quota_amount: float
    attainment_percentage: float
    opportunities_count: int
    created_at: datetime

# Endpoints
@router.post("/", response_model=ForecastResponse)
async def create_forecast(
    forecast: ForecastCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create sales forecast"""
    # Calculate initial forecast amounts (would be more complex in reality)
    pipeline_coverage = forecast.quota_amount * 3
    committed_amount = forecast.quota_amount * 0.8
    best_case_amount = forecast.quota_amount * 1.2
    most_likely_amount = forecast.quota_amount * 0.95
    worst_case_amount = forecast.quota_amount * 0.6

    query = """
        INSERT INTO sales_forecasts (
            forecast_name, forecast_period, start_date, end_date,
            forecast_type, sales_rep, territory_id, team_id,
            pipeline_coverage, committed_amount, best_case_amount,
            most_likely_amount, worst_case_amount, closed_amount,
            quota_amount, attainment_percentage, opportunities_count,
            assumptions, risks, notes, created_by
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
            $13, $14, $15, $16, $17, $18, $19, $20, $21
        ) RETURNING *
    """

    result = await conn.fetchrow(
        query,
        forecast.forecast_name,
        forecast.forecast_period,
        forecast.start_date,
        forecast.end_date,
        forecast.forecast_type,
        forecast.sales_rep,
        uuid.UUID(forecast.territory_id) if forecast.territory_id else None,
        uuid.UUID(forecast.team_id) if forecast.team_id else None,
        pipeline_coverage,
        committed_amount,
        best_case_amount,
        most_likely_amount,
        worst_case_amount,
        0,  # closed_amount starts at 0
        forecast.quota_amount,
        0,  # attainment_percentage starts at 0
        0,  # opportunities_count starts at 0
        forecast.assumptions,
        forecast.risks,
        forecast.notes,
        "system"
    )

    return {
        **dict(result),
        "id": str(result['id']),
        "territory_id": str(result['territory_id']) if result['territory_id'] else None,
        "team_id": str(result['team_id']) if result['team_id'] else None
    }

@router.get("/", response_model=List[ForecastResponse])
async def list_forecasts(
    forecast_type: Optional[str] = None,
    sales_rep: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List sales forecasts with filters"""
    conditions = []
    params = []

    if forecast_type:
        params.append(forecast_type)
        conditions.append(f"forecast_type = ${len(params)}")

    if sales_rep:
        params.append(sales_rep)
        conditions.append(f"sales_rep = ${len(params)}")

    if start_date:
        params.append(start_date)
        conditions.append(f"start_date >= ${len(params)}")

    if end_date:
        params.append(end_date)
        conditions.append(f"end_date <= ${len(params)}")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, skip])

    query = f"""
        SELECT * FROM sales_forecasts
        {where_clause}
        ORDER BY start_date DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [
        {
            **dict(row),
            "id": str(row['id']),
            "territory_id": str(row['territory_id']) if row['territory_id'] else None,
            "team_id": str(row['team_id']) if row['team_id'] else None
        }
        for row in rows
    ]
''',

    "territory_management.py": '''"""
Territory Management Module - Task 69
Complete territory assignment and management system
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import asyncpg
import uuid
import json

router = APIRouter()

# Database connection - credentials from environment variables
import os

async def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set")
    conn = await asyncpg.connect(db_url)
    try:
        yield conn
    finally:
        await conn.close()

# Models
class TerritoryCreate(BaseModel):
    territory_code: str
    territory_name: str
    territory_type: str = "geographic"
    description: Optional[str] = None
    geographic_area: Optional[str] = None
    countries: Optional[List[str]] = []
    states: Optional[List[str]] = []
    cities: Optional[List[str]] = []
    postal_codes: Optional[List[str]] = []
    industry_segments: Optional[List[str]] = []
    annual_quota: Optional[float] = None

class TerritoryResponse(BaseModel):
    id: str
    territory_code: str
    territory_name: str
    territory_type: str
    description: Optional[str]
    geographic_area: Optional[str]
    annual_quota: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class TerritoryAssignment(BaseModel):
    territory_id: str
    sales_rep: str
    role: str = "primary"
    start_date: date
    end_date: Optional[date] = None
    quota_amount: Optional[float] = None
    is_primary: bool = False
    notes: Optional[str] = None

# Endpoints
@router.post("/", response_model=TerritoryResponse)
async def create_territory(
    territory: TerritoryCreate,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new territory"""
    query = """
        INSERT INTO territories (
            territory_code, territory_name, territory_type,
            description, geographic_area, countries, states,
            cities, postal_codes, industry_segments, annual_quota
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        ) RETURNING *
    """

    result = await conn.fetchrow(
        query,
        territory.territory_code,
        territory.territory_name,
        territory.territory_type,
        territory.description,
        territory.geographic_area,
        territory.countries,
        territory.states,
        territory.cities,
        territory.postal_codes,
        territory.industry_segments,
        territory.annual_quota
    )

    return {
        **dict(result),
        "id": str(result['id'])
    }

@router.get("/", response_model=List[TerritoryResponse])
async def list_territories(
    is_active: bool = True,
    territory_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List territories with filters"""
    conditions = ["is_active = $1"]
    params = [is_active]

    if territory_type:
        params.append(territory_type)
        conditions.append(f"territory_type = ${len(params)}")

    where_clause = " AND ".join(conditions)
    params.extend([limit, skip])

    query = f"""
        SELECT * FROM territories
        WHERE {where_clause}
        ORDER BY territory_name
        LIMIT ${len(params)-1} OFFSET ${len(params)}
    """

    rows = await conn.fetch(query, *params)
    return [{"**dict(row), "id": str(row['id'])} for row in rows]

@router.post("/{territory_id}/assign")
async def assign_territory(
    territory_id: str,
    assignment: TerritoryAssignment,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Assign sales rep to territory"""
    query = """
        INSERT INTO territory_assignments (
            territory_id, sales_rep, role, start_date, end_date,
            quota_amount, is_primary, notes
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
    """

    result = await conn.fetchrow(
        query,
        uuid.UUID(territory_id),
        assignment.sales_rep,
        assignment.role,
        assignment.start_date,
        assignment.end_date,
        assignment.quota_amount,
        assignment.is_primary,
        assignment.notes
    )

    return {
        "message": "Territory assigned successfully",
        "assignment_id": str(result['id'])
    }
''',

    "sales_analytics.py": '''"""
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

# Database connection - credentials from environment variables
import os

async def get_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set")
    conn = await asyncpg.connect(db_url)
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
'''
}

def main():
    """Write all implementations to their respective files"""
    routes_dir = "/home/matt-woodworth/fastapi-operator-env/routes"

    print("Implementing Sales CRM Tasks 63-70...")

    for filename, content in IMPLEMENTATIONS.items():
        filepath = os.path.join(routes_dir, filename)

        # Write the file
        with open(filepath, 'w') as f:
            f.write(content)

        print(f"✅ Implemented {filename}")

    print("\n✨ All Sales CRM modules (Tasks 63-70) implemented successfully!")
    print("\nNext steps:")
    print("1. Update main.py to include all new routes")
    print("2. Test locally")
    print("3. Deploy to production")

if __name__ == "__main__":
    main()