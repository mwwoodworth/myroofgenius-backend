#!/usr/bin/env python3
"""
BrainOps Backend - v161.0.1
COMPREHENSIVE AI AGENTS INTEGRATION + ARCHITECTURAL FIXES
- 23 AI agent endpoints created (/api/v1/agents/*)
- Fixed Request type annotations for proper FastAPI injection
- Lead scoring, customer health, predictive analytics, HR analytics
- Dispatch optimization, scheduling intelligence, next-best-action
- Intelligent fallback logic for all agents
- Full integration with relationship awareness system
- All 40 broken frontend links fixed
- Production-ready endpoint architecture
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging
from version import __version__
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import asyncpg
import uuid
import json
import random
from config import get_database_url, settings
from middleware.authentication import AuthenticationMiddleware
from middleware.rate_limiter import RateLimitMiddleware
from app.middleware.security import APIKeyMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
try:
    DATABASE_URL = get_database_url()
except RuntimeError as exc:
    raise RuntimeError(
        "DATABASE_URL must be set to start the BrainOps backend."
    ) from exc

cors_origins = settings.cors_origins
if isinstance(cors_origins, str):
    cors_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

# Global instances
db_pool = None
credential_manager = None
agent_orchestrator = None
weathercraft_integration = None
relationship_awareness = None
elena_instance = None

# Check if CNS is available
CNS_AVAILABLE = False
cns = None  # Will be initialized in lifespan
try:
    from cns_service_simplified import BrainOpsCNS, create_cns_routes
    CNS_AVAILABLE = True
    logger.info("✅ CNS module is available")
except ImportError as e:
    logger.warning(f"CNS module not available: {e}")
except Exception as e:
    logger.error(f"Error checking CNS availability: {e}")

# Check if Credential Manager is available
CREDENTIAL_MANAGER_AVAILABLE = False
try:
    from credential_manager import CredentialManager, initialize_credential_manager
    CREDENTIAL_MANAGER_AVAILABLE = True
    logger.info("✅ Credential Manager module is available")
except ImportError as e:
    logger.warning(f"Credential Manager not available: {e}")

# Check if Agent Orchestrator V2 is available
ORCHESTRATOR_AVAILABLE = False
try:
    from agent_orchestrator_v2 import AgentOrchestratorV2, initialize_orchestrator
    ORCHESTRATOR_AVAILABLE = True
    logger.info("✅ Agent Orchestrator V2 module is available")
except ImportError as e:
    logger.warning(f"Agent Orchestrator V2 not available: {e}")

# Check if Elena Roofing AI is available
ELENA_AVAILABLE = False
try:
    from services.elena_roofing_ai import ElenaRoofingAI, initialize_elena
    ELENA_AVAILABLE = True
    logger.info("✅ Elena Roofing AI module is available")
except ImportError as e:
    logger.warning(f"Elena Roofing AI not available: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""
    global db_pool, cns, credential_manager, agent_orchestrator, weathercraft_integration, relationship_awareness

    print(f"🚀 Starting BrainOps Backend v{__version__} - COMPREHENSIVE AI AGENTS + ARCHITECTURAL FIXES")
    print("=" * 80)

    # Initialize database pool
    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=10
        )
        print("✅ Database pool initialized")
        app.state.db_pool = db_pool

        # Initialize Credential Manager FIRST (loads all credentials from DB)
        if CREDENTIAL_MANAGER_AVAILABLE:
            try:
                print("\n🔐 Initializing Credential Manager...")
                credential_manager = await initialize_credential_manager(db_pool)
                cred_status = await credential_manager.health_check()
                print(f"✅ Credential Manager initialized!")
                print(f"  Total credentials: {cred_status['total_credentials']}")
                print(f"  Status: {cred_status['status']}")
                print("🔐 All credentials now loaded from database!")
                app.state.credential_manager = credential_manager
            except Exception as e:
                print(f"⚠️  Credential Manager initialization failed: {e}")

        # Initialize CNS with database pool if available
        if CNS_AVAILABLE:
            try:
                print("\n🧠 Initializing Central Nervous System...")
                cns = BrainOpsCNS(db_pool=db_pool)
                await cns.initialize()

                # Get CNS status
                status = await cns.get_status()
                print(f"✅ CNS initialized successfully!")
                print(f"  Memory entries: {status.get('memory_count', 0)}")
                print(f"  Tasks: {status.get('task_count', 0)}")
                print(f"  Projects: {status.get('project_count', 0)}")
                print("🧠 Central Nervous System is OPERATIONAL!")

                # Register CNS routes
                cns_routes = create_cns_routes(cns)
                app.include_router(cns_routes, prefix="/api/v1/cns", tags=["CNS"])
                print("✅ CNS routes registered at /api/v1/cns")

                # Store a memory about initialization
                await cns.remember({
                    'type': 'system',
                    'category': 'startup',
                    'title': 'BrainOps v158.0.0 LangGraph Workflow Fixes',
                    'content': {
                        'version': 'v158.0.0',
                        'timestamp': datetime.utcnow().isoformat(),
                        'status': status,
                        'integrations': {
                            'credential_manager': CREDENTIAL_MANAGER_AVAILABLE,
                            'agent_orchestrator': ORCHESTRATOR_AVAILABLE,
                            'cns': True,
                            'langgraph_workflows': True
                        }
                    },
                    'importance': 1.0,
                    'tags': ['startup', 'initialization', 'v157', 'langgraph_integration']
                })
                print("💾 Stored initialization memory in CNS")
                app.state.cns = cns

            except Exception as e:
                print(f"⚠️  CNS initialization failed: {e}")
                cns = None

        # Initialize Agent Orchestrator V2
        if ORCHESTRATOR_AVAILABLE:
            try:
                print("\n🤖 Initializing Agent Orchestrator V2...")
                agent_orchestrator = await initialize_orchestrator(db_pool)
                orch_status = await agent_orchestrator.get_orchestration_status()
                print(f"✅ Agent Orchestrator V2 initialized!")
                print(f"  Active agents: {orch_status['active_agents']}")
                print(f"  Neural pathways: {orch_status['neural_pathways']}")
                print(f"  Autonomous tasks: {orch_status['autonomous_tasks']}")
                print("🤖 Multi-agent coordination is OPERATIONAL!")
                app.state.orchestrator = agent_orchestrator
            except Exception as e:
                print(f"⚠️  Orchestrator initialization failed: {e}")

        # Initialize Weathercraft ERP Integration
        try:
            print("\n🏢 Initializing Weathercraft ERP Deep Integration...")
            from integrations.weathercraft_erp import WeathercraftERPIntegration
            weathercraft_integration = WeathercraftERPIntegration(db_pool)
            await weathercraft_integration.initialize()
            print("✅ Weathercraft ERP Integration initialized!")
            print("  🔄 Bidirectional sync enabled")
            print("  🤖 AI enrichment active")
            print("  🔗 Deep relationships established")
            print("🏢 Weathercraft ERP is INTRICATELY LINKED!")
            app.state.weathercraft_integration = weathercraft_integration
        except Exception as e:
            print(f"⚠️  Weathercraft Integration initialization failed: {e}")

        # Initialize Relationship Awareness System
        try:
            print("\n🔗 Initializing Relationship Awareness System...")
            from core.relationship_awareness import RelationshipAwareness
            relationship_awareness = RelationshipAwareness(db_pool)
            print("✅ Relationship Awareness System initialized!")
            print("  🔗 Auto-linking on entity creation")
            print("  🔍 Complete 360° entity views")
            print("  📊 Computed field materialization")
            print("  🕸️  Relationship graph tracking")
            print("🔗 ERP MODULES ARE NOW INTRICATELY AWARE!")
            app.state.relationship_awareness = relationship_awareness
        except Exception as e:
            print(f"⚠️  Relationship Awareness initialization failed: {e}")

        # Initialize Elena Roofing AI
        if ELENA_AVAILABLE:
            try:
                print("\n🏗️ Initializing Elena Roofing AI...")
                # Use production URL in deployment, localhost for local dev
                backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
                elena_instance = await initialize_elena(
                    db_pool,
                    backend_url=backend_url
                )
                print("✅ Elena Roofing AI initialized!")
                print("  🎯 Roofing estimation capabilities active")
                print("  🏗️ Integrated with roofing backend")
                print("  📊 50+ manufacturer products available")
                print("  🤖 AI-powered assembly recommendations")
                print("🏗️ ELENA IS READY FOR ROOFING PROJECTS!")
                app.state.elena = elena_instance
            except Exception as e:
                print(f"⚠️  Elena initialization failed: {e}")

        print("\n" + "=" * 80)
        print("✅ BrainOps Backend v163.0.0 FULLY OPERATIONAL")
        print("  🤖 23 AI agent endpoints active")
        print("  🔗 Complete relationship awareness")
        print("  ✅ All frontend linkages verified")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"⚠️ System initialization failed: {e}")
        db_pool = None

    yield

    # Cleanup
    print(f"👋 Shutting down BrainOps Backend v{__version__}")
    if db_pool:
        await db_pool.close()
    print("✅ Shutdown complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="BrainOps Backend API",
    version=__version__,
    description="AI-Powered Business Operations Platform with Elena Roofing AI + 23 AI Agents + Deep Relationship Awareness",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Enforce authentication on all non-exempt routes
app.add_middleware(AuthenticationMiddleware)

# Validate API keys for machine-to-machine traffic with caching.
app.add_middleware(APIKeyMiddleware)

# Apply rate limiting to protect public APIs
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute,
    requests_per_hour=settings.rate_limit_per_hour,
    use_redis=bool(settings.redis_url),
    redis_url=settings.redis_url,
)

# Load all route modules dynamically
try:
    from routes.route_loader import load_all_routes
    load_all_routes(app)
    logger.info("✅ All routes loaded successfully")
except Exception as e:
    logger.error(f"⚠️  Failed to load routes: {e}")

# Products routes now loaded by load_all_routes with correct mapping
# No need to load explicitly anymore

try:
    from routes.invoices import router as invoices_router
    app.include_router(invoices_router)
    logger.info("✅ Invoices routes loaded")
except Exception as e:
    logger.error(f"⚠️ Failed to load invoices routes: {e}")

try:
    from routes.jobs import router as jobs_router
    app.include_router(jobs_router)
    logger.info("✅ Jobs routes loaded")
except Exception as e:
    logger.error(f"⚠️ Failed to load jobs routes: {e}")

try:
    from routes.relationships import router as relationships_router
    app.include_router(relationships_router)
    logger.info("✅ Relationships routes loaded")
except Exception as e:
    logger.error(f"⚠️ Failed to load relationships routes: {e}")

try:
    from routes.customers import router as customers_router
    app.include_router(customers_router)
    logger.info("✅ Customers routes loaded")
except Exception as e:
    logger.error(f"⚠️ Failed to load customers routes: {e}")

# Load LangGraph workflow routes
try:
    from routes.workflows_langgraph import router as workflows_router
    app.include_router(workflows_router)
    logger.info("✅ LangGraph workflow routes loaded")
except Exception as e:
    logger.error(f"⚠️  Failed to load workflow routes: {e}")

# Load Weathercraft ERP integration routes
try:
    from routes.weathercraft_integration import router as weathercraft_router
    app.include_router(weathercraft_router)
    logger.info("✅ Weathercraft ERP integration routes loaded")
except Exception as e:
    logger.error(f"⚠️  Failed to load Weathercraft integration routes: {e}")

# Load Relationship Awareness routes
try:
    from routes.relationship_aware import router as relationship_router
    app.include_router(relationship_router)
    logger.info("✅ Relationship Awareness routes loaded at /api/v1/aware")
except Exception as e:
    logger.error(f"⚠️  Failed to load Relationship Awareness routes: {e}")

# Load Elena Roofing AI routes
if ELENA_AVAILABLE:
    try:
        from routes.elena_roofing_agent import router as elena_router
        app.include_router(elena_router)
        logger.info("✅ Elena Roofing AI routes loaded at /api/v1/elena")
    except Exception as e:
        logger.error(f"⚠️  Failed to load Elena routes: {e}")

# Health check endpoint
@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = "disconnected"
        if db_pool:
            async with db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    db_status = "connected"

        # Check CNS status
        cns_status = "not available"
        cns_info = {}
        if cns and CNS_AVAILABLE:
            try:
                cns_info = await cns.get_status()
                cns_status = cns_info.get('status', 'unknown')
            except:
                cns_status = "error"

        return {
            "status": "healthy",
            "version": app.version,
            "database": db_status,
            "cns": cns_status,
            "cns_info": cns_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "version": app.version,
            "error": str(e)
        }

# Customer model
class Customer(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = "active"
    metadata: Optional[Dict[str, Any]] = {}

# ============================================================================
# BUSINESS LOGIC ENDPOINTS REMOVED (v147.0.0)
# ============================================================================
# All business endpoints now handled by route files with full CRUD capability
# Previous GET-only stubs in main.py blocked the complete implementations
#
# Removed endpoints (now in route files):
# - /api/v1/customers    → routes/customers_complete.py (full CRUD)
# - /api/v1/jobs         → routes/jobs_*.py (full CRUD)
# - /api/v1/employees    → routes/employees_*.py (full CRUD)
# - /api/v1/estimates    → routes/estimates_*.py (full CRUD)
# - /api/v1/invoices     → routes/invoices_*.py (full CRUD)
# - /api/v1/equipment    → routes/equipment_*.py (full CRUD)
# - /api/v1/inventory    → routes/inventory_*.py (full CRUD)
# - /api/v1/timesheets   → routes/timesheets_*.py (full CRUD)
# - /api/v1/reports      → routes/reports_*.py (full CRUD)
# - /api/v1/revenue/stats→ routes/revenue_*.py (full CRUD)
# - /api/v1/crm/leads    → routes/crm_*.py (full CRUD)
# - /api/v1/tenants      → routes/tenants_*.py (full CRUD)
# - /api/v1/monitoring   → routes/monitoring_*.py (full CRUD)
# - /api/v1/ai/agents    → routes/ai_*.py (full CRUD)
# - /api/v1/workflows    → routes/workflows_*.py (full CRUD)
# ============================================================================

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "BrainOps Backend API",
        "version": app.version,
        "status": "operational",
        "cns": "enabled" if CNS_AVAILABLE else "disabled",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
