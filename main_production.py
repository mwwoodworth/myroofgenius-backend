"""
MyRoofGenius Production Backend - Complete AI OS
The unified backend that powers everything
"""

import os
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta, UTC
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import asyncpg
import redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

# Import our core systems
from ai_os_core import AIOS, get_ai_os, AgentType, Lead
from revenue_engine import RevenueEngine, Lead as RevenueLead
from infrastructure_manager import InfrastructureManager
from monitoring_system import MonitoringSystem
from security_system import SecuritySystem
from deployment_system import DeploymentSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/myroofgenius/app.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    environment=os.getenv("ENVIRONMENT", "production")
)

# Metrics for monitoring
request_count = Counter('app_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('app_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
active_users = Gauge('app_active_users', 'Active users')
revenue_total = Gauge('app_revenue_total', 'Total revenue')
lead_conversion = Gauge('app_lead_conversion_rate', 'Lead conversion rate')
ai_agents_active = Gauge('app_ai_agents_active', 'Active AI agents')

# Global instances
ai_os: Optional[AIOS] = None
revenue_engine: Optional[RevenueEngine] = None
infrastructure: Optional[InfrastructureManager] = None
monitoring: Optional[MonitoringSystem] = None
security: Optional[SecuritySystem] = None
deployment: Optional[DeploymentSystem] = None
pg_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None

# WebSocket connections for real-time updates
websocket_connections: List[WebSocket] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    global ai_os, revenue_engine, infrastructure, monitoring, security, deployment, pg_pool, redis_client
    
    logger.info("Starting MyRoofGenius AI OS...")
    
    try:
        # Database connection
        pg_pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL"),
            min_size=10,
            max_size=50,
            command_timeout=60
        )
        
        # Redis connection
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
            connection_pool=redis.BlockingConnectionPool(max_connections=50)
        )
        
        # Initialize database schema
        await initialize_database_schema(pg_pool)
        
        # Initialize AI OS
        ai_os = AIOS(industry="roofing", company_name="MyRoofGenius")
        await ai_os.initialize_connections()
        
        # Initialize Revenue Engine
        revenue_engine = RevenueEngine(pg_pool, redis_client)
        
        # Initialize Infrastructure Manager
        infrastructure = InfrastructureManager(pg_pool, redis_client)
        await infrastructure.initialize()
        
        # Initialize Monitoring System
        monitoring = MonitoringSystem(pg_pool, redis_client)
        await monitoring.start()
        
        # Initialize Security System
        security = SecuritySystem(pg_pool, redis_client)
        await security.initialize()
        
        # Initialize Deployment System
        deployment = DeploymentSystem(pg_pool, redis_client)
        
        # Start background tasks
        asyncio.create_task(revenue_engine.automated_lead_nurturing())
        asyncio.create_task(monitoring.continuous_monitoring())
        asyncio.create_task(security.continuous_security_scan())
        asyncio.create_task(infrastructure.auto_scaling_monitor())
        
        # Update metrics
        ai_agents_active.set(len(AgentType))
        
        logger.info("MyRoofGenius AI OS started successfully!")
        
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down MyRoofGenius AI OS...")
    
    if pg_pool:
        await pg_pool.close()
    
    logger.info("Shutdown complete")

