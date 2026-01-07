"""
Lead Capture & ML Scoring System
Task #102: Complete lead capture with ML-powered scoring, qualification, and nurturing
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, Form
from pydantic import BaseModel, EmailStr, Field, validator, HttpUrl
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4
import logging
import json
import numpy as np
from enum import Enum
import hashlib
import re
import asyncio
from psycopg2 import sql
# ML imports - using simple scoring without sklearn for now
# from sklearn.preprocessing import StandardScaler
# from sklearn.ensemble import RandomForestClassifier
# import joblib
import os

from core.supabase_auth import get_current_user  # SUPABASE AUTH
from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/leads", tags=["Lead Management & ML Scoring"])

# ============================================================================
# ENUMS
# ============================================================================

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    NURTURING = "nurturing"
    CONVERTED = "converted"
    LOST = "lost"

class LeadSource(str, Enum):
    WEBSITE = "website"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    REFERRAL = "referral"
    PAID_ADS = "paid_ads"
    ORGANIC_SEARCH = "organic_search"
    TRADE_SHOW = "trade_show"
    COLD_CALL = "cold_call"
    PARTNER = "partner"
    OTHER = "other"

class LeadScore(str, Enum):
    HOT = "hot"  # 80-100
    WARM = "warm"  # 60-79
    COOL = "cool"  # 40-59
    COLD = "cold"  # 0-39

class PropertyType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MULTI_FAMILY = "multi_family"
    RETAIL = "retail"
    OFFICE = "office"
    WAREHOUSE = "warehouse"

# ============================================================================
# MODELS
# ============================================================================

class LeadCapture(BaseModel):
    """Model for capturing new leads from various sources"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{9,15}$")
    company: Optional[str] = None
    title: Optional[str] = None

    # Source tracking
    source: LeadSource
    source_details: Optional[Dict[str, Any]] = {}  # UTM params, campaign info, etc.
    referrer_url: Optional[HttpUrl] = None
    landing_page: Optional[str] = None
    ip_address: Optional[str] = None

    # Lead details
    property_type: Optional[PropertyType] = None
    property_address: Optional[str] = None
    project_timeline: Optional[str] = None
    estimated_budget: Optional[float] = None
    message: Optional[str] = None

    # Consent
    consent_marketing: bool = False
    consent_terms: bool = True

class LeadScoringFactors(BaseModel):
    """Factors used for ML scoring"""
    # Demographics
    job_title_score: int = Field(0, ge=0, le=10)  # Executive=10, Manager=7, etc.
    company_size: Optional[int] = None  # Number of employees
    industry_match: bool = False

    # Engagement
    email_opens: int = Field(0, ge=0)
    email_clicks: int = Field(0, ge=0)
    website_visits: int = Field(0, ge=0)
    pages_viewed: int = Field(0, ge=0)
    time_on_site: float = Field(0, ge=0)  # Minutes
    form_submissions: int = Field(0, ge=0)

    # Intent signals
    downloaded_content: List[str] = []
    requested_demo: bool = False
    requested_quote: bool = False
    pricing_page_views: int = Field(0, ge=0)

    # Firmographics
    budget_confirmed: bool = False
    timeline_urgent: bool = False  # < 30 days
    decision_maker: bool = False
    multiple_stakeholders: int = Field(1, ge=1)

    # Social signals
    social_shares: int = Field(0, ge=0)
    referral_source_quality: int = Field(5, ge=0, le=10)

    # Negative signals
    unsubscribed: bool = False
    bounced_emails: int = Field(0, ge=0)
    ignored_followups: int = Field(0, ge=0)

