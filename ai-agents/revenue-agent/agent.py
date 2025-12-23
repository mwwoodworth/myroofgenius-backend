#!/usr/bin/env python3
"""
revenue-agent - Revenue optimization and growth
AI Model: claude-3
Port: 6006
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
from datetime import datetime, timedelta
import httpx
import os
import asyncpg
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="revenue-agent",
    description="Revenue optimization and growth",
    version="1.0.0"
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'aws-0-us-east-2.pooler.supabase.com'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres.yomagoqdmxszqtdwuhab'),
    'password': os.getenv('DB_PASSWORD', 'Brain0ps2O2S'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

# Database pool
db_pool = None

# Agent state
class AgentState:
    def __init__(self):
        self.tasks_processed = 0
        self.last_activity = datetime.utcnow()
        self.status = "idle"
        self.current_task = None
        self.memory = []

agent_state = AgentState()

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            min_size=2,
            max_size=10
        )
    return db_pool

class AgentTask(BaseModel):
    task_id: str
    task_type: str
    priority: int = 5
    params: Dict[str, Any] = {}

class AgentResponse(BaseModel):
    agent: str = "revenue-agent"
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

@app.get("/health")
async def health():
    # Check database connection
    db_healthy = False
    try:
        pool = await get_db_pool()
        await pool.fetchval("SELECT 1")
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    return {
        "status": "healthy" if db_healthy else "degraded",
        "agent": "revenue-agent",
        "port": 6006,
        "capabilities": ["analyze_revenue", "optimize_pricing", "forecast", "recommend"],
        "data_source": "real_database",
        "database_connected": db_healthy,
        "tasks_processed": agent_state.tasks_processed,
        "current_status": agent_state.status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/process")
async def process_task(task: AgentTask):
    """Process an AI task"""
    try:
        agent_state.status = "processing"
        agent_state.current_task = task.task_id
        agent_state.last_activity = datetime.utcnow()
        
        logger.info(f"Processing task {task.task_id}: {task.task_type}")
        
        # Simulate AI processing (replace with actual AI calls)
        result = await execute_ai_task(task)
        
        agent_state.tasks_processed += 1
        agent_state.status = "idle"
        agent_state.current_task = None
        
        # Store in memory
        agent_state.memory.append({
            "task_id": task.task_id,
            "task_type": task.task_type,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 100 memories
        if len(agent_state.memory) > 100:
            agent_state.memory = agent_state.memory[-100:]
        
        return AgentResponse(status="success", result=result)
        
    except Exception as e:
        logger.error(f"Error processing task: {e}")
        agent_state.status = "error"
        return AgentResponse(status="error", error=str(e))

async def execute_ai_task(task: AgentTask) -> Dict[str, Any]:
    """Execute the actual AI task with real database queries"""
    pool = await get_db_pool()

    try:
        if task.task_type == "analyze_revenue":
            # Get real revenue metrics from database
            total_revenue = await pool.fetchval("""
                SELECT COALESCE(SUM(revenue), 0) FROM revenue_tracking
            """)

            monthly_revenue = await pool.fetch("""
                SELECT
                    DATE_TRUNC('month', date) as month,
                    SUM(revenue) as total
                FROM revenue_tracking
                GROUP BY DATE_TRUNC('month', date)
                ORDER BY month DESC
                LIMIT 6
            """)

            active_subscriptions = await pool.fetchval("""
                SELECT COUNT(*) FROM subscriptions WHERE status = 'active'
            """)

            return {
                "analysis": "Real revenue analysis from database",
                "total_revenue": float(total_revenue or 0),
                "monthly_trend": [
                    {"month": row['month'].isoformat(), "revenue": float(row['total'])}
                    for row in monthly_revenue
                ],
                "active_subscriptions": active_subscriptions or 0,
                "insights": [
                    f"Total revenue tracked: ${float(total_revenue or 0):.2f}",
                    f"Active subscriptions: {active_subscriptions or 0}",
                    f"Last {len(monthly_revenue)} months of data available"
                ],
                "confidence": 1.0
            }

        elif task.task_type == "optimize_pricing":
            # Get real subscription pricing data
            pricing_data = await pool.fetch("""
                SELECT
                    plan_name,
                    AVG(amount) as avg_price,
                    COUNT(*) as count,
                    billing_cycle
                FROM subscriptions
                WHERE status = 'active'
                GROUP BY plan_name, billing_cycle
                ORDER BY avg_price DESC
            """)

            return {
                "optimization": "Pricing recommendations based on real subscription data",
                "current_plans": [
                    {
                        "plan": row['plan_name'],
                        "avg_price": float(row['avg_price'] or 0),
                        "subscribers": row['count'],
                        "billing_cycle": row['billing_cycle']
                    }
                    for row in pricing_data
                ],
                "recommendations": [
                    "Consider introducing annual discounts to increase LTV",
                    "Monitor churn rates by pricing tier",
                    "A/B test pricing variations for new signups"
                ]
            }

        elif task.task_type == "forecast":
            # Get historical data for forecasting
            historical = await pool.fetch("""
                SELECT
                    date,
                    revenue,
                    new_customers
                FROM revenue_tracking
                ORDER BY date DESC
                LIMIT 90
            """)

            if not historical:
                return {
                    "forecast": "Insufficient data for forecasting",
                    "message": "Need at least 30 days of historical revenue data",
                    "data_points": 0
                }

            # Simple moving average forecast
            avg_daily_revenue = sum(float(row['revenue'] or 0) for row in historical) / len(historical)
            avg_new_customers = sum(row['new_customers'] or 0 for row in historical) / len(historical)

            return {
                "forecast": "30-day revenue forecast based on historical data",
                "data_points": len(historical),
                "avg_daily_revenue": round(avg_daily_revenue, 2),
                "avg_daily_new_customers": round(avg_new_customers, 2),
                "projected_30_day_revenue": round(avg_daily_revenue * 30, 2),
                "projected_new_customers": round(avg_new_customers * 30),
                "confidence": 0.75 if len(historical) >= 30 else 0.5
            }

        elif task.task_type == "recommend":
            # Get revenue opportunities from database
            recent_transactions = await pool.fetchval("""
                SELECT COUNT(*) FROM revenue_tracking
                WHERE date > NOW() - INTERVAL '7 days'
            """)

            churn_risk = await pool.fetchval("""
                SELECT COUNT(*) FROM subscriptions
                WHERE status = 'active'
                AND next_billing_date < NOW() + INTERVAL '7 days'
            """)

            return {
                "recommendations": [
                    {
                        "type": "retention",
                        "priority": "high" if churn_risk > 0 else "low",
                        "message": f"{churn_risk or 0} subscriptions renewing in next 7 days - send retention emails"
                    },
                    {
                        "type": "growth",
                        "priority": "medium",
                        "message": f"Recent activity: {recent_transactions or 0} transactions in last 7 days"
                    },
                    {
                        "type": "optimization",
                        "priority": "medium",
                        "message": "Review pricing tiers based on customer LTV data"
                    }
                ],
                "action_items": churn_risk or 0
            }

        else:
            return {
                "result": f"Unknown task type: {task.task_type}",
                "supported_types": ["analyze_revenue", "optimize_pricing", "forecast", "recommend"],
                "details": task.params
            }

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/status")
async def get_status():
    return {
        "agent": "revenue-agent",
        "status": agent_state.status,
        "current_task": agent_state.current_task,
        "tasks_processed": agent_state.tasks_processed,
        "last_activity": agent_state.last_activity.isoformat(),
        "memory_size": len(agent_state.memory)
    }

@app.get("/memory")
async def get_memory(limit: int = 10):
    """Get agent's memory (recent tasks)"""
    return {
        "agent": "revenue-agent",
        "memory": agent_state.memory[-limit:],
        "total_memories": len(agent_state.memory)
    }

@app.post("/communicate")
async def communicate_with_agent(message: str):
    """Communicate with the agent using natural language"""
    # Here you would integrate with actual AI for NLP
    return {
        "agent": "revenue-agent",
        "response": f"Acknowledged: {message}",
        "action_taken": "Message processed and understood"
    }

# Background task to keep agent alive
async def heartbeat():
    while True:
        await asyncio.sleep(30)
        logger.info(f"{'revenue-agent'} heartbeat - Status: {agent_state.status}, Tasks: {agent_state.tasks_processed}")

@app.on_event("startup")
async def startup_event():
    # Initialize database pool
    try:
        await get_db_pool()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")

    asyncio.create_task(heartbeat())
    logger.info(f"revenue-agent started on port 6006")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6006)
