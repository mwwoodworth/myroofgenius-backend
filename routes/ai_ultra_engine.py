#!/usr/bin/env python3
"""
ULTRA AI ENGINE API ROUTES - NO BULLSHIT
Real AI-powered business intelligence endpoints with transformational capabilities
"""

import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from lib.ai_ultra_services import (
    analyze_lead_intelligence,
    optimize_revenue, 
    analyze_document,
    predict_business_trends,
    AIAnalysisResult,
    UltraAINotConfiguredError,
    UltraAIProviderCallError,
)
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.supabase_auth import get_current_user
from database import engine as db_engine
from database import get_db as _get_db


def get_db():
    if db_engine is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    yield from _get_db()

import json
from decimal import Decimal

# JSON encoder for Decimal and datetime
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

router = APIRouter(prefix="/api/v1/ai/ultra", tags=["Ultra AI Engine"])
logger = logging.getLogger(__name__)

@router.post("/leads/analyze")
async def ultra_lead_analysis(
    lead_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ultra-powerful lead intelligence analysis"""
    try:
        # Get enhanced lead data from database if lead_id provided
        if 'lead_id' in lead_data:
            lead_id = lead_data['lead_id']
            result = db.execute(text("""
                SELECT l.*, c.name as customer_name, c.email as customer_email
                FROM leads l
                LEFT JOIN customers c ON l.customer_id = c.id
                WHERE l.id = :lead_id
            """), {"lead_id": lead_id})
            
            db_lead = result.fetchone()
            if db_lead:
                # Merge database data with provided data
                enhanced_data = dict(db_lead._mapping)
                enhanced_data.update(lead_data)
                lead_data = enhanced_data
        
        # Ultra AI analysis
        ai_result = await analyze_lead_intelligence(lead_data)
        
        # Update database with AI insights if lead_id provided
        lead_score = ai_result.metadata.get("lead_score")
        try:
            lead_score_num = float(lead_score) if lead_score is not None else None
        except Exception:
            lead_score_num = None

        if 'lead_id' in lead_data and ai_result.confidence > 0.7 and lead_score_num is not None:
            db.execute(text("""
                UPDATE leads 
                SET lead_score = :score,
                    lead_grade = :grade,
                    priority = :priority,
                    ai_analysis = :analysis,
                    last_activity_at = NOW(),
                    updated_at = NOW()
                WHERE id = :lead_id
            """), {
                "score": lead_score_num,
                "grade": "A" if lead_score_num >= 90 else "B" if lead_score_num >= 75 else "C" if lead_score_num >= 60 else "D",
                "priority": ai_result.metadata.get("priority", "medium"),
                "analysis": ai_result.analysis,
                "lead_id": lead_data['lead_id']
            })
            db.commit()
        
        return {
            "success": True,
            "ai_analysis": {
                "confidence": ai_result.confidence,
                "analysis": ai_result.analysis,
                "recommendations": ai_result.recommendations,
                "lead_score": ai_result.metadata.get("lead_score"),
                "priority": ai_result.metadata.get("priority"),
                "conversion_probability": ai_result.metadata.get("conversion_probability"),
                "revenue_potential": ai_result.metadata.get("revenue_potential"),
                "processing_time": ai_result.processing_time,
                "ai_providers": ai_result.metadata.get("ai_providers_used", [])
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except UltraAINotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except UltraAIProviderCallError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Ultra lead analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ultra AI analysis failed: {str(e)}")

@router.post("/revenue/optimize")
async def ultra_revenue_optimization(
    optimization_request: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ultra-powerful revenue optimization with predictive analytics"""
    try:
        # Gather comprehensive business data
        business_metrics = {}
        
        # Get revenue data
        revenue_result = db.execute(text("""
            SELECT 
                COUNT(DISTINCT c.id) as total_customers,
                COALESCE(SUM(i.total_cents), 0) / 100.0 as total_revenue,
                COALESCE(AVG(i.total_cents), 0) / 100.0 as avg_deal_size,
                COUNT(DISTINCT i.id) as total_invoices
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            WHERE i.status IN ('paid', 'completed')
        """))
        
        revenue_data = revenue_result.fetchone()
        if revenue_data:
            business_metrics.update(dict(revenue_data._mapping))
        
        # Get lead conversion data
        lead_result = db.execute(text("""
            SELECT 
                COUNT(*) as total_leads,
                COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted_leads,
                AVG(lead_score) as avg_lead_score,
                SUM(estimated_value) as pipeline_value
            FROM leads
            WHERE created_at > NOW() - INTERVAL '6 months'
        """))
        
        lead_data = lead_result.fetchone()
        if lead_data:
            business_metrics.update(dict(lead_data._mapping))
            if business_metrics.get('total_leads', 0) > 0:
                business_metrics['conversion_rate'] = (
                    business_metrics.get('converted_leads', 0) / 
                    business_metrics['total_leads']
                )
        
        # Merge with request data
        business_metrics.update(optimization_request)
        
        # Ultra AI optimization
        ai_result = await optimize_revenue(business_metrics)
        
        # Store optimization insights (convert Decimals to float)
        business_metrics_clean = {k: float(v) if isinstance(v, Decimal) else v for k, v in business_metrics.items()}
        
        optimization_record = {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "analysis_type": "revenue_optimization",
            "input_data": json.dumps(business_metrics_clean, cls=JSONEncoder),
            "ai_confidence": ai_result.confidence,
            "ai_analysis": ai_result.analysis,
            "recommendations": json.dumps(ai_result.recommendations),
            "processing_time": ai_result.processing_time,
            "created_at": datetime.now()
        }
        
        return {
            "success": True,
            "revenue_optimization": {
                "confidence": ai_result.confidence,
                "analysis": ai_result.analysis,
                "recommendations": ai_result.recommendations,
                "projected_growth": ai_result.metadata.get("projected_growth"),
                "optimization_score": ai_result.metadata.get("optimization_score"),
                "revenue_forecast": ai_result.metadata.get("revenue_forecast"),
                "priority_actions": ai_result.metadata.get("priority_actions"),
                "processing_time": ai_result.processing_time
            },
            "business_metrics": business_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except UltraAINotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except UltraAIProviderCallError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Ultra revenue optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Revenue optimization failed: {str(e)}")

@router.post("/documents/analyze")
async def ultra_document_intelligence(
    file: UploadFile = File(...),
    analysis_type: str = "general",
) -> Dict[str, Any]:
    """Ultra-powerful document analysis with GPT-4 Vision"""
    try:
        # Read document data
        document_data = await file.read()
        
        # Determine document type
        file_extension = file.filename.split('.')[-1].lower() if file.filename else "unknown"
        
        # Ultra AI document analysis
        ai_result = await analyze_document(document_data, file_extension)
        
        return {
            "success": True,
            "document_analysis": {
                "filename": file.filename,
                "file_size": len(document_data),
                "document_type": file_extension,
                "confidence": ai_result.confidence,
                "analysis": ai_result.analysis,
                "recommendations": ai_result.recommendations,
                "vision_analysis": ai_result.metadata.get("vision_analysis", False),
                "processing_time": ai_result.processing_time
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UltraAINotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except UltraAIProviderCallError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Ultra document intelligence failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {str(e)}")

@router.post("/predictions/analyze")
async def ultra_predictive_analytics(
    prediction_request: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ultra-advanced predictive analytics for business forecasting"""
    try:
        # Gather comprehensive historical data
        historical_data = {}
        
        # Revenue trends (12 months)
        revenue_trend = db.execute(text("""
            SELECT 
                DATE_TRUNC('month', created_at) as month,
                COUNT(DISTINCT customer_id) as customers,
                COALESCE(SUM(total_cents), 0) / 100.0 as revenue,
                COUNT(*) as invoices
            FROM invoices
            WHERE created_at > NOW() - INTERVAL '12 months'
              AND status IN ('paid', 'completed')
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month
        """))
        
        revenue_trends = []
        for row in revenue_trend.fetchall():
            trend_data = dict(row._mapping)
            # Convert datetime and Decimal objects
            if 'month' in trend_data and hasattr(trend_data['month'], 'isoformat'):
                trend_data['month'] = trend_data['month'].isoformat()
            if 'revenue' in trend_data and isinstance(trend_data['revenue'], Decimal):
                trend_data['revenue'] = float(trend_data['revenue'])
            revenue_trends.append(trend_data)
        
        historical_data['revenue_trends'] = revenue_trends
        
        # Lead conversion trends
        lead_trend = db.execute(text("""
            SELECT 
                DATE_TRUNC('month', created_at) as month,
                COUNT(*) as total_leads,
                COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted_leads,
                AVG(lead_score) as avg_score
            FROM leads
            WHERE created_at > NOW() - INTERVAL '12 months'
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month
        """))
        
        lead_trends = []
        for row in lead_trend.fetchall():
            trend_data = dict(row._mapping)
            # Convert datetime and Decimal objects
            if 'month' in trend_data and hasattr(trend_data['month'], 'isoformat'):
                trend_data['month'] = trend_data['month'].isoformat()
            for key in ['avg_score']:
                if key in trend_data and isinstance(trend_data[key], Decimal):
                    trend_data[key] = float(trend_data[key])
            lead_trends.append(trend_data)
        
        historical_data['lead_trends'] = lead_trends
        
        # Customer behavior patterns
        customer_patterns = db.execute(text("""
            SELECT 
                c.id,
                c.created_at as customer_since,
                COUNT(i.id) as total_invoices,
                COALESCE(SUM(i.total_cents), 0) / 100.0 as total_spent,
                COALESCE(AVG(i.total_cents), 0) / 100.0 as avg_invoice,
                MAX(i.created_at) as last_purchase
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            WHERE c.created_at > NOW() - INTERVAL '12 months'
            GROUP BY c.id, c.created_at
            HAVING COUNT(i.id) > 0
        """))
        
        customer_data = []
        for row in customer_patterns.fetchall():
            cust_data = dict(row._mapping)
            # Convert datetime and Decimal objects
            for key in ['customer_since', 'last_purchase']:
                if key in cust_data and hasattr(cust_data[key], 'isoformat'):
                    cust_data[key] = cust_data[key].isoformat()
            for key in ['total_spent', 'avg_invoice']:
                if key in cust_data and isinstance(cust_data[key], Decimal):
                    cust_data[key] = float(cust_data[key])
            customer_data.append(cust_data)
        
        historical_data['customer_patterns'] = customer_data
        
        # Merge with request data
        historical_data.update(prediction_request)
        
        # Ultra AI predictive analysis
        ai_result = await predict_business_trends(historical_data)
        
        return {
            "success": True,
            "predictive_analytics": {
                "confidence": ai_result.confidence,
                "analysis": ai_result.analysis,
                "recommendations": ai_result.recommendations,
                "forecast_accuracy": ai_result.metadata.get("forecast_accuracy"),
                "prediction_horizon": ai_result.metadata.get("prediction_horizon"),
                "model_type": ai_result.metadata.get("model_type"),
                "processing_time": ai_result.processing_time
            },
            "data_points_analyzed": {
                "revenue_months": len(revenue_trends),
                "lead_months": len(lead_trends),
                "customer_records": len(customer_data)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except UltraAINotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except UltraAIProviderCallError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Ultra predictive analytics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Predictive analysis failed: {str(e)}")

@router.get("/status")
async def ultra_ai_status(current_user = Depends(get_current_user)) -> Dict[str, Any]:
    """Get Ultra AI Engine status and capabilities"""
    try:
        from lib.ai_ultra_services import ultra_ai
        
        return {
            "success": True,
            "ultra_ai_status": {
                "initialized": ultra_ai.initialized,
                "openai_available": ultra_ai.openai_client is not None,
                "anthropic_available": ultra_ai.anthropic_client is not None,
                "gemini_available": ultra_ai.gemini_model is not None,
                "capabilities": [
                    "ultra_lead_intelligence",
                    "ultra_revenue_optimization", 
                    "ultra_document_intelligence",
                    "ultra_predictive_analytics"
                ],
                "ai_providers": [
                    provider for provider, available in [
                        ("GPT-4", ultra_ai.openai_client is not None),
                        ("Claude-3", ultra_ai.anthropic_client is not None),
                        ("Gemini-1.5", ultra_ai.gemini_model is not None)
                    ] if available
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ultra AI status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/workflow/automate")
async def ultra_workflow_automation(
    workflow_request: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Ultra-powerful workflow automation with AI orchestration"""
    try:
        workflow_type = workflow_request.get("type", "general")
        workflow_data = workflow_request.get("data", {})
        
        # Define ultra-powerful workflows
        automation_results = []
        
        if workflow_type == "lead_to_customer":
            # Automated lead conversion workflow
            lead_id = workflow_data.get("lead_id")
            if lead_id:
                # 1. Analyze lead with AI
                lead_result = db.execute(text("SELECT * FROM leads WHERE id = :id"), {"id": lead_id})
                lead = lead_result.fetchone()
                
                if lead:
                    lead_data = dict(lead._mapping)
                    ai_analysis = await analyze_lead_intelligence(lead_data)
                    
                    # 2. Auto-convert high-scoring leads
                    if ai_analysis.metadata.get("lead_score", 0) >= 80:
                        # Create customer record
                        customer_result = db.execute(text("""
                            INSERT INTO customers (name, email, phone, created_at)
                            VALUES (:name, :email, :phone, NOW())
                            RETURNING id
                        """), {
                            "name": lead_data["company_name"],
                            "email": lead_data["email"], 
                            "phone": lead_data["phone"]
                        })
                        
                        customer_id = customer_result.fetchone()[0]
                        
                        # Update lead status
                        db.execute(text("""
                            UPDATE leads 
                            SET status = 'converted', customer_id = :customer_id, updated_at = NOW()
                            WHERE id = :lead_id
                        """), {"customer_id": customer_id, "lead_id": lead_id})
                        
                        db.commit()
                        
                        automation_results.append({
                            "action": "auto_conversion",
                            "lead_id": lead_id,
                            "customer_id": customer_id,
                            "ai_score": ai_analysis.metadata.get("lead_score"),
                            "success": True
                        })
        
        elif workflow_type == "revenue_optimization":
            # Automated revenue optimization workflow
            
            # 1. Identify underperforming customers
            underperformers = db.execute(text("""
                SELECT c.id, c.name, c.email,
                       COUNT(i.id) as invoice_count,
                       COALESCE(SUM(i.total_cents), 0) / 100.0 as total_spent,
                       MAX(i.created_at) as last_purchase
                FROM customers c
                LEFT JOIN invoices i ON c.id = i.customer_id
                WHERE c.created_at < NOW() - INTERVAL '90 days'
                GROUP BY c.id, c.name, c.email
                HAVING COALESCE(SUM(i.total_cents), 0) < 50000  -- Less than $500
                OR MAX(i.created_at) < NOW() - INTERVAL '60 days'
                ORDER BY last_purchase ASC NULLS FIRST
                LIMIT 20
            """))
            
            for customer in underperformers.fetchall():
                customer_data = dict(customer._mapping)
                
                # AI-powered re-engagement strategy
                reengagement_analysis = await optimize_revenue({
                    "customer_data": customer_data,
                    "analysis_type": "reengagement"
                })
                
                automation_results.append({
                    "action": "reengagement_strategy",
                    "customer_id": customer_data["id"],
                    "customer_name": customer_data["name"],
                    "ai_recommendations": reengagement_analysis.recommendations,
                    "success": True
                })
        
        return {
            "success": True,
            "workflow_automation": {
                "workflow_type": workflow_type,
                "actions_executed": len(automation_results),
                "automation_results": automation_results,
                "ai_orchestrated": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except UltraAINotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except UltraAIProviderCallError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Ultra workflow automation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow automation failed: {str(e)}")
