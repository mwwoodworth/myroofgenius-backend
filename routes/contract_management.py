"""
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
