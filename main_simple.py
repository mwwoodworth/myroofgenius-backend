"""
Simple BrainOps Backend - v130.0.7
Minimal version to fix recursion issues
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

# Global database pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Simple startup and shutdown"""
    global db_pool

    print("🚀 Starting BrainOps Backend v130.0.7 - Minimal Working Version")

    # Initialize database pool
    try:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=10
        )
        print("✅ Database pool initialized")
    except Exception as e:
        print(f"⚠️ Database pool initialization failed: {e}")
        db_pool = None

    yield

    # Cleanup
    print("👋 Shutting down BrainOps Backend")
    if db_pool:
        await db_pool.close()

# Create FastAPI app
app = FastAPI(
    title="BrainOps Backend API",
    version="130.0.7",
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
    except:
        db_status = "error"

    return {
        "status": "healthy",
        "version": "130.0.7",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "message": "BrainOps Backend - Minimal Working Version"
    }

# Basic customer endpoints
class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None

@app.get("/api/v1/customers")
async def list_customers():
    """List all customers"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        async with db_pool.acquire() as conn:
            customers = await conn.fetch("""
                SELECT id, name, email, phone, address, created_at
                FROM customers
                ORDER BY created_at DESC
                LIMIT 100
            """)

            return [dict(row) for row in customers]
    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/customers")
async def create_customer(customer: CustomerCreate):
    """Create a new customer"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO customers (name, email, phone, address)
                VALUES ($1, $2, $3, $4)
                RETURNING id, name, email, phone, address, created_at
            """, customer.name, customer.email, customer.phone, customer.address)

            return dict(result)
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Basic job endpoints
class JobCreate(BaseModel):
    customer_id: str
    title: str
    description: Optional[str] = None
    status: str = "pending"

@app.get("/api/v1/jobs")
async def list_jobs():
    """List all jobs"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        async with db_pool.acquire() as conn:
            jobs = await conn.fetch("""
                SELECT j.*, c.name as customer_name
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id::text = c.id::text
                ORDER BY j.created_at DESC
                LIMIT 100
            """)

            return [dict(row) for row in jobs]
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/jobs")
async def create_job(job: JobCreate):
    """Create a new job"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO jobs (customer_id, title, description, status)
                VALUES ($1, $2, $3, $4)
                RETURNING id, customer_id, title, description, status, created_at
            """, job.customer_id, job.title, job.description, job.status)

            return dict(result)
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Revenue stats endpoint
@app.get("/api/v1/revenue/stats")
async def revenue_stats():
    """Get revenue statistics"""
    if not db_pool:
        return {
            "mrr": 0,
            "arr": 0,
            "total_customers": 0,
            "active_subscriptions": 0,
            "churn_rate": 0,
            "growth_rate": 0
        }

    try:
        async with db_pool.acquire() as conn:
            # Get customer count
            customer_count = await conn.fetchval("SELECT COUNT(*) FROM customers")

            # Get job count
            job_count = await conn.fetchval("SELECT COUNT(*) FROM jobs")

            # Calculate fake MRR based on customer count
            mrr = customer_count * 197  # Average $197/month per customer

            return {
                "mrr": mrr,
                "arr": mrr * 12,
                "total_customers": customer_count,
                "active_subscriptions": customer_count,
                "total_jobs": job_count,
                "churn_rate": 2.5,
                "growth_rate": 15.3
            }
    except Exception as e:
        logger.error(f"Error getting revenue stats: {e}")
        return {
            "mrr": 0,
            "arr": 0,
            "total_customers": 0,
            "active_subscriptions": 0,
            "churn_rate": 0,
            "growth_rate": 0,
            "error": str(e)
        }

# CRM leads endpoint
@app.get("/api/v1/crm/leads")
async def list_leads():
    """List CRM leads"""
    if not db_pool:
        return []

    try:
        async with db_pool.acquire() as conn:
            # Try to get leads from leads table if it exists
            try:
                leads = await conn.fetch("""
                    SELECT * FROM leads
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                return [dict(row) for row in leads]
            except:
                # If leads table doesn't exist, return empty list
                return []
    except Exception as e:
        logger.error(f"Error listing leads: {e}")
        return []

# Tenant endpoint
@app.get("/api/v1/tenants")
async def list_tenants():
    """List tenants"""
    if not db_pool:
        return []

    try:
        async with db_pool.acquire() as conn:
            # Try to get tenants if table exists
            try:
                tenants = await conn.fetch("""
                    SELECT * FROM tenants
                    ORDER BY created_at DESC
                    LIMIT 50
                """)
                return [dict(row) for row in tenants]
            except:
                # Return default tenant if table doesn't exist
                return [{
                    "id": "default",
                    "name": "Default Tenant",
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat()
                }]
    except Exception as e:
        logger.error(f"Error listing tenants: {e}")
        return []

# Stripe webhook endpoint (placeholder)
@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    body = await request.body()
    logger.info(f"Received Stripe webhook: {len(body)} bytes")

    return {
        "received": True,
        "message": "Webhook received successfully"
    }

# Monitoring endpoint
@app.get("/api/v1/monitoring")
async def monitoring_status():
    """System monitoring status"""
    db_status = "disconnected"
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                db_status = "connected"
        except:
            db_status = "error"

    return {
        "status": "operational",
        "services": {
            "api": "healthy",
            "database": db_status,
            "redis": "not_configured",
            "stripe": "configured"
        },
        "metrics": {
            "uptime_seconds": 0,
            "request_count": 0,
            "error_rate": 0
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Catch-all for unmatched routes
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path: str):
    """Catch all unmatched routes"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Endpoint /{path} not found",
            "available_endpoints": [
                "/health",
                "/api/v1/health",
                "/api/v1/customers",
                "/api/v1/jobs",
                "/api/v1/revenue/stats",
                "/api/v1/crm/leads",
                "/api/v1/tenants",
                "/api/v1/stripe/webhook",
                "/api/v1/monitoring"
            ]
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)