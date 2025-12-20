"""
AI Intelligence Routes for MyRoofGenius
Complete AI-native functionality with revenue optimization
NOW WITH REAL AI - No more fake data!
"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import base64
import os
import sys

# Set up logger
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

# Import REAL AI service with fallback
try:
    # Import from ai_services directory
    from ai_services.real_ai_integration import (
        ai_service,
        AIServiceError,
        AIServiceNotConfiguredError,
        AIProviderCallError,
    )
    logger.info("Successfully imported real AI service from ai_services")
except ImportError as e:
    logger.error("AI service module not available: %s", e)
    ai_service = None
    AIServiceError = Exception  # type: ignore
    AIServiceNotConfiguredError = Exception  # type: ignore
    AIProviderCallError = Exception  # type: ignore

router = APIRouter(prefix="/api/v1/ai", tags=["AI Intelligence"])
APP_START_TIME = datetime.utcnow()

# AI Models
class RoofAnalysisRequest(BaseModel):
    image_url: Optional[str] = None
    address: Optional[str] = None
    urgency: Optional[str] = "normal"
    customer_id: Optional[str] = None

class AIResponse(BaseModel):
    success: bool
    analysis: Dict[str, Any]
    recommendations: List[str]
    confidence: float
    metadata: Optional[Dict[str, Any]] = None

class LeadScoringRequest(BaseModel):
    lead_data: Dict[str, Any]
    behavior_signals: Optional[List[str]] = []

class RevenueOptimizationRequest(BaseModel):
    customer_id: str
    product_id: str
    market_data: Optional[Dict[str, Any]] = None

# Core AI Endpoints
@router.post("/analyze-roof", response_model=AIResponse)
async def analyze_roof(data: RoofAnalysisRequest, file: Optional[UploadFile] = None):
    """
    REAL AI-powered roof analysis using GPT-4 Vision, Claude 3, or Gemini
    Returns actual AI analysis - NOT random data!
    """
    try:
        # Get image data
        image_data = None
        
        if file:
            # Handle uploaded file
            contents = await file.read()
            image_data = base64.b64encode(contents).decode('utf-8')
        elif data.image_url:
            # Handle base64 image from URL
            if data.image_url.startswith('data:image'):
                # Extract base64 data from data URL
                image_data = data.image_url.split(',')[1]
            else:
                # Assume it's already base64
                image_data = data.image_url
        
        if not image_data:
            raise HTTPException(status_code=400, detail="No image provided for analysis")

        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")
        
        # Use REAL AI service for analysis
        metadata = {
            "address": data.address,
            "urgency": data.urgency,
            "customer_id": data.customer_id
        }
        
        # Get REAL AI analysis
        analysis = await ai_service.analyze_roof_image(image_data, metadata)
        
        # Generate intelligent recommendations based on real analysis
        recommendations = []
        
        if analysis.get("condition_score", 0) < 50:
            recommendations.append("⚠️ URGENT: Roof requires immediate attention to prevent major damage")
            recommendations.append("Schedule emergency inspection within 48 hours")
        elif analysis.get("condition_score", 0) < 70:
            recommendations.append("Plan for roof replacement within 6-12 months")
            recommendations.append("Get multiple contractor quotes for comparison")
        else:
            recommendations.append("Roof is in good condition - maintain regular inspections")
        
        # Add specific recommendations based on damage
        if analysis.get("damage_detected"):
            for damage in analysis["damage_detected"]:
                if damage.get("severity") == "severe":
                    recommendations.append(f"Critical: Repair {damage['type']} immediately")
                elif damage.get("severity") == "moderate":
                    recommendations.append(f"Important: Address {damage['type']} within 30 days")
        
        return AIResponse(
            success=True,
            analysis=analysis,
            recommendations=recommendations[:5],  # Top 5 recommendations
            confidence=analysis.get("confidence"),
            metadata={
                "analysis_id": analysis.get("analysis_id", f"ROOF-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "processing_time": analysis.get("processing_time"),
                "model_version": "3.0.0-REAL-AI",
                "ai_provider": analysis.get("ai_provider"),
            }
        )
    except Exception as e:
        logger.error(f"Real AI roof analysis error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        if isinstance(e, AIServiceNotConfiguredError):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=f"AI Analysis Error: {str(e)}")

@router.post("/score-lead")
async def score_lead(data: LeadScoringRequest):
    """
    REAL AI-powered lead scoring using machine learning
    Not random - actual intelligent analysis!
    """
    try:
        lead_data = data.lead_data
        signals = data.behavior_signals or []

        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")
        
        # Use REAL AI service for intelligent lead scoring
        result = await ai_service.score_lead(lead_data, signals)
        
        result.setdefault("success", True)
        return result
        
    except Exception as e:
        logger.error(f"Real AI lead scoring error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        if isinstance(e, AIServiceNotConfiguredError):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-revenue")
async def optimize_revenue(data: RevenueOptimizationRequest):
    """
    AI-driven revenue optimization with dynamic pricing
    """
    try:
        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")

        business_data = {
            "customer_id": data.customer_id,
            "product_id": data.product_id,
            "market_data": data.market_data or {},
        }
        return await ai_service.optimize_revenue(business_data)
    except Exception as e:
        logger.error(f"Revenue optimization error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        if isinstance(e, AIServiceNotConfiguredError):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/churn-prediction/{customer_id}")
async def predict_churn(customer_id: str, db: Session = Depends(get_db)):
    """
    REAL AI-powered churn prediction using actual customer data
    """
    try:
        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")

        # Get real customer data from database
        customer_data = {}

        query = text(
            """
            SELECT 
                c.id,
                c.email,
                COUNT(DISTINCT DATE(s.created_at)) as days_active,
                COUNT(s.id) as total_sessions,
                MAX(s.created_at) as last_login,
                EXTRACT(DAY FROM NOW() - MAX(s.created_at)) as days_since_login,
                COUNT(DISTINCT i.id) as total_invoices,
                COUNT(DISTINCT CASE WHEN i.status = 'overdue' THEN i.id END) as overdue_invoices
            FROM customers c
            LEFT JOIN user_sessions s ON c.id = s.user_id
            LEFT JOIN invoices i ON c.id = i.customer_id
            WHERE c.id = :customer_id
            GROUP BY c.id, c.email
            """
        )

        result = db.execute(query, {"customer_id": customer_id}).first()
        if not result:
            raise HTTPException(status_code=404, detail="Customer not found")

        customer_data = {
            "customer_id": str(result.id),
            "days_since_login": int(result.days_since_login) if result.days_since_login else None,
            "total_sessions": int(result.total_sessions or 0),
            "monthly_usage": int(result.days_active or 0),
            "failed_payments": int(result.overdue_invoices or 0),
            "unresolved_tickets": 0,
        }
        
        # Use REAL AI service for churn prediction
        prediction = await ai_service.predict_churn(customer_data)
        
        return {
            "success": True,
            "customer_id": customer_id,
            "churn_risk": prediction.get("risk_score"),
            "risk_factors": prediction.get("risk_factors"),
            "retention_strategy": prediction.get("retention_strategy"),
            "predicted_ltv": prediction.get("predicted_ltv"),
            "recommended_actions": (prediction.get("retention_strategy") or {}).get("tactics", []),
            "ai_powered": True,
            "analysis_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Real AI churn prediction error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        if isinstance(e, AIServiceNotConfiguredError):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-content")
async def generate_marketing_content(topic: str = "roofing", style: str = "professional"):
    """
    REAL AI-powered content generation for marketing
    Uses actual LLMs to create unique, high-quality content
    """
    try:
        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")

        # Use REAL AI service for content generation
        content_data = await ai_service.generate_content(topic, style)
        content_data.setdefault("success", True)
        content_data["topic"] = topic
        content_data["style"] = style
        return content_data
        
    except Exception as e:
        logger.error(f"Real AI content generation error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        if isinstance(e, AIServiceNotConfiguredError):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-health")
async def get_system_health(db: Session = Depends(get_db)):
    """
    AI system health monitoring and self-management status
    NOW WITH REAL METRICS - Not random!
    """
    try:
        now = datetime.utcnow()
        uptime_seconds = (now - APP_START_TIME).total_seconds()

        ai_providers = {
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
            "anthropic": "configured" if os.getenv("ANTHROPIC_API_KEY") else "not_configured",
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "not_configured",
        }

        daily_analyses = None
        try:
            roof_analyses = db.execute(
                text("SELECT COUNT(*) FROM roof_analyses WHERE created_at >= CURRENT_DATE")
            ).scalar()
            daily_analyses = int(roof_analyses or 0)
        except Exception:
            daily_analyses = None

        revenue_metrics = {"mrr": None, "growth_rate": None, "churn_rate": None, "arpu": None, "ltv": None}
        try:
            latest = db.execute(
                text(
                    """
                    SELECT mrr, churn_rate, ltv
                    FROM revenue_metrics
                    ORDER BY metric_date DESC
                    LIMIT 1
                    """
                )
            ).first()
            if latest:
                revenue_metrics["mrr"] = float(latest.mrr) if latest.mrr is not None else None
                revenue_metrics["churn_rate"] = float(latest.churn_rate) if latest.churn_rate is not None else None
                revenue_metrics["ltv"] = float(latest.ltv) if latest.ltv is not None else None
        except Exception:
            pass

        # Growth based on paid invoices (last 30 days vs prior 30 days).
        try:
            last_30 = float(
                db.execute(
                    text(
                        """
                        SELECT COALESCE(SUM(COALESCE(total_amount, 0)), 0)
                        FROM invoices
                        WHERE status = 'paid'
                          AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                        """
                    )
                ).scalar()
                or 0
            )
            prior_30 = float(
                db.execute(
                    text(
                        """
                        SELECT COALESCE(SUM(COALESCE(total_amount, 0)), 0)
                        FROM invoices
                        WHERE status = 'paid'
                          AND created_at >= CURRENT_DATE - INTERVAL '60 days'
                          AND created_at < CURRENT_DATE - INTERVAL '30 days'
                        """
                    )
                ).scalar()
                or 0
            )
            if prior_30 > 0:
                revenue_metrics["growth_rate"] = round(((last_30 - prior_30) / prior_30) * 100, 2)
        except Exception:
            pass

        # ARPU when MRR is available.
        if revenue_metrics["mrr"] is not None:
            try:
                active_subs = db.execute(text("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")).scalar()
                if active_subs:
                    revenue_metrics["arpu"] = round(revenue_metrics["mrr"] / float(active_subs), 2)
            except Exception:
                pass

        return {
            "status": "healthy",
            "uptime_seconds": round(uptime_seconds, 2),
            "metrics": {
                "daily_analyses": daily_analyses,
                "model_version": "3.0.0-REAL-AI",
                "ai_providers": ai_providers,
            },
            "revenue_metrics": revenue_metrics,
            "automation_status": {},
            "recommendations": [],
            "last_updated": now.isoformat(),
        }
    except Exception as e:
        logger.error(f"System health error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-automation")
async def execute_automation(automation_type: str, background_tasks: BackgroundTasks):
    """
    Execute automated growth and optimization tasks
    """
    raise HTTPException(
        status_code=501,
        detail="Automation execution requires a configured worker/queue and is not enabled on this server",
    )

@router.post("/recommendations", response_model=AIResponse)
async def get_ai_recommendations(
    user_id: str = Body(..., embed=True),
    context: Optional[str] = Body("dashboard", embed=True)
):
    """
    Get AI-powered recommendations for a user
    """
    try:
        if ai_service is None:
            raise HTTPException(status_code=503, detail="AI service not available on this server")

        prompt = (
            "You are an assistant for a roofing ERP/SaaS product.\n\n"
            f"User ID: {user_id}\n"
            f"Context: {context}\n\n"
            "Return JSON with key 'recommendations' as a list of 1-5 items. "
            "Each item must include: id, title, description, action, priority, potential_impact."
        )
        result = await ai_service.generate_json(prompt)
        return {
            "success": True,
            "result": {
                **result,
                "user_id": user_id,
                "context": context,
                "generated_at": datetime.now().isoformat(),
            },
            "metadata": {"ai_provider": result.get("ai_provider")},
        }
    except Exception as e:
        logger.error(f"Recommendations error: {str(e)}")
        if isinstance(e, HTTPException):
            raise
        if isinstance(e, AIServiceNotConfiguredError):
            raise HTTPException(status_code=503, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