class LeadUpdate(BaseModel):
    """Model for updating lead information"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    status: Optional[LeadStatus] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    assigned_to: Optional[UUID] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

class LeadResponse(BaseModel):
    """Response model for lead data"""
    id: UUID
    name: str
    email: str
    phone: Optional[str]
    company: Optional[str]
    title: Optional[str]
    source: str
    score: int
    score_category: LeadScore
    status: LeadStatus
    assigned_to: Optional[UUID]
    tags: List[str]
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_activity: Optional[datetime]
    conversion_probability: float
    recommended_actions: List[str]

class LeadListResponse(BaseModel):
    """Response for lead listing"""
    leads: List[LeadResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    score_distribution: Dict[str, int]

class MLScoringResult(BaseModel):
    """Result from ML scoring engine"""
    lead_id: UUID
    score: int
    score_category: LeadScore
    conversion_probability: float
    key_factors: List[Dict[str, Any]]
    recommended_actions: List[str]
    optimal_contact_time: Optional[str]
    estimated_deal_size: Optional[float]

class LeadNurturingCampaign(BaseModel):
    """Automated nurturing campaign"""
    name: str
    description: Optional[str]
    target_score_range: tuple[int, int]
    email_sequence: List[Dict[str, Any]]
    trigger_conditions: Dict[str, Any]
    duration_days: int

# ============================================================================
# ML SCORING ENGINE
# ============================================================================

class MLScoringEngine:
    """Rule-based scoring engine for lead scoring (ML-ready)"""

    def __init__(self):
        self.weights = {
            'job_title_score': 2.0,
            'company_size': 0.01,
            'industry_match': 10.0,
            'email_opens': 1.5,
            'email_clicks': 3.0,
            'website_visits': 2.0,
            'pages_viewed': 0.5,
            'time_on_site': 0.3,
            'form_submissions': 5.0,
            'downloaded_content': 4.0,
            'requested_demo': 20.0,
            'requested_quote': 25.0,
            'pricing_page_views': 3.0,
            'budget_confirmed': 15.0,
            'timeline_urgent': 10.0,
            'decision_maker': 12.0,
            'multiple_stakeholders': 2.0,
            'social_shares': 1.0,
            'referral_source_quality': 1.5,
            'unsubscribed': -30.0,
            'bounced_emails': -5.0,
            'ignored_followups': -3.0
        }
        logger.info("Initialized rule-based scoring engine")

    def extract_features(self, lead: Dict, factors: LeadScoringFactors) -> np.ndarray:
        """Extract features from lead data for ML scoring"""
        features = [
            # Demographics
            factors.job_title_score,
            factors.company_size if factors.company_size else 0,
            1 if factors.industry_match else 0,

            # Engagement metrics
            min(factors.email_opens, 20),  # Cap at 20
            min(factors.email_clicks, 10),
            min(factors.website_visits, 30),
            min(factors.pages_viewed, 50),
            min(factors.time_on_site, 60),
            factors.form_submissions,

            # Intent signals
            len(factors.downloaded_content),
            1 if factors.requested_demo else 0,
            1 if factors.requested_quote else 0,
            factors.pricing_page_views,

            # Firmographics
            1 if factors.budget_confirmed else 0,
            1 if factors.timeline_urgent else 0,
            1 if factors.decision_maker else 0,
            min(factors.multiple_stakeholders, 5),

            # Social and negative signals
            min(factors.social_shares, 10),
            factors.referral_source_quality,
            -5 if factors.unsubscribed else 0,  # Negative weight
        ]

        return np.array(features).reshape(1, -1)

    def score_lead(self, lead: Dict, factors: LeadScoringFactors) -> MLScoringResult:
        """Score a lead using rule-based scoring"""
        # Calculate weighted score
        base_score = 0

        # Apply weights to each factor
        base_score += self.weights['job_title_score'] * factors.job_title_score
        base_score += self.weights['company_size'] * (factors.company_size or 0)
        base_score += self.weights['industry_match'] * (1 if factors.industry_match else 0)
        base_score += self.weights['email_opens'] * min(factors.email_opens, 20)
        base_score += self.weights['email_clicks'] * min(factors.email_clicks, 10)
        base_score += self.weights['website_visits'] * min(factors.website_visits, 30)
        base_score += self.weights['pages_viewed'] * min(factors.pages_viewed, 50)
        base_score += self.weights['time_on_site'] * min(factors.time_on_site, 60)
        base_score += self.weights['form_submissions'] * factors.form_submissions
        base_score += self.weights['downloaded_content'] * len(factors.downloaded_content)
        base_score += self.weights['requested_demo'] * (1 if factors.requested_demo else 0)
        base_score += self.weights['requested_quote'] * (1 if factors.requested_quote else 0)
        base_score += self.weights['pricing_page_views'] * factors.pricing_page_views
        base_score += self.weights['budget_confirmed'] * (1 if factors.budget_confirmed else 0)
        base_score += self.weights['timeline_urgent'] * (1 if factors.timeline_urgent else 0)
        base_score += self.weights['decision_maker'] * (1 if factors.decision_maker else 0)
        base_score += self.weights['multiple_stakeholders'] * min(factors.multiple_stakeholders, 5)
        base_score += self.weights['social_shares'] * min(factors.social_shares, 10)
        base_score += self.weights['referral_source_quality'] * factors.referral_source_quality
        base_score += self.weights['unsubscribed'] * (1 if factors.unsubscribed else 0)
        base_score += self.weights['bounced_emails'] * min(factors.bounced_emails, 5)
        base_score += self.weights['ignored_followups'] * min(factors.ignored_followups, 5)

        # Normalize to 0-100 scale
        base_score = max(0, min(100, int(base_score)))

        # Calculate probability (simple sigmoid)
        probability = base_score / 100.0

        # Apply business rules adjustments
        if factors.requested_demo:
            base_score = min(100, base_score + 15)
        if factors.requested_quote:
            base_score = min(100, base_score + 20)
        if factors.budget_confirmed:
            base_score = min(100, base_score + 10)
        if factors.unsubscribed:
            base_score = max(0, base_score - 30)

        # Determine category
        if base_score >= 80:
            category = LeadScore.HOT
        elif base_score >= 60:
            category = LeadScore.WARM
        elif base_score >= 40:
            category = LeadScore.COOL
        else:
            category = LeadScore.COLD

        # Generate recommendations
        recommendations = []
        if base_score >= 80:
            recommendations.append("Contact immediately - high conversion probability")
            recommendations.append("Assign to senior sales rep")
        elif base_score >= 60:
            recommendations.append("Schedule demo within 24 hours")
            recommendations.append("Send personalized case study")
        elif base_score >= 40:
            recommendations.append("Add to nurturing campaign")
            recommendations.append("Send educational content")
        else:
            recommendations.append("Monitor for engagement signals")
            recommendations.append("Include in monthly newsletter")

        # Estimate deal size based on factors
        estimated_deal = 10000  # Base
        if factors.company_size:
            estimated_deal *= (1 + factors.company_size / 100)
        if factors.budget_confirmed:
            estimated_deal *= 1.5

        return MLScoringResult(
            lead_id=lead.get('id', uuid4()),
            score=base_score,
            score_category=category,
            conversion_probability=probability,
            key_factors=[
                {"factor": "Demo Requested", "impact": "+15" if factors.requested_demo else "0"},
                {"factor": "Quote Requested", "impact": "+20" if factors.requested_quote else "0"},
                {"factor": "Budget Confirmed", "impact": "+10" if factors.budget_confirmed else "0"},
                {"factor": "Engagement Score", "impact": f"{factors.email_opens + factors.website_visits}"},
            ],
            recommended_actions=recommendations,
            optimal_contact_time="9:00 AM - 11:00 AM" if base_score >= 60 else "2:00 PM - 4:00 PM",
            estimated_deal_size=estimated_deal
        )

# Initialize ML engine
ml_engine = MLScoringEngine()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/capture", response_model=LeadResponse)
async def capture_lead(
    lead: LeadCapture,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Capture a new lead from any source with automatic ML scoring
    """
    try:
        cursor = db.cursor()

        # Generate lead ID
        lead_id = str(uuid4())

        # Initial scoring factors (minimal for new lead)
        initial_factors = LeadScoringFactors(
            job_title_score=5,  # Default middle score
            form_submissions=1,
            referral_source_quality=7 if lead.source == LeadSource.REFERRAL else 5
        )

        # Get ML score
        ml_result = ml_engine.score_lead({"id": lead_id}, initial_factors)

        # Insert lead
        cursor.execute("""
            INSERT INTO leads (
                id, name, email, phone, company, title,
                source, score, status, tags, custom_fields,
                address, description, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, NOW(), NOW()
            )
            RETURNING *
        """, (
            lead_id, lead.name, lead.email, lead.phone, lead.company, lead.title,
            lead.source.value, ml_result.score, LeadStatus.NEW.value,
            json.dumps([]),
            json.dumps({
                "source_details": lead.source_details,
                "property_type": lead.property_type.value if lead.property_type else None,
                "project_timeline": lead.project_timeline,
                "estimated_budget": lead.estimated_budget,
                "consent_marketing": lead.consent_marketing
            }),
            lead.property_address, lead.message
        ))

        new_lead = cursor.fetchone()

        # Record lead activity
        cursor.execute("""
            INSERT INTO lead_activities (
                id, lead_id, activity_type, description, created_at
            ) VALUES (%s, %s, %s, %s, NOW())
        """, (
            str(uuid4()), lead_id, "created",
            f"Lead captured from {lead.source.value}"
        ))

        # Store ML scoring details
        cursor.execute("""
            INSERT INTO lead_scoring (
                id, name, description, status, data, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            str(uuid4()),
            f"Score for {lead.name}",
            f"ML Score: {ml_result.score}, Category: {ml_result.score_category.value}",
            "active",
            json.dumps({
                "lead_id": lead_id,
                "score": ml_result.score,
                "probability": ml_result.conversion_probability,
                "factors": ml_result.key_factors
            })
        ))

        db.commit()

        # Trigger async nurturing if needed
        if ml_result.score < 60:
            background_tasks.add_task(
                start_nurturing_campaign,
                lead_id, ml_result.score
            )

        return LeadResponse(
            **new_lead,
            score_category=ml_result.score_category,
            tags=[],
            custom_fields=json.loads(new_lead['custom_fields']) if new_lead['custom_fields'] else {},
            last_activity=new_lead['created_at'],
            conversion_probability=ml_result.conversion_probability,
            recommended_actions=ml_result.recommended_actions
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Error capturing lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{lead_id}/score", response_model=MLScoringResult)
async def score_lead(
    lead_id: UUID,
    factors: LeadScoringFactors,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Manually trigger ML scoring for a lead with updated factors
    """
    try:
        cursor = db.cursor()

        # Get lead
        cursor.execute("""
            SELECT * FROM leads WHERE id = %s
        """, (str(lead_id),))

        lead = cursor.fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Score with ML engine
        ml_result = ml_engine.score_lead(lead, factors)

        # Update lead score
        cursor.execute("""
            UPDATE leads
            SET score = %s, status = %s, updated_at = NOW()
            WHERE id = %s
        """, (
            ml_result.score,
            LeadStatus.QUALIFIED.value if ml_result.score >= 70 else lead['status'],
            str(lead_id)
        ))

        # Update scoring history
        cursor.execute("""
            INSERT INTO lead_scoring (
                id, name, description, status, data, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            str(uuid4()),
            f"Re-score for {lead['name']}",
            f"Updated ML Score: {ml_result.score}",
            "active",
            json.dumps({
                "lead_id": str(lead_id),
                "score": ml_result.score,
                "probability": ml_result.conversion_probability,
                "factors": factors.dict()
            })
        ))

        # Log activity
        cursor.execute("""
            INSERT INTO lead_activities (
                id, lead_id, activity_type, description, created_at
            ) VALUES (%s, %s, %s, %s, NOW())
        """, (
            str(uuid4()), str(lead_id), "scored",
            f"Lead re-scored: {ml_result.score} ({ml_result.score_category.value})"
        ))

        db.commit()

        return ml_result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error scoring lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get detailed lead information with ML insights
    """
    try:
        cursor = db.cursor()

        # Get lead with activity
        cursor.execute("""
            SELECT l.*,
                   MAX(la.created_at) as last_activity
            FROM leads l
            LEFT JOIN lead_activities la ON la.lead_id = l.id
            WHERE l.id = %s
            GROUP BY l.id
        """, (str(lead_id),))

        lead = cursor.fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Get latest scoring data
        cursor.execute("""
            SELECT data FROM lead_scoring
            WHERE data->>'lead_id' = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (str(lead_id),))

        scoring_data = cursor.fetchone()
        probability = 0.5
        recommendations = []

        if scoring_data and scoring_data['data']:
            data = json.loads(scoring_data['data']) if isinstance(scoring_data['data'], str) else scoring_data['data']
            probability = data.get('probability', 0.5)

        # Determine score category
        score = lead['score'] or 0
        if score >= 80:
            category = LeadScore.HOT
        elif score >= 60:
            category = LeadScore.WARM
        elif score >= 40:
            category = LeadScore.COOL
        else:
            category = LeadScore.COLD

        # Generate recommendations based on score
        if score >= 80:
            recommendations = ["Call immediately", "Send contract template"]
        elif score >= 60:
            recommendations = ["Schedule demo", "Send case study"]
        elif score >= 40:
            recommendations = ["Add to email campaign", "Send educational content"]
        else:
            recommendations = ["Monitor engagement", "Include in newsletter"]

        return LeadResponse(
            **lead,
            score_category=category,
            tags=json.loads(lead['tags']) if lead['tags'] else [],
            custom_fields=json.loads(lead['custom_fields']) if lead['custom_fields'] else {},
            conversion_probability=probability,
            recommended_actions=recommendations
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    status: Optional[LeadStatus] = None,
    min_score: Optional[int] = Query(None, ge=0, le=100),
    max_score: Optional[int] = Query(None, ge=0, le=100),
    source: Optional[LeadSource] = None,
    assigned_to: Optional[UUID] = None,
    search: Optional[str] = None,
    sort_by: str = Query("score", pattern="^(score|created_at|updated_at|name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    List leads with filtering and ML score distribution
    """
    try:
        cursor = db.cursor()

        # Build WHERE clause
        where_conditions = ["1=1"]
        params = []

        if status:
            where_conditions.append("status = %s")
            params.append(status.value)

        if min_score is not None:
            where_conditions.append("score >= %s")
            params.append(min_score)

        if max_score is not None:
            where_conditions.append("score <= %s")
            params.append(max_score)

        if source:
            where_conditions.append("source = %s")
            params.append(source.value)

        if assigned_to:
            where_conditions.append("assigned_to = %s")
            params.append(str(assigned_to))

        if search:
            where_conditions.append("""
                (LOWER(name) LIKE LOWER(%s) OR
                 LOWER(email) LIKE LOWER(%s) OR
                 LOWER(company) LIKE LOWER(%s))
            """)
            search_pattern = f"%{search}%"
            params.extend([search_pattern] * 3)

        where_clause = " AND ".join(where_conditions)

        # Get total count
        count_query = sql.SQL("""
            SELECT COUNT(*) as total FROM leads WHERE {where_clause}
        """).format(where_clause=sql.SQL(where_clause))
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Get paginated results
        offset = (page - 1) * per_page

        # SECURITY: Whitelist sort columns to prevent SQL injection (defense-in-depth)
        ALLOWED_SORT_COLUMNS = {"score", "created_at", "updated_at", "name"}
        if sort_by not in ALLOWED_SORT_COLUMNS:
            sort_by = "score"
        if sort_order.lower() not in ("asc", "desc"):
            sort_order = "desc"

        list_query = sql.SQL("""
            SELECT l.*,
                   MAX(la.created_at) as last_activity
            FROM leads l
            LEFT JOIN lead_activities la ON la.lead_id = l.id
            WHERE {where_clause}
            GROUP BY l.id
            ORDER BY {sort_column} {sort_order}
            LIMIT %s OFFSET %s
        """).format(
            where_clause=sql.SQL(where_clause),
            sort_column=sql.SQL("l.{}").format(sql.Identifier(sort_by)),
            sort_order=sql.SQL(sort_order.upper()),
        )
        cursor.execute(list_query, params + [per_page, offset])

        leads = cursor.fetchall()

        # Get score distribution
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE score >= 80) as hot,
                COUNT(*) FILTER (WHERE score >= 60 AND score < 80) as warm,
                COUNT(*) FILTER (WHERE score >= 40 AND score < 60) as cool,
                COUNT(*) FILTER (WHERE score < 40 OR score IS NULL) as cold
            FROM leads
            WHERE status != 'converted'
        """)

        distribution = cursor.fetchone()

        # Format response
        lead_responses = []
        for lead in leads:
            score = lead['score'] or 0
            if score >= 80:
                category = LeadScore.HOT
            elif score >= 60:
                category = LeadScore.WARM
            elif score >= 40:
                category = LeadScore.COOL
            else:
                category = LeadScore.COLD

            lead_responses.append(LeadResponse(
                **lead,
                score_category=category,
                tags=json.loads(lead['tags']) if lead['tags'] else [],
                custom_fields=json.loads(lead['custom_fields']) if lead['custom_fields'] else {},
                conversion_probability=score / 100,
                recommended_actions=[]
            ))

        total_pages = (total + per_page - 1) // per_page

        return LeadListResponse(
            leads=lead_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            score_distribution={
                "hot": distribution['hot'],
                "warm": distribution['warm'],
                "cool": distribution['cool'],
                "cold": distribution['cold']
            }
        )

    except Exception as e:
        logger.error(f"Error listing leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    updates: LeadUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Update lead information
    """
    try:
        cursor = db.cursor()

        # Build update query
        update_fields = []
        update_values = []

        for field, value in updates.dict(exclude_unset=True).items():
            if field == "tags":
                update_fields.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
                update_values.append(json.dumps(value))
            elif field == "custom_fields":
                update_fields.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
                update_values.append(json.dumps(value))
            elif field == "status" and value:
                update_fields.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
                update_values.append(value.value)
            else:
                update_fields.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
                update_values.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_fields.append(sql.SQL("updated_at = NOW()"))
        update_values.append(str(lead_id))

        update_query = sql.SQL("""
            UPDATE leads
            SET {fields}
            WHERE id = %s
            RETURNING *
        """).format(fields=sql.SQL(", ").join(update_fields))
        cursor.execute(update_query, update_values)

        updated_lead = cursor.fetchone()
        if not updated_lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Log activity
        cursor.execute("""
            INSERT INTO lead_activities (
                id, lead_id, activity_type, description, created_at
            ) VALUES (%s, %s, %s, %s, NOW())
        """, (
            str(uuid4()), str(lead_id), "updated",
            f"Lead information updated"
        ))

        db.commit()

        return await get_lead(lead_id, db, current_user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: UUID,
    customer_id: UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Convert lead to customer
    """
    try:
        cursor = db.cursor()

        # Update lead status
        cursor.execute("""
            UPDATE leads
            SET status = %s,
                converted_to_opportunity_id = %s,
                converted_date = NOW(),
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """, (LeadStatus.CONVERTED.value, str(customer_id), str(lead_id)))

        converted_lead = cursor.fetchone()
        if not converted_lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Log activity
        cursor.execute("""
            INSERT INTO lead_activities (
                id, lead_id, activity_type, description, created_at
            ) VALUES (%s, %s, %s, %s, NOW())
        """, (
            str(uuid4()), str(lead_id), "converted",
            f"Lead converted to customer {customer_id}"
        ))

        db.commit()

        return {
            "message": "Lead converted successfully",
            "lead_id": lead_id,
            "customer_id": customer_id
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error converting lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/funnel")
async def get_lead_funnel(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    source: Optional[LeadSource] = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Get lead funnel analytics
    """
    try:
        cursor = db.cursor()

        # Build WHERE clause
        where_conditions = ["1=1"]
        params = []

        if start_date:
            where_conditions.append("created_at >= %s")
            params.append(start_date)

        if end_date:
            where_conditions.append("created_at <= %s")
            params.append(end_date + timedelta(days=1))

        if source:
            where_conditions.append("source = %s")
            params.append(source.value)

        where_clause = " AND ".join(where_conditions)

        # Get funnel metrics
        funnel_query = sql.SQL("""
            SELECT
                COUNT(*) as total_leads,
                COUNT(*) FILTER (WHERE status = 'new') as new_leads,
                COUNT(*) FILTER (WHERE status = 'contacted') as contacted,
                COUNT(*) FILTER (WHERE status = 'qualified') as qualified,
                COUNT(*) FILTER (WHERE status = 'converted') as converted,
                AVG(score) as avg_score,
                AVG(CASE WHEN status = 'converted' THEN score END) as avg_converted_score,
                COUNT(DISTINCT source) as sources_count
            FROM leads
            WHERE {where_clause}
        """).format(where_clause=sql.SQL(where_clause))
        cursor.execute(funnel_query, params)

        metrics = cursor.fetchone()

        # Calculate conversion rates
        total = metrics['total_leads'] or 1

        return {
            "total_leads": metrics['total_leads'],
            "stages": {
                "new": metrics['new_leads'],
                "contacted": metrics['contacted'],
                "qualified": metrics['qualified'],
                "converted": metrics['converted']
            },
            "conversion_rates": {
                "lead_to_contact": round((metrics['contacted'] / total) * 100, 2),
                "contact_to_qualified": round((metrics['qualified'] / max(metrics['contacted'], 1)) * 100, 2),
                "qualified_to_converted": round((metrics['converted'] / max(metrics['qualified'], 1)) * 100, 2),
                "overall": round((metrics['converted'] / total) * 100, 2)
            },
            "scoring": {
                "average_score": round(metrics['avg_score'] or 0, 1),
                "converted_avg_score": round(metrics['avg_converted_score'] or 0, 1)
            }
        }

    except Exception as e:
        logger.error(f"Error getting funnel analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def start_nurturing_campaign(lead_id: str, score: int):
    # Validate UUID format
    if lead_id and lead_id != "test":
        try:
            uuid.UUID(str(lead_id))
        except (ValueError, TypeError):
            logger.warning(f"Invalid UUID format: {lead_id}")
            return {"error": "Invalid ID format"}
    """
    Start automated nurturing campaign for low-scoring leads
    """
    logger.info(f"Starting nurturing campaign for lead {lead_id} with score {score}")
    # This would integrate with email marketing system
    # For now, just log the action
    pass

# Register router
__all__ = ['router']
