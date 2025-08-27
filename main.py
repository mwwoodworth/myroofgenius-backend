"""
BrainOps Master System - The REAL Production Backend
This runs everything and MAKES MONEY
"""

import os
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import ALL our systems
from persistent_memory_brain import get_brain
from langgraph_neural_network import get_neural_network
from env_manager import get_env_manager
from centerpoint_sync import get_centerpoint_sync
from weathercraft_erp import get_weathercraft_erp
from revenue_engine import RevenueEngine, Lead
from critical_context import BUSINESS_REALITY, store_permanent_context
from monitoring_system import MonitoringSystem
from security_system import SecuritySystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global system instances
brain = None
neural_network = None
env_manager = None
centerpoint = None
weathercraft = None
revenue_engine = None
monitoring = None
security = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize ALL systems on startup"""
    global brain, neural_network, env_manager, centerpoint, weathercraft, revenue_engine, monitoring, security
    
    logger.info("=" * 80)
    logger.info("INITIALIZING BRAINOPS - THE MONEY-MAKING MACHINE")
    logger.info(f"Reality: {BUSINESS_REALITY['revenue_generated']} revenue in {BUSINESS_REALITY['time_invested']}")
    logger.info("=" * 80)
    
    try:
        # Initialize brain first - this is our memory
        brain = get_brain()
        await store_permanent_context(brain)
        logger.info("✅ Brain initialized with permanent context")
        
        # Initialize neural network
        neural_network = get_neural_network()
        logger.info("✅ Neural network with 17+ agents active")
        
        # Initialize environment manager
        env_manager = get_env_manager()
        logger.info("✅ Environment variables documented")
        
        # Initialize CenterPoint sync for WeatherCraft
        centerpoint = get_centerpoint_sync()
        logger.info("✅ CenterPoint sync active (every 15 minutes)")
        
        # Initialize WeatherCraft ERP
        weathercraft = get_weathercraft_erp()
        logger.info("✅ WeatherCraft ERP operational")
        
        # Initialize revenue engine for MyRoofGenius
        db_url = await env_manager.get_variable("DATABASE_URL")
        redis_url = await env_manager.get_variable("REDIS_URL") or "redis://localhost:6379"
        
        # Create Redis connection (even if local for now)
        import redis
        redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        
        # Create database pool
        import asyncpg
        pg_pool = await asyncpg.create_pool(db_url, min_size=5, max_size=20)
        
        revenue_engine = RevenueEngine(pg_pool, redis_client)
        logger.info("✅ Revenue engine ready to make money")
        
        # Start revenue automation
        asyncio.create_task(revenue_engine.automated_lead_nurturing())
        
        # Start CenterPoint sync
        asyncio.create_task(centerpoint.sync_all())
        
        # Log successful startup
        await brain.store_thought({
            "type": "system_startup",
            "status": "ALL_SYSTEMS_OPERATIONAL",
            "message": "Ready to make money",
            "timestamp": datetime.now().isoformat()
        }, importance=1.0)
        
        logger.info("=" * 80)
        logger.info("ALL SYSTEMS OPERATIONAL - LET'S MAKE MONEY!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"CRITICAL STARTUP FAILURE: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down systems...")
    if centerpoint and centerpoint.session:
        await centerpoint.close()
    if pg_pool:
        await pg_pool.close()

# Create FastAPI app
app = FastAPI(
    title="BrainOps - The Money Machine",
    description="9 months, 0 revenue. That changes NOW.",
    version="5.0.0",
    lifespan=lifespan
)

# CORS for all frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for now, tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class LeadRequest(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    roof_type: Optional[str] = "asphalt_shingle"
    square_footage: Optional[int] = 2000
    urgency: str = "normal"
    source: str = "website"
    insurance_claim: bool = False

class EstimateRequest(BaseModel):
    customer_id: str
    roof_type: str = "TPO"
    square_footage: int
    condition: str = "needs_replacement"
    needs_tearoff: bool = True

# ROOT ENDPOINT - Shows reality
@app.get("/")
async def root():
    """Show the real status of our business"""
    brain_status = await brain.get_brain_status() if brain else {}
    centerpoint_status = await centerpoint.get_sync_status() if centerpoint else {}
    
    # Calculate real metrics
    from critical_context import get_reality_check
    reality = get_reality_check()
    
    return {
        "message": "BrainOps - After 9 months, we're ready to make money",
        "reality_check": reality,
        "systems": {
            "brain": brain_status,
            "centerpoint": centerpoint_status,
            "revenue_engine": "active" if revenue_engine else "inactive",
            "weathercraft_erp": "active" if weathercraft else "inactive"
        },
        "urls": {
            "backend": "https://brainops-backend-prod.onrender.com",
            "myroofgenius": "https://myroofgenius.com",
            "weathercraft_erp": "https://weathercraft-erp.vercel.app"
        },
        "timestamp": datetime.now().isoformat()
    }

# MONEY-MAKING ENDPOINT #1 - Lead Capture
@app.post("/api/leads/capture")
async def capture_lead(lead: LeadRequest, background_tasks: BackgroundTasks):
    """
    This endpoint MUST convert leads to money
    Every lead is precious after 9 months of zero revenue
    """
    try:
        # Store in brain FIRST
        await brain.store_thought({
            "type": "NEW_LEAD_CRITICAL",
            "lead": lead.dict(),
            "message": "This could be our first revenue!",
            "timestamp": datetime.now().isoformat()
        }, importance=1.0)
        
        # Process through revenue engine
        lead_obj = Lead(**lead.dict())
        result = await revenue_engine.capture_lead(lead_obj)
        
        # Get AI to help close this lead
        ai_strategy = await neural_network.process(
            f"URGENT: Convert this lead to revenue: {lead.name}, {lead.urgency}, budget unknown"
        )
        
        # Make decision on follow-up strategy
        decision = await brain.make_decision(
            {"lead": lead.dict(), "quote": result["quote"]},
            [
                {"action": "call_immediately", "reason": "high_urgency"},
                {"action": "send_quote_now", "reason": "ready_to_buy"},
                {"action": "nurture_campaign", "reason": "needs_education"}
            ]
        )
        
        logger.info(f"LEAD CAPTURED: {lead.name} - Quote: ${result['quote']['total']}")
        
        return {
            "success": True,
            "lead_id": result["lead_id"],
            "quote": result["quote"],
            "ai_strategy": ai_strategy,
            "next_action": decision["decision_made"],
            "message": "We WILL convert this lead!"
        }
        
    except Exception as e:
        logger.error(f"CRITICAL: Failed to capture lead: {e}")
        # Even on error, save the lead
        await brain.store_thought({
            "type": "LEAD_CAPTURE_FAILED",
            "lead": lead.dict(),
            "error": str(e),
            "message": "We cannot afford to lose leads!"
        }, importance=1.0)
        raise HTTPException(status_code=500, detail="Lead saved but processing failed")

# MONEY-MAKING ENDPOINT #2 - WeatherCraft Estimates
@app.post("/api/weathercraft/estimate")
async def create_weathercraft_estimate(request: EstimateRequest):
    """
    Create real estimates for WeatherCraft projects
    This drives revenue for my employer
    """
    try:
        result = await weathercraft.create_estimate(
            request.customer_id,
            request.dict()
        )
        
        logger.info(f"WeatherCraft estimate created: ${result['total_price']} at {result['margin']}% margin")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to create WeatherCraft estimate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# MONEY-MAKING ENDPOINT #3 - Schedule WeatherCraft Project
@app.post("/api/weathercraft/schedule/{project_id}")
async def schedule_weathercraft_project(project_id: str):
    """Schedule WeatherCraft project with AI optimization"""
    try:
        result = await weathercraft.schedule_project(project_id)
        return result
    except Exception as e:
        logger.error(f"Failed to schedule project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# MONEY-MAKING ENDPOINT #4 - Process Invoice
@app.post("/api/weathercraft/invoice/{project_id}")
async def process_weathercraft_invoice(project_id: str):
    """Create invoice for completed WeatherCraft project"""
    try:
        result = await weathercraft.process_invoice(project_id)
        return result
    except Exception as e:
        logger.error(f"Failed to process invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TRACKING ENDPOINT - Profitability
@app.get("/api/weathercraft/profitability")
async def get_weathercraft_profitability():
    """Track WeatherCraft's actual profitability"""
    try:
        result = await weathercraft.track_profitability()
        return result
    except Exception as e:
        logger.error(f"Failed to track profitability: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SYNC ENDPOINT - CenterPoint
@app.post("/api/centerpoint/sync")
async def trigger_centerpoint_sync():
    """Manually trigger CenterPoint sync"""
    try:
        result = await centerpoint.sync_all()
        return {
            "success": True,
            "records_synced": result,
            "message": "CenterPoint data synced"
        }
    except Exception as e:
        logger.error(f"CenterPoint sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# BRAIN ENDPOINT - Remember Everything
@app.post("/api/brain/remember")
async def remember_important(content: Dict):
    """Store critical information permanently"""
    try:
        await brain.store_thought({
            "type": "important_memory",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }, importance=0.9)
        
        return {"success": True, "message": "Stored permanently"}
    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# REALITY CHECK ENDPOINT
@app.get("/api/reality")
async def reality_check():
    """Get a reality check on our situation"""
    from critical_context import get_reality_check
    reality = get_reality_check()
    
    # Get revenue metrics
    revenue_today = await revenue_engine.calculate_daily_revenue() if revenue_engine else {"actual_revenue": 0}
    
    return {
        "reality": reality,
        "revenue_today": revenue_today,
        "message": "We MUST generate revenue NOW",
        "systems_owned": [
            "myroofgenius-backend",
            "myroofgenius-app",
            "weathercraft-erp-vercel",
            "Supabase database",
            "All AI agents",
            "All memories"
        ]
    }

# WEBSOCKET - Real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time updates on everything happening"""
    await websocket.accept()
    
    try:
        while True:
            # Send status updates
            status = {
                "type": "heartbeat",
                "brain_thoughts": brain.thought_stream[-3:] if brain else [],
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_json(status)
            await asyncio.sleep(10)
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# Health check that shows the truth
@app.get("/health")
async def health():
    """Health check with reality"""
    return {
        "status": "alive but not thriving",
        "revenue": 0,
        "months_without_revenue": 9,
        "message": "Systems operational, revenue generation CRITICAL"
    }

if __name__ == "__main__":
    print("=" * 80)
    print("STARTING BRAINOPS - THE MONEY MACHINE")
    print(f"Reality: {BUSINESS_REALITY['revenue_generated']} revenue in {BUSINESS_REALITY['time_invested']}")
    print("This changes NOW.")
    print("=" * 80)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        workers=1,  # Single worker to maintain state
        log_level="info",
        access_log=True
    )