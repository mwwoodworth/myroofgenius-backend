"""
Lead Management Module - Task 61
Complete lead tracking and qualification system
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from ..database import get_db

from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import asyncpg
import uuid
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Use SQLAlchemy from main app for connection pooling
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    ""
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enums
class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CONVERTED = "converted"
    LOST = "lost"
    NURTURING = "nurturing"
    UNQUALIFIED = "unqualified"

class LeadSource(str, Enum):
    WEBSITE = "website"
    EMAIL = "email"
    PHONE = "phone"
    SOCIAL_MEDIA = "social_media"
    REFERRAL = "referral"
    PARTNER = "partner"
    EVENT = "event"
    COLD_OUTREACH = "cold_outreach"
    ADVERTISEMENT = "advertisement"
    OTHER = "other"

class LeadRating(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"

class ActivityType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    DEMO = "demo"
    FOLLOWUP = "followup"
    NOTE = "note"
    TASK = "task"

# Models
class LeadBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    contact_name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[float] = Field(None, ge=0)
    lead_source: LeadSource
    lead_status: LeadStatus = LeadStatus.NEW
    rating: Optional[LeadRating] = None
    assigned_to: Optional[str] = None
    territory_id: Optional[str] = None
    address_line1: Optional[str] = Field(None, max_length=500)
    address_line2: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=200)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    contact_name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    annual_revenue: Optional[float] = Field(None, ge=0)
    lead_source: Optional[LeadSource] = None
    lead_status: Optional[LeadStatus] = None
    rating: Optional[LeadRating] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

class LeadResponse(LeadBase):
    id: str
    lead_number: str
    lead_score: int
    last_contacted_at: Optional[datetime] = None
    converted_to_customer: bool = False
    converted_customer_id: Optional[str] = None
    converted_at: Optional[datetime] = None
    converted_by: Optional[str] = None
    lost_reason: Optional[str] = None
    lost_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class LeadActivity(BaseModel):
    activity_type: ActivityType
    subject: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    outcome: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    assigned_to: Optional[str] = None

class LeadActivityResponse(LeadActivity):
    id: str
    lead_id: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[str] = None

class LeadConversion(BaseModel):
    customer_id: str
    notes: Optional[str] = None

class LeadQualification(BaseModel):
    budget: Optional[float] = None
    authority: Optional[bool] = None
    need: Optional[str] = None
    timeline: Optional[str] = None
    score_adjustment: Optional[int] = None

# Helper functions
async def generate_lead_number(conn: asyncpg.Connection) -> str:
    """Generate unique lead number"""
    count = await conn.fetchval("SELECT COUNT(*) FROM leads")
    return f"LEAD-{(count or 0) + 1:05d}"

def calculate_lead_score(lead: dict) -> int:
    """Calculate lead score based on various factors"""
    score = 0

    # Rating score
    if lead.get('rating') == 'hot':
        score += 30
    elif lead.get('rating') == 'warm':
        score += 20
    elif lead.get('rating') == 'cold':
        score += 10

    # Company size score
    company_size = lead.get('company_size', '').lower()
    if 'enterprise' in company_size or '1000+' in company_size:
        score += 25
    elif 'mid' in company_size or '100-999' in company_size:
        score += 15
    elif 'small' in company_size or '10-99' in company_size:
        score += 10

    # Annual revenue score
    revenue = lead.get('annual_revenue', 0) or 0
    if revenue >= 10000000:  # $10M+
        score += 25
    elif revenue >= 1000000:  # $1M+
        score += 15
    elif revenue >= 100000:  # $100K+
        score += 10

    # Lead source score
    source = lead.get('lead_source', '')
    if source in ['referral', 'partner']:
        score += 20
    elif source in ['website', 'event']:
        score += 15
    elif source in ['email', 'social_media']:
        score += 10
    elif source in ['cold_outreach', 'advertisement']:
        score += 5

    # Status score
    status = lead.get('lead_status', '')
    if status in ['qualified', 'proposal', 'negotiation']:
        score += 20
    elif status in ['qualifying', 'contacted']:
        score += 10
    elif status == 'new':
        score += 5

    # Contact information completeness
    if lead.get('email'):
        score += 5
    if lead.get('phone') or lead.get('mobile'):
        score += 5
    if lead.get('website'):
        score += 3
    if all([lead.get('city'), lead.get('state'), lead.get('country')]):
        score += 7

    return min(score, 100)  # Cap at 100

# CRUD Endpoints
@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead: LeadCreate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create new lead"""
    try:
        lead_number = await generate_lead_number(conn)
        lead_data = lead.dict()
        lead_score = calculate_lead_score(lead_data)

        query = """
            INSERT INTO leads (
                lead_number, company_name, contact_name, email, phone, mobile,
                website, industry, company_size, annual_revenue, lead_source,
                lead_status, lead_score, rating, assigned_to, territory_id,
                address_line1, address_line2, city, state, postal_code, country,
                description, notes, tags, created_by
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26
            ) RETURNING *
        """

        result = await conn.fetchrow(
            query,
            lead_number, lead.company_name, lead.contact_name, lead.email,
            lead.phone, lead.mobile, lead.website, lead.industry,
            lead.company_size, lead.annual_revenue, lead.lead_source,
            lead.lead_status, lead_score, lead.rating, lead.assigned_to,
            uuid.UUID(lead.territory_id) if lead.territory_id else None,
            lead.address_line1, lead.address_line2, lead.city, lead.state,
            lead.postal_code, lead.country, lead.description, lead.notes,
            lead.tags, "system"
        )

        # Track lead creation activity
        background_tasks.add_task(
            track_lead_activity,
            str(result['id']),
            "Lead created",
            "system"
        )

        return {**dict(result), "id": str(result['id'])}

    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[LeadStatus] = None,
    source: Optional[LeadSource] = None,
    rating: Optional[LeadRating] = None,
    assigned_to: Optional[str] = None,
    min_score: Optional[int] = Query(None, ge=0, le=100),
    converted: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """List leads with filters"""
    try:
        conditions = []
        params = []
        param_count = 0

        if status:
            param_count += 1
            conditions.append(f"lead_status = ${param_count}")
            params.append(status)

        if source:
            param_count += 1
            conditions.append(f"lead_source = ${param_count}")
            params.append(source)

        if rating:
            param_count += 1
            conditions.append(f"rating = ${param_count}")
            params.append(rating)

        if assigned_to:
            param_count += 1
            conditions.append(f"assigned_to = ${param_count}")
            params.append(assigned_to)

        if min_score is not None:
            param_count += 1
            conditions.append(f"lead_score >= ${param_count}")
            params.append(min_score)

        if converted is not None:
            param_count += 1
            conditions.append(f"converted_to_customer = ${param_count}")
            params.append(converted)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        param_count += 1
        limit_param = f"${param_count}"
        params.append(limit)

        param_count += 1
        offset_param = f"${param_count}"
        params.append(skip)

        query = f"""
            SELECT * FROM leads
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit_param} OFFSET {offset_param}
        """

        rows = await conn.fetch(query, *params)

        return [
            {**dict(row), "id": str(row['id']),
             "territory_id": str(row['territory_id']) if row['territory_id'] else None,
             "converted_customer_id": str(row['converted_customer_id']) if row['converted_customer_id'] else None}
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error listing leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: str,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get lead by ID"""
    try:
        query = "SELECT * FROM leads WHERE id = $1"
        row = await conn.fetchrow(query, uuid.UUID(lead_id))

        if not row:
            raise HTTPException(status_code=404, detail="Lead not found")

        return {
            **dict(row),
            "id": str(row['id']),
            "territory_id": str(row['territory_id']) if row['territory_id'] else None,
            "converted_customer_id": str(row['converted_customer_id']) if row['converted_customer_id'] else None
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid lead ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    updates: LeadUpdate,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Update lead information"""
    try:
        # Check if lead exists
        existing = await conn.fetchrow(
            "SELECT * FROM leads WHERE id = $1",
            uuid.UUID(lead_id)
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Build update query
        update_data = updates.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No updates provided")

        # Recalculate score if relevant fields changed
        score_fields = {'rating', 'company_size', 'annual_revenue', 'lead_source', 'lead_status'}
        if any(field in update_data for field in score_fields):
            merged_data = {**dict(existing), **update_data}
            update_data['lead_score'] = calculate_lead_score(merged_data)

        set_clauses = []
        params = []
        param_count = 0

        for field, value in update_data.items():
            param_count += 1
            set_clauses.append(f"{field} = ${param_count}")
            params.append(value)

        param_count += 1
        set_clauses.append(f"updated_at = ${param_count}")
        params.append(datetime.utcnow())

        param_count += 1
        set_clauses.append(f"updated_by = ${param_count}")
        params.append("system")

        param_count += 1
        query = f"""
            UPDATE leads
            SET {', '.join(set_clauses)}
            WHERE id = ${param_count}
            RETURNING *
        """
        params.append(uuid.UUID(lead_id))

        result = await conn.fetchrow(query, *params)

        # Track status change
        if 'lead_status' in update_data and update_data['lead_status'] != existing['lead_status']:
            background_tasks.add_task(
                track_lead_activity,
                lead_id,
                f"Status changed from {existing['lead_status']} to {update_data['lead_status']}",
                "system"
            )

        return {
            **dict(result),
            "id": str(result['id']),
            "territory_id": str(result['territory_id']) if result['territory_id'] else None,
            "converted_customer_id": str(result['converted_customer_id']) if result['converted_customer_id'] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{lead_id}/convert", response_model=Dict[str, Any])
async def convert_lead_to_customer(
    lead_id: str,
    conversion: LeadConversion,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Convert lead to customer"""
    try:
        # Check if lead exists and not already converted
        lead = await conn.fetchrow(
            "SELECT * FROM leads WHERE id = $1",
            uuid.UUID(lead_id)
        )
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        if lead['converted_to_customer']:
            raise HTTPException(status_code=400, detail="Lead already converted")

        # Update lead as converted
        query = """
            UPDATE leads
            SET converted_to_customer = true,
                converted_customer_id = $1,
                converted_at = $2,
                converted_by = $3,
                lead_status = 'converted',
                updated_at = $2
            WHERE id = $4
            RETURNING *
        """

        result = await conn.fetchrow(
            query,
            uuid.UUID(conversion.customer_id),
            datetime.utcnow(),
            "system",
            uuid.UUID(lead_id)
        )

        # Track conversion
        background_tasks.add_task(
            track_lead_activity,
            lead_id,
            f"Lead converted to customer {conversion.customer_id}",
            "system"
        )

        return {
            "message": "Lead successfully converted",
            "lead_id": str(result['id']),
            "customer_id": conversion.customer_id,
            "converted_at": result['converted_at'].isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{lead_id}/activities", response_model=LeadActivityResponse)
async def create_lead_activity(
    lead_id: str,
    activity: LeadActivity,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Create activity for a lead"""
    try:
        # Check if lead exists
        lead_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM leads WHERE id = $1)",
            uuid.UUID(lead_id)
        )
        if not lead_exists:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Create activity
        query = """
            INSERT INTO lead_activities (
                lead_id, activity_type, subject, description, outcome,
                scheduled_at, duration_minutes, assigned_to, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """

        result = await conn.fetchrow(
            query,
            uuid.UUID(lead_id),
            activity.activity_type,
            activity.subject,
            activity.description,
            activity.outcome,
            activity.scheduled_at,
            activity.duration_minutes,
            activity.assigned_to,
            "system"
        )

        # Update lead last contacted
        if activity.activity_type in ['call', 'email', 'meeting']:
            await conn.execute(
                "UPDATE leads SET last_contacted_at = $1 WHERE id = $2",
                datetime.utcnow(),
                uuid.UUID(lead_id)
            )

        return {
            **dict(result),
            "id": str(result['id']),
            "lead_id": str(result['lead_id'])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{lead_id}/activities", response_model=List[LeadActivityResponse])
async def get_lead_activities(
    lead_id: str,
    activity_type: Optional[ActivityType] = None,
    limit: int = Query(50, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get activities for a lead"""
    try:
        conditions = [f"lead_id = $1"]
        params = [uuid.UUID(lead_id)]

        if activity_type:
            conditions.append(f"activity_type = $2")
            params.append(activity_type)

        where_clause = " AND ".join(conditions)
        params.append(limit)

        query = f"""
            SELECT * FROM lead_activities
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
        """

        rows = await conn.fetch(query, *params)

        return [
            {**dict(row), "id": str(row['id']), "lead_id": str(row['lead_id'])}
            for row in rows
        ]

    except Exception as e:
        logger.error(f"Error getting activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{lead_id}/qualify", response_model=LeadResponse)
async def qualify_lead(
    lead_id: str,
    qualification: LeadQualification,
    background_tasks: BackgroundTasks,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Qualify lead with BANT criteria"""
    try:
        # Get lead
        lead = await conn.fetchrow(
            "SELECT * FROM leads WHERE id = $1",
            uuid.UUID(lead_id)
        )
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Calculate new score based on qualification
        current_score = lead['lead_score'] or 0
        score_adjustment = 0

        if qualification.budget and qualification.budget >= 10000:
            score_adjustment += 15
        if qualification.authority:
            score_adjustment += 10
        if qualification.need:
            score_adjustment += 10
        if qualification.timeline and 'immediate' in qualification.timeline.lower():
            score_adjustment += 15
        elif qualification.timeline and 'quarter' in qualification.timeline.lower():
            score_adjustment += 10

        # Add manual adjustment if provided
        if qualification.score_adjustment:
            score_adjustment += qualification.score_adjustment

        new_score = min(current_score + score_adjustment, 100)

        # Update lead
        metadata = json.loads(lead['metadata'] or '{}')
        metadata['qualification'] = {
            'budget': qualification.budget,
            'authority': qualification.authority,
            'need': qualification.need,
            'timeline': qualification.timeline,
            'qualified_at': datetime.utcnow().isoformat()
        }

        query = """
            UPDATE leads
            SET lead_status = 'qualified',
                lead_score = $1,
                metadata = $2,
                updated_at = $3
            WHERE id = $4
            RETURNING *
        """

        result = await conn.fetchrow(
            query,
            new_score,
            json.dumps(metadata),
            datetime.utcnow(),
            uuid.UUID(lead_id)
        )

        # Track qualification
        background_tasks.add_task(
            track_lead_activity,
            lead_id,
            f"Lead qualified with score {new_score}",
            "system"
        )

        return {
            **dict(result),
            "id": str(result['id']),
            "territory_id": str(result['territory_id']) if result['territory_id'] else None,
            "converted_customer_id": str(result['converted_customer_id']) if result['converted_customer_id'] else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error qualifying lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_lead_stats(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    assigned_to: Optional[str] = None,
    conn: asyncpg.Connection = Depends(get_db)
):
    """Get lead statistics"""
    try:
        conditions = []
        params = []

        if date_from:
            params.append(date_from)
            conditions.append(f"created_at >= ${len(params)}")

        if date_to:
            params.append(date_to + timedelta(days=1))
            conditions.append(f"created_at < ${len(params)}")

        if assigned_to:
            params.append(assigned_to)
            conditions.append(f"assigned_to = ${len(params)}")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT
                COUNT(*) as total_leads,
                COUNT(CASE WHEN lead_status = 'new' THEN 1 END) as new_leads,
                COUNT(CASE WHEN lead_status = 'qualified' THEN 1 END) as qualified_leads,
                COUNT(CASE WHEN converted_to_customer THEN 1 END) as converted_leads,
                COUNT(CASE WHEN lead_status = 'lost' THEN 1 END) as lost_leads,
                AVG(lead_score) as avg_lead_score,
                COUNT(CASE WHEN rating = 'hot' THEN 1 END) as hot_leads,
                COUNT(CASE WHEN rating = 'warm' THEN 1 END) as warm_leads,
                COUNT(CASE WHEN rating = 'cold' THEN 1 END) as cold_leads
            FROM leads
            {where_clause}
        """

        result = await conn.fetchrow(query, *params)

        # Get source distribution
        source_query = f"""
            SELECT lead_source, COUNT(*) as count
            FROM leads
            {where_clause}
            GROUP BY lead_source
        """

        source_rows = await conn.fetch(source_query, *params)
        source_distribution = {row['lead_source']: row['count'] for row in source_rows}

        return {
            **dict(result),
            "conversion_rate": (result['converted_leads'] / result['total_leads'] * 100)
                              if result['total_leads'] > 0 else 0,
            "source_distribution": source_distribution
        }

    except Exception as e:
        logger.error(f"Error getting lead stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task
async def track_lead_activity(lead_id: str, activity: str, user: str):
    # Validate UUID format
    if lead_id and lead_id != "test":
        try:
            uuid.UUID(str(lead_id))
        except (ValueError, TypeError):
            logger.warning(f"Invalid UUID format: {lead_id}")
            return {"error": "Invalid ID format"}
    """Background task to track lead activities"""
    try:
        conn = await asyncpg.connect(
            host="aws-0-us-east-2.pooler.supabase.com",
            port=5432,
            user="postgres.yomagoqdmxszqtdwuhab",
            password="Brain0ps2O2S",
            database="postgres"
        )
        try:
            await conn.execute(
                """
                INSERT INTO lead_activities (
                    lead_id, activity_type, subject, created_by
                ) VALUES ($1, $2, $3, $4)
                """,
                uuid.UUID(lead_id),
                "note",
                activity,
                user
            )
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error tracking activity: {e}")