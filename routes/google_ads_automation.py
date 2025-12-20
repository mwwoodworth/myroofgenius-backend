"""
Google Ads Campaign Automation
Automated bidding, targeting, and optimization for maximum ROI
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
from sqlalchemy import text
import httpx
import asyncio

router = APIRouter(tags=["Google Ads"])

# Google Ads configuration (would use actual API in production)
GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")
GOOGLE_ADS_API_KEY = os.getenv("GOOGLE_ADS_API_KEY", "")

try:
    from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError
except Exception:
    ai_service = None
    AIServiceNotConfiguredError = Exception  # type: ignore

class Campaign(BaseModel):
    name: str
    budget_daily: float
    target_cpa: float = 45.00  # Target cost per acquisition
    keywords: List[str]
    locations: List[str]
    ad_schedule: Optional[Dict[str, Any]] = None

class AdGroup(BaseModel):
    campaign_id: str
    name: str
    keywords: List[Dict[str, Any]]  # keyword, match_type, bid
    ads: List[Dict[str, Any]]  # headlines, descriptions, urls

def get_db():
    from database import engine as db_engine

    if db_engine is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return db_engine

@router.post("/campaigns/create")
async def create_campaign(campaign: Campaign, background_tasks: BackgroundTasks):
    """
    Create and launch Google Ads campaign
    """
    campaign_id = f"CAMPAIGN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    google_ads_enabled = bool(GOOGLE_ADS_API_KEY and GOOGLE_ADS_CUSTOMER_ID)

    # Store campaign configuration (does not launch Google Ads without integration)
    with get_db().connect() as conn:
        conn.execute(text("""
            INSERT INTO ad_campaigns (
                campaign_id,
                platform,
                name,
                budget_daily_cents,
                target_cpa_cents,
                keywords,
                locations,
                ad_schedule,
                status,
                created_at
            ) VALUES (
                :campaign_id,
                'google_ads',
                :name,
                :budget,
                :target_cpa,
                :keywords,
                :locations,
                :ad_schedule,
                :status,
                NOW()
            )
        """), {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "budget": int(campaign.budget_daily * 100),
            "target_cpa": int(campaign.target_cpa * 100),
            "keywords": json.dumps(campaign.keywords),
            "locations": json.dumps(campaign.locations),
            "ad_schedule": json.dumps(campaign.ad_schedule) if campaign.ad_schedule else None,
            "status": "pending_launch" if google_ads_enabled else "draft",
        })
        conn.commit()
    
    return {
        "campaign_id": campaign_id,
        "status": "stored",
        "launched": False,
        "google_ads_enabled": google_ads_enabled,
        "message": "Campaign configuration stored. Google Ads launch requires configured Google Ads credentials.",
    }

@router.post("/campaigns/emergency-weather")
async def create_weather_triggered_campaign(location: str, weather_event: str):
    """
    Auto-create campaign for weather events (hail, storms, etc.)
    """
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
    
    # Create high-urgency campaign
    campaign = Campaign(
        name=f"Emergency {weather_event.title()} - {location}",
        budget_daily=250.00,  # Higher budget for emergencies
        target_cpa=65.00,  # Higher CPA acceptable for emergency leads
        keywords=keywords,
        locations=[location],
        ad_schedule={
            "always_on": True,  # 24/7 for emergencies
            "bid_modifier": 1.5  # 50% higher bids
        }
    )
    
    campaign_id = f"EMERGENCY_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Create ad groups with emergency messaging
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
    
    # Store campaign
    with get_db().connect() as conn:
        conn.execute(text("""
            INSERT INTO ad_campaigns (
                campaign_id, platform, name, budget_daily_cents,
                target_cpa_cents, keywords, locations, status, 
                metadata, created_at
            ) VALUES (
                :campaign_id, 'google_ads', :name, :budget,
                :target_cpa, :keywords, :locations, 'active',
                :metadata, NOW()
            )
        """), {
            "campaign_id": campaign_id,
            "name": campaign.name,
            "budget": int(campaign.budget_daily * 100),
            "target_cpa": int(campaign.target_cpa * 100),
            "keywords": json.dumps(keywords),
            "locations": json.dumps([location]),
            "metadata": json.dumps({
                "type": "emergency",
                "weather_event": weather_event,
                "ad_groups": ad_groups
            })
        })
        conn.commit()
    
    google_ads_enabled = bool(GOOGLE_ADS_API_KEY and GOOGLE_ADS_CUSTOMER_ID)
    return {
        "campaign_id": campaign_id,
        "type": "emergency",
        "location": location,
        "weather_event": weather_event,
        "status": "stored",
        "launched": False,
        "google_ads_enabled": google_ads_enabled,
        "budget": campaign.budget_daily,
        "message": "Emergency campaign configuration stored. Google Ads launch requires configured Google Ads credentials.",
    }

@router.get("/campaigns/performance")
async def get_campaign_performance():
    """
    Real-time campaign performance metrics
    """
    with get_db().connect() as conn:
        # Get today's performance
        today_stats = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT campaign_id) as active_campaigns,
                SUM(impressions) as total_impressions,
                SUM(clicks) as total_clicks,
                SUM(conversions) as total_conversions,
                SUM(spend_cents) / 100.0 as total_spend,
                AVG(cpc_cents) / 100.0 as avg_cpc,
                AVG(conversion_rate) as avg_conversion_rate
            FROM ad_performance
            WHERE date = CURRENT_DATE
        """)).fetchone()
        
        # Get campaign-level performance
        campaigns = conn.execute(text("""
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
            WHERE c.platform = 'google_ads'
            GROUP BY c.campaign_id, c.name, c.budget_daily_cents, c.status
            ORDER BY spent_today DESC
        """)).fetchall()
        
        # Calculate ROI
        revenue_today = conn.execute(text("""
            SELECT COALESCE(SUM(amount_cents) / 100.0, 0) as revenue
            FROM revenue_tracking
            WHERE source LIKE '%google%'
            AND DATE(created_at) = CURRENT_DATE
        """)).scalar()
        
        total_spend = today_stats["total_spend"] if today_stats else 0
        roi = ((revenue_today - total_spend) / total_spend * 100) if total_spend > 0 else 0
        
        return {
            "summary": {
                "active_campaigns": today_stats["active_campaigns"] if today_stats else 0,
                "total_spend": total_spend,
                "total_clicks": today_stats["total_clicks"] if today_stats else 0,
                "total_conversions": today_stats["total_conversions"] if today_stats else 0,
                "avg_cpc": today_stats["avg_cpc"] if today_stats else 0,
                "revenue": revenue_today,
                "roi": round(roi, 2)
            },
            "campaigns": [dict(c._mapping) for c in campaigns],
            "recommendations": generate_optimization_recommendations(campaigns, today_stats)
        }

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

async def optimize_campaign(campaign_id: str):
    """
    Background task stub (not enabled without a worker/queue)
    """
    return

@router.post("/keywords/research")
async def keyword_research(seed_keyword: str):
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
async def generate_ad_copy(product: str, tone: str = "urgent"):
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

# Database tables needed
"""
CREATE TABLE IF NOT EXISTS ad_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50) UNIQUE,
    platform VARCHAR(20),
    name VARCHAR(255),
    budget_daily_cents INTEGER,
    target_cpa_cents INTEGER,
    keywords JSONB,
    locations JSONB,
    ad_schedule JSONB,
    status VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
) RETURNING * RETURNING *;

CREATE TABLE IF NOT EXISTS ad_performance (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50),
    date DATE,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    spend_cents INTEGER DEFAULT 0,
    cpc_cents INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ad_perf_campaign ON ad_performance(campaign_id, date);
"""
