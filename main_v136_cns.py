#!/usr/bin/env python3
"""
BrainOps Backend - v136.0.0
COMPLETE with Central Nervous System (CNS) FULLY OPERATIONAL
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import asyncpg
import uuid
import json
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

# Global database pool
db_pool = None

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""
    global db_pool, cns

    print("🚀 Starting BrainOps Backend v136.0.0 - WITH CENTRAL NERVOUS SYSTEM")
    print("=" * 60)

    # Initialize database pool
    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=10
        )
        print("✅ Database pool initialized")

        # Store DB pool in app state for access
        app.state.db_pool = db_pool

        # Initialize CNS with database pool if available
        if CNS_AVAILABLE:
            try:
                print("🧠 Initializing Central Nervous System...")
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
                    'title': 'CNS v136.0.0 Initialized',
                    'content': {
                        'version': 'v136.0.0',
                        'timestamp': datetime.utcnow().isoformat(),
                        'status': status
                    },
                    'importance': 0.9,
                    'tags': ['startup', 'initialization', 'v136']
                })
                print("💾 Stored initialization memory in CNS")

            except Exception as e:
                print(f"⚠️ CNS initialization failed: {e}")
                cns = None
                CNS_AVAILABLE = False
        else:
            print("⚠️ CNS service not available, skipping initialization")
            cns = None

    except Exception as e:
        print(f"⚠️ Database pool initialization failed: {e}")
        db_pool = None

    print("=" * 60)
    print("✅ BrainOps Backend v136.0.0 is READY!")

    yield

    # Cleanup
    print("👋 Shutting down BrainOps Backend")
    if db_pool:
        await db_pool.close()

# Create FastAPI app with lifespan
app = FastAPI(
    title="BrainOps Backend API",
    version="136.0.0",
    description="AI-Powered Business Operations Platform with Central Nervous System",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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
            "version": "136.0.0",
            "database": db_status,
            "cns": cns_status,
            "cns_info": cns_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "version": "136.0.0",
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

# Customers endpoint
@app.get("/api/v1/customers")
async def get_customers(limit: int = 100, offset: int = 0):
    """Get all customers"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM customers")

            # Get customers
            rows = await conn.fetch("""
                SELECT customer_id, name, email, phone, address,
                       company_name, status, created_at, metadata
                FROM customers
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            customers = []
            for row in rows:
                customers.append({
                    "customer_id": str(row['customer_id']),
                    "name": row['name'],
                    "email": row['email'],
                    "phone": row['phone'],
                    "address": row['address'],
                    "company_name": row['company_name'],
                    "status": row['status'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "metadata": row['metadata'] or {}
                })

            return {
                "customers": customers,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Jobs endpoint
@app.get("/api/v1/jobs")
async def get_jobs(limit: int = 100, offset: int = 0):
    """Get all jobs"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM jobs")

            # Get jobs
            rows = await conn.fetch("""
                SELECT job_id, customer_id, title, description,
                       status, priority, scheduled_date, completion_date,
                       created_at, metadata
                FROM jobs
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            jobs = []
            for row in rows:
                jobs.append({
                    "job_id": str(row['job_id']),
                    "customer_id": str(row['customer_id']) if row['customer_id'] else None,
                    "title": row['title'],
                    "description": row['description'],
                    "status": row['status'],
                    "priority": row['priority'],
                    "scheduled_date": row['scheduled_date'].isoformat() if row['scheduled_date'] else None,
                    "completion_date": row['completion_date'].isoformat() if row['completion_date'] else None,
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "metadata": row['metadata'] or {}
                })

            return {
                "jobs": jobs,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Employees endpoint
@app.get("/api/v1/employees")
async def get_employees(limit: int = 100, offset: int = 0):
    """Get all employees"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM employees")

            # Get employees
            rows = await conn.fetch("""
                SELECT employee_id, first_name, last_name, email,
                       phone, role, department, hire_date, status
                FROM employees
                ORDER BY hire_date DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            employees = []
            for row in rows:
                employees.append({
                    "employee_id": str(row['employee_id']),
                    "first_name": row['first_name'],
                    "last_name": row['last_name'],
                    "email": row['email'],
                    "phone": row['phone'],
                    "role": row['role'],
                    "department": row['department'],
                    "hire_date": row['hire_date'].isoformat() if row['hire_date'] else None,
                    "status": row['status']
                })

            return {
                "employees": employees,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Estimates endpoint
@app.get("/api/v1/estimates")
async def get_estimates(limit: int = 100, offset: int = 0):
    """Get all estimates"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM estimates")

            # Get estimates
            rows = await conn.fetch("""
                SELECT estimate_id, customer_id, job_id,
                       estimate_number, amount, status,
                       valid_until, created_at
                FROM estimates
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            estimates = []
            for row in rows:
                estimates.append({
                    "estimate_id": str(row['estimate_id']),
                    "customer_id": str(row['customer_id']) if row['customer_id'] else None,
                    "job_id": str(row['job_id']) if row['job_id'] else None,
                    "estimate_number": row['estimate_number'],
                    "amount": float(row['amount']) if row['amount'] else 0,
                    "status": row['status'],
                    "valid_until": row['valid_until'].isoformat() if row['valid_until'] else None,
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })

            return {
                "estimates": estimates,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching estimates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Invoices endpoint
@app.get("/api/v1/invoices")
async def get_invoices(limit: int = 100, offset: int = 0):
    """Get all invoices"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM invoices")

            # Get invoices
            rows = await conn.fetch("""
                SELECT invoice_id, customer_id, job_id,
                       invoice_number, amount, status,
                       due_date, paid_date, created_at
                FROM invoices
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            invoices = []
            for row in rows:
                invoices.append({
                    "invoice_id": str(row['invoice_id']),
                    "customer_id": str(row['customer_id']) if row['customer_id'] else None,
                    "job_id": str(row['job_id']) if row['job_id'] else None,
                    "invoice_number": row['invoice_number'],
                    "amount": float(row['amount']) if row['amount'] else 0,
                    "status": row['status'],
                    "due_date": row['due_date'].isoformat() if row['due_date'] else None,
                    "paid_date": row['paid_date'].isoformat() if row['paid_date'] else None,
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })

            return {
                "invoices": invoices,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Equipment endpoint
@app.get("/api/v1/equipment")
async def get_equipment(limit: int = 100, offset: int = 0):
    """Get all equipment"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM equipment")

            # Get equipment
            rows = await conn.fetch("""
                SELECT equipment_id, name, type, serial_number,
                       status, location, purchase_date, last_maintenance
                FROM equipment
                ORDER BY purchase_date DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            equipment = []
            for row in rows:
                equipment.append({
                    "equipment_id": str(row['equipment_id']),
                    "name": row['name'],
                    "type": row['type'],
                    "serial_number": row['serial_number'],
                    "status": row['status'],
                    "location": row['location'],
                    "purchase_date": row['purchase_date'].isoformat() if row['purchase_date'] else None,
                    "last_maintenance": row['last_maintenance'].isoformat() if row['last_maintenance'] else None
                })

            return {
                "equipment": equipment,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching equipment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Inventory endpoint
@app.get("/api/v1/inventory")
async def get_inventory(limit: int = 100, offset: int = 0):
    """Get all inventory"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM inventory")

            # Get inventory
            rows = await conn.fetch("""
                SELECT item_id, name, sku, category,
                       quantity_on_hand, unit_price, reorder_point, unit_of_measure
                FROM inventory
                ORDER BY name
                LIMIT $1 OFFSET $2
            """, limit, offset)

            inventory = []
            for row in rows:
                inventory.append({
                    "item_id": str(row['item_id']),
                    "name": row['name'],
                    "sku": row['sku'],
                    "category": row['category'],
                    "quantity_on_hand": row['quantity_on_hand'],
                    "unit_price": float(row['unit_price']) if row['unit_price'] else 0,
                    "reorder_point": row['reorder_point'],
                    "unit_of_measure": row['unit_of_measure']
                })

            return {
                "inventory": inventory,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching inventory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Timesheets endpoint
@app.get("/api/v1/timesheets")
async def get_timesheets(limit: int = 100, offset: int = 0):
    """Get all timesheets"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM timesheets")

            # Get timesheets
            rows = await conn.fetch("""
                SELECT timesheet_id, employee_id, job_id,
                       date, hours_worked, overtime_hours, status
                FROM timesheets
                ORDER BY date DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            timesheets = []
            for row in rows:
                timesheets.append({
                    "timesheet_id": str(row['timesheet_id']),
                    "employee_id": str(row['employee_id']) if row['employee_id'] else None,
                    "job_id": str(row['job_id']) if row['job_id'] else None,
                    "date": row['date'].isoformat() if row['date'] else None,
                    "hours_worked": float(row['hours_worked']) if row['hours_worked'] else 0,
                    "overtime_hours": float(row['overtime_hours']) if row['overtime_hours'] else 0,
                    "status": row['status']
                })

            return {
                "timesheets": timesheets,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching timesheets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Reports endpoint
@app.get("/api/v1/reports")
async def get_reports():
    """Get system reports"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get various counts
            customers = await conn.fetchval("SELECT COUNT(*) FROM customers")
            jobs = await conn.fetchval("SELECT COUNT(*) FROM jobs")
            active_jobs = await conn.fetchval("SELECT COUNT(*) FROM jobs WHERE status = 'active'")
            invoices = await conn.fetchval("SELECT COUNT(*) FROM invoices")
            paid_invoices = await conn.fetchval("SELECT COUNT(*) FROM invoices WHERE status = 'paid'")

            # Calculate revenue (example)
            revenue = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0)
                FROM invoices
                WHERE status = 'paid'
            """)

            return {
                "summary": {
                    "total_customers": customers,
                    "total_jobs": jobs,
                    "active_jobs": active_jobs,
                    "total_invoices": invoices,
                    "paid_invoices": paid_invoices,
                    "total_revenue": float(revenue) if revenue else 0
                },
                "generated_at": datetime.utcnow().isoformat(),
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error generating reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Revenue stats endpoint
@app.get("/api/v1/revenue/stats")
async def get_revenue_stats():
    """Get revenue statistics"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get revenue metrics
            total_revenue = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0)
                FROM invoices
                WHERE status = 'paid'
            """)

            pending_revenue = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0)
                FROM invoices
                WHERE status IN ('pending', 'sent')
            """)

            monthly_revenue = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0)
                FROM invoices
                WHERE status = 'paid'
                AND paid_date >= DATE_TRUNC('month', CURRENT_DATE)
            """)

            return {
                "total_revenue": float(total_revenue) if total_revenue else 0,
                "pending_revenue": float(pending_revenue) if pending_revenue else 0,
                "monthly_revenue": float(monthly_revenue) if monthly_revenue else 0,
                "currency": "USD",
                "generated_at": datetime.utcnow().isoformat(),
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching revenue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# CRM Leads endpoint
@app.get("/api/v1/crm/leads")
async def get_leads(limit: int = 100, offset: int = 0):
    """Get CRM leads"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM crm_leads")

            # Get leads
            rows = await conn.fetch("""
                SELECT lead_id, name, email, phone, source,
                       status, score, created_at
                FROM crm_leads
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            leads = []
            for row in rows:
                leads.append({
                    "lead_id": str(row['lead_id']),
                    "name": row['name'],
                    "email": row['email'],
                    "phone": row['phone'],
                    "source": row['source'],
                    "status": row['status'],
                    "score": row['score'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })

            return {
                "leads": leads,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Tenants endpoint (multi-tenant support)
@app.get("/api/v1/tenants")
async def get_tenants(limit: int = 100, offset: int = 0):
    """Get all tenants"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get total count
            total = await conn.fetchval("SELECT COUNT(*) FROM tenants")

            # Get tenants
            rows = await conn.fetch("""
                SELECT tenant_id, name, domain, status,
                       plan, created_at
                FROM tenants
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)

            tenants = []
            for row in rows:
                tenants.append({
                    "tenant_id": str(row['tenant_id']),
                    "name": row['name'],
                    "domain": row['domain'],
                    "status": row['status'],
                    "plan": row['plan'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })

            return {
                "tenants": tenants,
                "total": total,
                "limit": limit,
                "offset": offset,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching tenants: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Monitoring endpoint
@app.get("/api/v1/monitoring")
async def get_monitoring():
    """Get system monitoring data"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get database stats
            db_size = await conn.fetchval("SELECT pg_database_size(current_database())")
            table_count = await conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)

            # Get CNS stats
            cns_stats = {}
            if cns and CNS_AVAILABLE:
                try:
                    cns_stats = await cns.get_status()
                except:
                    cns_stats = {"status": "error"}

            return {
                "database": {
                    "size_bytes": db_size,
                    "size_mb": round(db_size / 1024 / 1024, 2),
                    "table_count": table_count,
                    "connection_pool": {
                        "min": 5,
                        "max": 20,
                        "active": db_pool.size if db_pool else 0
                    }
                },
                "cns": cns_stats,
                "uptime": "operational",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching monitoring data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Agents endpoint
@app.get("/api/v1/ai/agents")
async def get_ai_agents():
    """Get AI agents status"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get AI agents
            rows = await conn.fetch("""
                SELECT agent_id, name, type, status, capabilities
                FROM ai_agents
                WHERE status = 'active'
                LIMIT 50
            """)

            agents = []
            for row in rows:
                agents.append({
                    "agent_id": str(row['agent_id']),
                    "name": row['name'],
                    "type": row['type'],
                    "status": row['status'],
                    "capabilities": row['capabilities'] or []
                })

            return {
                "agents": agents,
                "total": len(agents),
                "cns_enabled": CNS_AVAILABLE,
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching AI agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Workflows endpoint
@app.get("/api/v1/workflows")
async def get_workflows():
    """Get workflow status"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with db_pool.acquire() as conn:
            # Get workflows
            rows = await conn.fetch("""
                SELECT workflow_id, name, type, status, last_run
                FROM workflows
                WHERE status = 'active'
                LIMIT 50
            """)

            workflows = []
            for row in rows:
                workflows.append({
                    "workflow_id": str(row['workflow_id']),
                    "name": row['name'],
                    "type": row['type'],
                    "status": row['status'],
                    "last_run": row['last_run'].isoformat() if row['last_run'] else None
                })

            return {
                "workflows": workflows,
                "total": len(workflows),
                "version": "136.0.0"
            }
    except Exception as e:
        logger.error(f"Error fetching workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "BrainOps Backend API",
        "version": "136.0.0",
        "status": "operational",
        "cns": "enabled" if CNS_AVAILABLE else "disabled",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)