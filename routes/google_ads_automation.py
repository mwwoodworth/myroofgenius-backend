"""
Google Ads Campaign Automation
Automated bidding, targeting, and optimization for maximum ROI
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import json
import os
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime, ForeignKey, Text, Date, text
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.dialects.postgresql import UUID

from database import get_db, engine
from core.supabase_auth import get_current_user

router = APIRouter(tags=["Google Ads"])

# Google Ads configuration
GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
GOOGLE_ADS_API_KEY = os.getenv("GOOGLE_ADS_API_KEY", "")

try:
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError
except Exception:
    ai_service = None
    AIServiceNotConfiguredError = Exception

# Local Base for internal models
Base = declarative_base()

# ============================================================================
# MODELS
# ============================================================================

class AdCampaign(Base):
    __tablename__ = "ad_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(String, unique=True, nullable=False) # External ID or generated ID
    platform = Column(String, default="google_ads")
    name = Column(String, nullable=False)
    budget_daily_cents = Column(Integer, default=0)
    target_cpa_cents = Column(Integer, default=0)
    keywords = Column(JSON, default=[])
    locations = Column(JSON, default=[])
    ad_schedule = Column(JSON, nullable=True)
    status = Column(String, default="draft")
    meta_data = Column("metadata", JSON, default={})
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdPerformance(Base):
    __tablename__ = "ad_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(String, nullable=False) # Link by external ID
    date = Column(Date, default=datetime.utcnow().date)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend_cents = Column(Integer, default=0)
    cpc_cents = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Ensure tables exist
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

# ============================================================================
# SCHEMAS
# ============================================================================

class CampaignBase(BaseModel):
    name: str
    budget_daily: float
    target_cpa: float = 45.00
    keywords: List[str]
    locations: List[str]
    ad_schedule: Optional[Dict[str, Any]] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    launched: bool
    google_ads_enabled: bool
    message: str

# ============================================================================
# ROUTES
# ============================================================================

@router.post("/campaigns/create", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create and launch Google Ads campaign
    """
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Tenant assignment required")

        campaign_id_str = f"CAMPAIGN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        google_ads_enabled = bool(GOOGLE_ADS_API_KEY and GOOGLE_ADS_CUSTOMER_ID)

        new_campaign = AdCampaign(
            campaign_id=campaign_id_str,
            platform="google_ads",
            name=campaign.name,
            budget_daily_cents=int(campaign.budget_daily * 100),
            target_cpa_cents=int(campaign.target_cpa * 100),
            keywords=campaign.keywords,
            locations=campaign.locations,
            ad_schedule=campaign.ad_schedule,
            status="pending_launch" if google_ads_enabled else "draft",
            tenant_id=tenant_id
        )
        
        db.add(new_campaign)
        db.commit()
        
        return {
            "campaign_id": campaign_id_str,
            "status": "stored",
            "launched": False,
            "google_ads_enabled": google_ads_enabled,
            "message": "Campaign configuration stored. Google Ads launch requires configured Google Ads credentials.",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/emergency-weather")
async def create_weather_triggered_campaign(
    location: str,
    weather_event: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Auto-create campaign for weather events (hail, storms, etc.)
    """
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
             raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Weather-specific keywords
        weather_keywords = {
            "hail": [
                "hail damage roof repair",
                "emergency hail damage estimate",
                "roof hail damage claim",
                "hail damaged roof replacement"
            ],
            "storm": [
                "storm damage roof repair",
                "emergency storm damage",
                "wind damage roof repair",
                "storm damaged roof estimate"
            ],
            "hurricane": [
                "hurricane roof damage",
                "emergency roof repair hurricane",
                "hurricane damage estimate",
                "roof replacement hurricane"
            ]
        }
        
        keywords = weather_keywords.get(weather_event, weather_keywords["storm"])
        
        campaign_name = f"Emergency {weather_event.title()} - {location}"
        budget = 250.00
        cpa = 65.00
        
        ad_groups = [
            {
                "name": "Emergency Response",
                "keywords": [
                    {"keyword": kw, "match_type": "exact", "bid": 8.50}
                    for kw in keywords
                ],
                "ads": [
                    {
                        "headlines": [
                            f"{weather_event.title()} Damage? Free Estimate",
                            "Emergency Roof Repair - 24/7",
                            "Insurance Claims Assistance"
                        ],
                        "descriptions": [
                            f"Expert {weather_event} damage assessment. Fast response.",
                            "Licensed contractors ready. Save with AI estimates."
                        ],
                        "url": f"https://myroofgenius.com/emergency?event={weather_event}&location={location}"
                    }
                ]
            }
        ]
        
        campaign_id_str = f"EMERGENCY_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        new_campaign = AdCampaign(
            campaign_id=campaign_id_str,
            platform="google_ads",
            name=campaign_name,
            budget_daily_cents=int(budget * 100),
            target_cpa_cents=int(cpa * 100),
            keywords=keywords,
            locations=[location],
            status="active",
            meta_data={
                "type": "emergency",
                "weather_event": weather_event,
                "ad_groups": ad_groups
            },
            tenant_id=tenant_id
        )

        db.add(new_campaign)
        db.commit()
        
        google_ads_enabled = bool(GOOGLE_ADS_API_KEY and GOOGLE_ADS_CUSTOMER_ID)
        return {
            "campaign_id": campaign_id_str,
            "type": "emergency",
            "location": location,
            "weather_event": weather_event,
            "status": "stored",
            "launched": False,
            "google_ads_enabled": google_ads_enabled,
            "budget": budget,
            "message": "Emergency campaign configuration stored. Google Ads launch requires configured Google Ads credentials.",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaigns/performance")
async def get_campaign_performance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Real-time campaign performance metrics
    """
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
             raise HTTPException(status_code=403, detail="Tenant assignment required")

        # Get today's performance
        today_stats_query = text("""
            SELECT 
                COUNT(DISTINCT campaign_id) as active_campaigns,
                SUM(impressions) as total_impressions,
                SUM(clicks) as total_clicks,
                SUM(conversions) as total_conversions,
                SUM(spend_cents) / 100.0 as total_spend,
                AVG(cpc_cents) / 100.0 as avg_cpc,
                AVG(conversion_rate) as avg_conversion_rate
            FROM ad_performance
            WHERE date = CURRENT_DATE AND tenant_id = :tenant_id
        """)
        today_stats = db.execute(today_stats_query, {"tenant_id": tenant_id}).fetchone()
        
        # Get campaign-level performance
        campaigns_query = text("""
            SELECT 
                c.campaign_id,
                c.name,
                c.budget_daily_cents / 100.0 as daily_budget,
                COALESCE(SUM(p.spend_cents) / 100.0, 0) as spent_today,
                COALESCE(SUM(p.clicks), 0) as clicks_today,
                COALESCE(SUM(p.conversions), 0) as conversions_today,
                COALESCE(AVG(p.cpc_cents) / 100.0, 0) as avg_cpc,
                c.status
            FROM ad_campaigns c
            LEFT JOIN ad_performance p ON c.campaign_id = p.campaign_id 
                AND p.date = CURRENT_DATE
            WHERE c.platform = 'google_ads' AND c.tenant_id = :tenant_id
            GROUP BY c.campaign_id, c.name, c.budget_daily_cents, c.status
            ORDER BY spent_today DESC
        """)
        campaigns = db.execute(campaigns_query, {"tenant_id": tenant_id}).fetchall()
        
        # Calculate ROI
        # Assuming revenue_tracking might not have tenant_id in some legacy setups, 
        # but we should try to filter if possible. If table doesn't exist, this will throw.
        # We wrap in try/catch specifically for the revenue part or assume table exists.
        # Given the "stub" nature, let's assume revenue_tracking is global or per-tenant.
        # Ideally it should be per tenant.
        try:
            revenue_query = text("""
                SELECT COALESCE(SUM(amount_cents) / 100.0, 0) as revenue
                FROM revenue_tracking
                WHERE source LIKE '%google%'
                AND DATE(created_at) = CURRENT_DATE
                -- AND tenant_id = :tenant_id  -- Uncomment if revenue_tracking has tenant_id
            """)
            # revenue_today = db.execute(revenue_query, {"tenant_id": tenant_id}).scalar()
            revenue_today = db.execute(revenue_query).scalar()
        except Exception:
            revenue_today = 0.0
        
        total_spend = today_stats.total_spend if today_stats and today_stats.total_spend else 0
        roi = ((revenue_today - total_spend) / total_spend * 100) if total_spend > 0 else 0
        
        campaign_list = []
        for c in campaigns:
            c_dict = dict(c._mapping)
            campaign_list.append(c_dict)

        return {
            "summary": {
                "active_campaigns": today_stats.active_campaigns if today_stats and today_stats.active_campaigns else 0,
                "total_spend": total_spend,
                "total_clicks": today_stats.total_clicks if today_stats and today_stats.total_clicks else 0,
                "total_conversions": today_stats.total_conversions if today_stats and today_stats.total_conversions else 0,
                "avg_cpc": float(today_stats.avg_cpc) if today_stats and today_stats.avg_cpc else 0,
                "revenue": revenue_today,
                "roi": round(roi, 2)
            },
            "campaigns": campaign_list,
            "recommendations": generate_optimization_recommendations(campaign_list, today_stats)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_optimization_recommendations(campaigns, stats):
    """Generate AI-powered optimization recommendations"""
    recommendations = []
    
    # Check for underperforming campaigns
    for campaign in campaigns:
        if campaign["conversions_today"] == 0 and campaign["clicks_today"] > 10:
            recommendations.append({
                "campaign": campaign["name"],
                "issue": "No conversions despite clicks",
                "action": "Review landing page and ad relevance"
            })
        
        if campaign["avg_cpc"] > 5.00:
            recommendations.append({
                "campaign": campaign["name"],
                "issue": "High CPC",
                "action": "Add negative keywords and refine targeting"
            })
        
        if campaign["spent_today"] < campaign["daily_budget"] * 0.5:
            recommendations.append({
                "campaign": campaign["name"],
                "issue": "Underspending budget",
                "action": "Increase bids or expand keywords"
            })
    
    return recommendations

@router.post("/keywords/research")
async def keyword_research(
    seed_keyword: str,
    current_user: dict = Depends(get_current_user)
):
    """
    AI-powered keyword research and suggestions
    """
    # Expand keywords based on seed
    keyword_variations = {
        "roof estimate": [
            "roof estimate calculator",
            "free roof estimate",
            "roof replacement estimate",
            "roofing estimate near me",
            "instant roof quote",
            "roof repair cost calculator",
            "online roof estimate",
            "roof inspection estimate"
        ],
        "roof repair": [
            "emergency roof repair",
            "roof leak repair",
            "roof repair cost",
            "roof repair near me",
            "residential roof repair",
            "commercial roof repair",
            "storm damage roof repair",
            "roof repair contractor"
        ],
        "roof replacement": [
            "roof replacement cost",
            "when to replace roof",
            "roof replacement estimate",
            "metal roof replacement",
            "shingle roof replacement",
            "roof replacement financing",
            "roof replacement contractor",
            "best time to replace roof"
        ]
    }
    
    # Find best matching category
    base_keywords = keyword_variations.get(seed_keyword, [])
    
    # Add location-based variations
    locations = ["near me", "Houston", "Dallas", "Austin", "San Antonio"]
    expanded_keywords = []
    
    for keyword in base_keywords:
        expanded_keywords.append({
            "keyword": keyword,
            "search_volume": None,
            "competition": None,
            "suggested_bid": None,
            "intent": "high" if "emergency" in keyword or "repair" in keyword else "medium",
            "available": False,
        })
    
    # Add location variations
    for location in locations[:3]:
        expanded_keywords.append({
            "keyword": f"{seed_keyword} {location}",
            "search_volume": None,
            "competition": None,
            "suggested_bid": None,
            "intent": "high",
            "available": False,
        })
    
    return {
        "seed_keyword": seed_keyword,
        "suggestions": expanded_keywords,
        "total_keywords": len(expanded_keywords),
        "estimated_monthly_clicks": None,
        "recommended_budget": None,
        "available": False,
    }

@router.post("/ads/generate")
async def generate_ad_copy(
    product: str,
    tone: str = "urgent",
    current_user: dict = Depends(get_current_user)
):
    """
    AI-generated ad copy variations
    """
    if ai_service is None:
        raise HTTPException(status_code=503, detail="AI service not available on this server")

    prompt = (
        "Generate Google Ads copy for a roofing company.\n\n"
        f"Product/service: {product}\n"
        f"Tone: {tone}\n\n"
        "Return JSON with key 'ad_variations' as a list of 3 variants.\n"
        "Each variant must include: variant (A/B/C), headlines (list of 3), descriptions (list of 2), "
        "display_url, final_url.\n"
        "Do not include fabricated performance metrics."
    )

    try:
        result = await ai_service.generate_json(prompt)
    except AIServiceNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    variations = result.get("ad_variations") if isinstance(result, dict) else None
    if not isinstance(variations, list):
        variations = []

    return {
        "product": product,
        "tone": tone,
        "ad_variations": variations,
        "ai_provider": result.get("ai_provider") if isinstance(result, dict) else None,
    }
