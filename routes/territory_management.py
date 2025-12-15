"""
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

# Database connection
async def get_db():
    conn = await asyncpg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        user="postgres.yomagoqdmxszqtdwuhab",
        password="<DB_PASSWORD_REDACTED>",
        database="postgres"
    )
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
    return [{**dict(row), "id": str(row['id'])} for row in rows]

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