# Initialize FastAPI
app = FastAPI(
    title="MyRoofGenius AI OS",
    description="AI-Native Business Platform for Roofing Industry",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add Sentry middleware
app.add_middleware(SentryAsgiMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myroofgenius.com",
        "https://www.myroofgenius.com",
        "https://myroofgenius.vercel.app",
        "https://weathercraft-erp.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class LeadRequest(BaseModel):
    """Lead capture request"""
    name: str
    email: str
    phone: str
    address: str
    roof_type: Optional[str] = None
    square_footage: Optional[int] = None
    urgency: str = "normal"
    source: str = "website"
    budget_range: Optional[str] = None
    insurance_claim: bool = False

class AIRequest(BaseModel):
    """AI processing request"""
    action: str
    data: Dict[str, Any] = {}
    context: Optional[Dict[str, Any]] = {}
    priority: str = "normal"

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    services: Dict[str, bool]
    metrics: Dict[str, Any]
    timestamp: datetime

# Middleware for metrics
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track request metrics"""
    start_time = datetime.now()
    
    response = await call_next(request)
    
    duration = (datetime.now() - start_time).total_seconds()
    
    # Update metrics
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# API Endpoints

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with system status"""
    metrics = await monitoring.get_current_metrics() if monitoring else {}
    
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        services={
            "ai_os": ai_os is not None,
            "revenue_engine": revenue_engine is not None,
            "monitoring": monitoring is not None,
            "security": security is not None,
            "infrastructure": infrastructure is not None,
            "database": pg_pool is not None,
            "redis": redis_client is not None
        },
        metrics=metrics,
        timestamp=datetime.now(UTC)
    )

@app.get("/health")
async def health_check():
    """Detailed health check"""
    checks = {}
    
    # Check database
    try:
        async with pg_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["database"] = "healthy"
    except:
        checks["database"] = "unhealthy"
    
    # Check Redis
    try:
        redis_client.ping()
        checks["redis"] = "healthy"
    except:
        checks["redis"] = "unhealthy"
    
    # Check AI agents
    if ai_os:
        active_agents = len([a for a in ai_os.agents.values() if a.get("active")])
        checks["ai_agents"] = f"{active_agents}/{len(AgentType)} active"
    else:
        checks["ai_agents"] = "not initialized"
    
    # Overall status
    all_healthy = all(v == "healthy" or "active" in str(v) for v in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat()
    }

@app.post("/api/leads/capture")
async def capture_lead(lead: LeadRequest, background_tasks: BackgroundTasks):
    """
    Capture a new lead and trigger revenue generation
    This is the money-making endpoint
    """
    try:
        # Convert to revenue engine lead
        revenue_lead = RevenueLead(**lead.dict())
        
        # Process through revenue engine
        result = await revenue_engine.capture_lead(revenue_lead)
        
        # Process through AI OS for additional optimization
        ai_request = {
            "type": "new_lead",
            "lead_data": lead.dict(),
            "revenue_data": result
        }
        
        ai_result = await ai_os.process_request(ai_request)
        
        # Update metrics
        lead_count = await pg_pool.fetchval(
            "SELECT COUNT(*) FROM leads WHERE captured_at::date = CURRENT_DATE"
        )
        active_users.set(lead_count)
        
        # Schedule background processing
        background_tasks.add_task(
            process_lead_background,
            result["lead_id"],
            lead.dict()
        )
        
        # Broadcast to websockets
        await broadcast_event({
            "type": "new_lead",
            "lead_id": result["lead_id"],
            "potential_value": result["potential_revenue"],
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        return {
            "success": True,
            "lead_id": result["lead_id"],
            "quote": result["quote"],
            "next_steps": result["immediate_actions"],
            "estimated_project_start": result["estimated_close_date"]
        }
        
    except Exception as e:
        logger.error(f"Lead capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/process")
async def process_ai_request(request: AIRequest):
    """Process request through AI OS"""
    try:
        result = await ai_os.process_request(request.dict())
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"AI processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics"""
    metrics = await monitoring.get_current_metrics()
    revenue_metrics = await revenue_engine.calculate_daily_revenue()
    
    # Update Prometheus metrics
    revenue_total.set(revenue_metrics["actual_revenue"])
    lead_conversion.set(revenue_metrics["conversion_rate"])
    
    return {
        "system": metrics,
        "revenue": revenue_metrics,
        "timestamp": datetime.now(UTC).isoformat()
    }

@app.get("/api/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Process websocket commands
            command = json.loads(data)
            
            if command.get("type") == "subscribe":
                # Handle subscription to specific events
                pass
            elif command.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

@app.post("/api/deploy")
async def trigger_deployment(background_tasks: BackgroundTasks):
    """Trigger a new deployment"""
    try:
        deployment_id = await deployment.create_deployment()
        
        # Run deployment in background
        background_tasks.add_task(
            deployment.execute_deployment,
            deployment_id
        )
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "status": "initiated"
        }
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agents/status")
async def get_agent_status():
    """Get status of all AI agents"""
    agents_status = {}
    
    for agent_type, agent in ai_os.agents.items():
        agents_status[agent_type.value] = {
            "active": agent.get("active", False),
            "memory_size": len(agent.get("memory", {})),
            "tools": len(agent.get("tools", []))
        }
    
    return {
        "agents": agents_status,
        "total": len(agents_status),
        "active": sum(1 for a in agents_status.values() if a["active"])
    }

@app.post("/api/industry/configure")
async def configure_industry(industry: str, config: Dict[str, Any]):
    """Configure system for a different industry"""
    try:
        template = await ai_os.create_industry_template(industry, config)
        return {
            "success": True,
            "template": template
        }
    except Exception as e:
        logger.error(f"Industry configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def process_lead_background(lead_id: str, lead_data: Dict):
    """Background processing for leads"""
    try:
        # Additional AI processing
        await ai_os.process_request({
            "type": "background_lead_processing",
            "lead_id": lead_id,
            "data": lead_data
        })
        
        # Update lead status
        async with pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE leads SET processed = true WHERE id = $1",
                lead_id
            )
    except Exception as e:
        logger.error(f"Background processing failed: {e}")

async def broadcast_event(event: Dict):
    """Broadcast event to all websocket connections"""
    dead_connections = []
    
    for ws in websocket_connections:
        try:
            await ws.send_json(event)
        except:
            dead_connections.append(ws)
    
    # Remove dead connections
    for ws in dead_connections:
        websocket_connections.remove(ws)

async def initialize_database_schema(pool):
    """Initialize complete database schema"""
    async with pool.acquire() as conn:
        # Main tables
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255) UNIQUE,
                phone VARCHAR(50),
                address TEXT,
                roof_type VARCHAR(100),
                square_footage INT,
                urgency VARCHAR(50),
                source VARCHAR(100),
                budget_range VARCHAR(100),
                insurance_claim BOOLEAN,
                captured_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR(50),
                value_score FLOAT,
                stripe_customer_id VARCHAR(255),
                processed BOOLEAN DEFAULT FALSE,
                converted BOOLEAN DEFAULT FALSE,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_followups (
                id SERIAL PRIMARY KEY,
                lead_id VARCHAR(255) REFERENCES leads(id),
                type VARCHAR(50),
                scheduled_for TIMESTAMP,
                data JSONB,
                status VARCHAR(50),
                executed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                lead_id VARCHAR(255) REFERENCES leads(id),
                amount DECIMAL(10,2),
                type VARCHAR(50),
                stripe_payment_intent VARCHAR(255),
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS sales_pipeline (
                id SERIAL PRIMARY KEY,
                lead_id VARCHAR(255) REFERENCES leads(id),
                stage VARCHAR(50),
                value DECIMAL(10,2),
                probability FLOAT,
                expected_close DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS insurance_opportunities (
                id SERIAL PRIMARY KEY,
                lead_id VARCHAR(255) REFERENCES leads(id),
                estimated_claim DECIMAL(10,2),
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS referral_campaigns (
                id SERIAL PRIMARY KEY,
                lead_email VARCHAR(255),
                referral_code VARCHAR(50) UNIQUE,
                incentive_amount DECIMAL(10,2),
                referrals_generated INT DEFAULT 0,
                revenue_generated DECIMAL(10,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR(50)
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS industry_templates (
                id SERIAL PRIMARY KEY,
                industry VARCHAR(100),
                config JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        
        # Create indexes for performance
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_followups_scheduled ON scheduled_followups(scheduled_for)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_lead ON transactions(lead_id)")
        
        logger.info("Database schema initialized")

if __name__ == "__main__":
    # Production server configuration
    uvicorn.run(
        "main_production:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=int(os.getenv("WORKERS", 4)),
        log_config={
            "version": 1,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
        },
        access_log=True,
        use_colors=False
    )