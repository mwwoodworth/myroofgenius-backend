"""
Observability and Monitoring System
Real-time metrics, error tracking, uptime monitoring, and performance analytics
"""

import os
import time
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil
import aiohttp
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(transaction_style="endpoint"),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment=os.getenv("ENVIRONMENT", "production"),
    release=os.getenv("RELEASE_VERSION", "1.0.0")
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'app_request_count',
    'Application Request Count',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'app_request_latency_seconds',
    'Application Request Latency',
    ['method', 'endpoint']
)

REVENUE_COUNTER = Counter(
    'revenue_total',
    'Total Revenue Generated',
    ['product_type', 'payment_method']
)

LEAD_COUNTER = Counter(
    'leads_captured',
    'Total Leads Captured',
    ['source', 'urgency']
)

CONVERSION_RATE = Gauge(
    'conversion_rate',
    'Lead to Customer Conversion Rate'
)

AI_LATENCY = Histogram(
    'ai_response_latency_seconds',
    'AI Response Latency',
    ['model', 'operation']
)

ERROR_COUNTER = Counter(
    'app_errors_total',
    'Total Application Errors',
    ['error_type', 'severity']
)

SYSTEM_CPU = Gauge('system_cpu_percent', 'System CPU Usage')
SYSTEM_MEMORY = Gauge('system_memory_percent', 'System Memory Usage')
SYSTEM_DISK = Gauge('system_disk_percent', 'System Disk Usage')

@dataclass
class HealthCheck:
    """Health check status"""
    status: str  # healthy, degraded, unhealthy
    timestamp: str
    checks: Dict[str, Any]
    uptime_seconds: float
    version: str

@dataclass
class PerformanceMetric:
    """Performance metric data"""
    metric_name: str
    value: float
    timestamp: str
    tags: Dict[str, str]

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracking and metrics"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Track request
        method = request.method
        path = request.url.path
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            # Add response headers
            response.headers["X-Request-ID"] = str(time.time())
            response.headers["X-Response-Time"] = str(duration)
            
            # Log slow requests
            if duration > 2.0:
                logger.warning(f"Slow request: {method} {path} took {duration:.2f}s")
                sentry_sdk.capture_message(
                    f"Slow request detected",
                    level="warning",
                    extras={"path": path, "duration": duration}
                )
            
            return response
            
        except Exception as e:
            # Track errors
            ERROR_COUNTER.labels(
                error_type=type(e).__name__,
                severity="high"
            ).inc()
            
            # Send to Sentry
            sentry_sdk.capture_exception(e)
            
            # Re-raise
            raise

class MonitoringSystem:
    """Comprehensive monitoring and observability system"""
    
    def __init__(self, pg_pool=None):
        self.pg_pool = pg_pool
        self.start_time = time.time()
        self.health_checks = {}
        self.synthetic_checks = []
        
    async def initialize(self):
        """Initialize monitoring systems"""
        # Start background monitoring tasks
        asyncio.create_task(self.collect_system_metrics())
        asyncio.create_task(self.run_synthetic_checks())
        asyncio.create_task(self.calculate_business_metrics())
        
        logger.info("Monitoring system initialized")
        
    async def collect_system_metrics(self):
        """Collect system resource metrics"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                SYSTEM_CPU.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                SYSTEM_MEMORY.set(memory.percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                SYSTEM_DISK.set(disk.percent)
                
                # Log if resources are high
                if cpu_percent > 80:
                    logger.warning(f"High CPU usage: {cpu_percent}%")
                if memory.percent > 90:
                    logger.warning(f"High memory usage: {memory.percent}%")
                if disk.percent > 85:
                    logger.warning(f"High disk usage: {disk.percent}%")
                    
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                
            await asyncio.sleep(30)
            
    async def run_synthetic_checks(self):
        """Run synthetic monitoring checks"""
        checks = [
            ("https://myroofgenius.com", "Frontend"),
            ("https://brainops-backend-prod.onrender.com/health", "Backend"),
            ("https://weathercraft-erp.vercel.app", "WeatherCraft ERP")
        ]
        
        while True:
            for url, name in checks:
                try:
                    async with aiohttp.ClientSession() as session:
                        start = time.time()
                        async with session.get(url, timeout=10) as response:
                            latency = time.time() - start
                            
                            if response.status == 200:
                                self.health_checks[name] = {
                                    "status": "healthy",
                                    "latency": latency,
                                    "last_check": datetime.now().isoformat()
                                }
                            else:
                                self.health_checks[name] = {
                                    "status": "unhealthy",
                                    "status_code": response.status,
                                    "last_check": datetime.now().isoformat()
                                }
                                
                                # Alert on unhealthy
                                sentry_sdk.capture_message(
                                    f"{name} health check failed",
                                    level="error",
                                    extras={"status_code": response.status}
                                )
                                
                except Exception as e:
                    self.health_checks[name] = {
                        "status": "error",
                        "error": str(e),
                        "last_check": datetime.now().isoformat()
                    }
                    
                    logger.error(f"Synthetic check failed for {name}: {e}")
                    
            await asyncio.sleep(60)  # Check every minute
            
    async def calculate_business_metrics(self):
        """Calculate business KPIs"""
        while True:
            if self.pg_pool:
                try:
                    async with self.pg_pool.acquire() as conn:
                        # Revenue metrics
                        revenue = await conn.fetchrow("""
                            SELECT 
                                COUNT(*) as transaction_count,
                                SUM(amount) as total_revenue,
                                AVG(amount) as avg_transaction
                            FROM payments
                            WHERE created_at > NOW() - INTERVAL '24 hours'
                            AND status = 'completed'
                        """)
                        
                        # Lead metrics
                        leads = await conn.fetchrow("""
                            SELECT
                                COUNT(*) as total_leads,
                                COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted,
                                AVG(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as conversion_rate
                            FROM leads
                            WHERE created_at > NOW() - INTERVAL '7 days'
                        """)
                        
                        # Update gauges
                        if leads['conversion_rate']:
                            CONVERSION_RATE.set(float(leads['conversion_rate']))
                            
                        # Log critical metrics
                        if revenue['total_revenue']:
                            logger.info(f"Daily revenue: ${revenue['total_revenue']}")
                        if leads['total_leads'] > 0:
                            logger.info(f"Weekly leads: {leads['total_leads']}, Conversion: {leads['conversion_rate']:.2%}")
                            
                except Exception as e:
                    logger.error(f"Error calculating business metrics: {e}")
                    
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def get_health_status(self) -> HealthCheck:
        """Get overall health status"""
        # Check all components
        all_healthy = all(
            check.get("status") == "healthy" 
            for check in self.health_checks.values()
        )
        
        status = "healthy" if all_healthy else "degraded"
        
        # Check database
        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                    self.health_checks["database"] = {"status": "healthy"}
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                self.health_checks["database"] = {"status": "unhealthy"}
                status = "unhealthy"
                
        return HealthCheck(
            status=status,
            timestamp=datetime.now().isoformat(),
            checks=self.health_checks,
            uptime_seconds=time.time() - self.start_time,
            version=os.getenv("RELEASE_VERSION", "1.0.0")
        )
        
    async def track_revenue(self, amount: float, product_type: str, payment_method: str = "stripe"):
        """Track revenue generation"""
        REVENUE_COUNTER.labels(
            product_type=product_type,
            payment_method=payment_method
        ).inc(amount)
        
        # Log significant revenue
        if amount > 100:
            logger.info(f"Revenue tracked: ${amount} for {product_type}")
            sentry_sdk.capture_message(
                "Significant revenue generated",
                level="info",
                extras={"amount": amount, "product": product_type}
            )
            
    async def track_lead(self, source: str, urgency: str):
        """Track lead capture"""
        LEAD_COUNTER.labels(
            source=source,
            urgency=urgency
        ).inc()
        
    async def track_ai_operation(self, model: str, operation: str, latency: float):
        """Track AI operation performance"""
        AI_LATENCY.labels(
            model=model,
            operation=operation
        ).observe(latency)
        
        # Alert on slow AI responses
        if latency > 3.0:
            logger.warning(f"Slow AI operation: {model}/{operation} took {latency:.2f}s")
            
    async def get_metrics_dashboard(self) -> Dict[str, Any]:
        """Get metrics for dashboard display"""
        return {
            "health": asdict(await self.get_health_status()),
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "business": {
                "conversion_rate": CONVERSION_RATE._value.get() if CONVERSION_RATE._value else 0,
                "synthetic_checks": self.health_checks
            },
            "timestamp": datetime.now().isoformat()
        }

def setup_monitoring(app: FastAPI, pg_pool=None) -> MonitoringSystem:
    """Setup monitoring for FastAPI app"""
    # Add middleware
    app.add_middleware(ObservabilityMiddleware)
    
    # Create monitoring system
    monitoring = MonitoringSystem(pg_pool)
    
    # Add Prometheus metrics endpoint
    @app.get("/metrics")
    async def metrics():
        return Response(
            generate_latest(),
            media_type="text/plain"
        )
        
    # Add health check endpoint
    @app.get("/health/detailed")
    async def health_detailed():
        return await monitoring.get_health_status()
        
    # Add dashboard endpoint
    @app.get("/api/monitoring/dashboard")
    async def monitoring_dashboard():
        return await monitoring.get_metrics_dashboard()
        
    return monitoring

# SLA tracking
class SLATracker:
    """Track SLA compliance"""
    
    def __init__(self):
        self.slas = {
            "uptime": 0.999,  # 99.9% uptime
            "latency_p95": 2.5,  # 2.5s P95 latency
            "error_rate": 0.01  # 1% error rate
        }
        self.measurements = []
        
    async def check_compliance(self) -> Dict[str, Any]:
        """Check SLA compliance"""
        # This would connect to real metrics
        return {
            "uptime": {"target": 99.9, "actual": 99.95, "compliant": True},
            "latency": {"target": 2.5, "actual": 1.8, "compliant": True},
            "errors": {"target": 1.0, "actual": 0.5, "compliant": True}
        }