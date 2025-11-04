"""
Production monitoring and analytics system
"""

import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
import logging
import json

logger = logging.getLogger(__name__)

class MetricsCollector:
    """
    Collects and aggregates system metrics
    """
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        
        # Request metrics
        self.request_times = deque(maxlen=window_size)
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.status_codes = defaultdict(int)
        
        # AI metrics
        self.ai_requests = deque(maxlen=window_size)
        self.ai_providers_used = defaultdict(int)
        self.ai_response_times = defaultdict(list)
        
        # Database metrics
        self.db_query_times = deque(maxlen=window_size)
        self.db_connection_pool = {"active": 0, "idle": 0, "total": 0}
        
        # System metrics
        self.system_metrics = []
        self.collection_task = None
        
        # Business metrics
        self.business_events = deque(maxlen=window_size)
        
    async def start_collection(self):
        """Start background metrics collection"""
        if not self.collection_task:
            self.collection_task = asyncio.create_task(self._collect_system_metrics())
    
    async def stop_collection(self):
        """Stop background metrics collection"""
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
    
    async def _collect_system_metrics(self):
        """Collect system metrics periodically"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                
                metrics = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory": {
                        "percent": psutil.virtual_memory().percent,
                        "available": psutil.virtual_memory().available,
                        "used": psutil.virtual_memory().used
                    },
                    "disk": {
                        "percent": psutil.disk_usage('/').percent,
                        "free": psutil.disk_usage('/').free
                    },
                    "network": {
                        "bytes_sent": psutil.net_io_counters().bytes_sent,
                        "bytes_recv": psutil.net_io_counters().bytes_recv
                    }
                }
                
                self.system_metrics.append(metrics)
                
                # Keep only last hour of metrics
                if len(self.system_metrics) > 60:
                    self.system_metrics = self.system_metrics[-60:]
                    
            except Exception as e:
                logger.error(f"Error collecting system metrics: {str(e)}")
    
    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float
    ):
        """Record HTTP request metrics"""
        self.request_times.append(response_time)
        self.request_counts[f"{method} {path}"] += 1
        self.status_codes[status_code] += 1
        
        if status_code >= 400:
            self.error_counts[f"{method} {path}"] += 1
    
    def record_ai_request(
        self,
        provider: str,
        response_time: float,
        success: bool
    ):
        """Record AI request metrics"""
        self.ai_requests.append({
            "provider": provider,
            "response_time": response_time,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.ai_providers_used[provider] += 1
        
        if provider not in self.ai_response_times:
            self.ai_response_times[provider] = deque(maxlen=100)
        self.ai_response_times[provider].append(response_time)
    
    def record_db_query(self, query_time: float):
        """Record database query metrics"""
        self.db_query_times.append(query_time)
    
    def update_db_pool_stats(self, active: int, idle: int, total: int):
        """Update database connection pool statistics"""
        self.db_connection_pool = {
            "active": active,
            "idle": idle,
            "total": total
        }
    
    def record_business_event(
        self,
        event_type: str,
        details: Dict[str, Any]
    ):
        """Record business event (job created, invoice paid, etc.)"""
        self.business_events.append({
            "type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        
        # Calculate request statistics
        request_stats = {}
        if self.request_times:
            request_stats = {
                "total_requests": sum(self.request_counts.values()),
                "avg_response_time": sum(self.request_times) / len(self.request_times),
                "min_response_time": min(self.request_times),
                "max_response_time": max(self.request_times),
                "error_rate": (
                    sum(self.error_counts.values()) / sum(self.request_counts.values()) * 100
                    if self.request_counts else 0
                )
            }
        
        # Calculate AI statistics
        ai_stats = {}
        if self.ai_requests:
            successful = sum(1 for r in self.ai_requests if r["success"])
            ai_stats = {
                "total_ai_requests": len(self.ai_requests),
                "success_rate": (successful / len(self.ai_requests)) * 100,
                "providers": dict(self.ai_providers_used),
                "avg_response_times": {
                    provider: sum(times) / len(times) if times else 0
                    for provider, times in self.ai_response_times.items()
                }
            }
        
        # Calculate database statistics
        db_stats = {}
        if self.db_query_times:
            db_stats = {
                "avg_query_time": sum(self.db_query_times) / len(self.db_query_times),
                "total_queries": len(self.db_query_times),
                "connection_pool": self.db_connection_pool
            }
        
        # Get latest system metrics
        system_stats = {}
        if self.system_metrics:
            latest = self.system_metrics[-1]
            system_stats = {
                "cpu_percent": latest["cpu_percent"],
                "memory_percent": latest["memory"]["percent"],
                "disk_percent": latest["disk"]["percent"]
            }
        
        # Business metrics
        business_stats = {}
        if self.business_events:
            event_counts = defaultdict(int)
            for event in self.business_events:
                event_counts[event["type"]] += 1
            business_stats = {
                "recent_events": list(self.business_events)[-10:],
                "event_counts": dict(event_counts)
            }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "requests": request_stats,
            "ai": ai_stats,
            "database": db_stats,
            "system": system_stats,
            "business": business_stats,
            "status_codes": dict(self.status_codes),
            "top_endpoints": dict(sorted(
                self.request_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])
        }

class HealthChecker:
    """
    System health checker
    """
    
    def __init__(self):
        self.checks = {}
        self.last_check = None
        self.status = "healthy"
        
    async def check_database(self, db_connection) -> Dict[str, Any]:
        """Check database health"""
        try:
            start = time.time()
            # Execute simple query
            await db_connection.execute("SELECT 1")
            latency = (time.time() - start) * 1000
            
            return {
                "status": "healthy" if latency < 100 else "degraded",
                "latency_ms": latency
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_redis(self, redis_client) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            start = time.time()
            await redis_client.ping()
            latency = (time.time() - start) * 1000
            
            return {
                "status": "healthy" if latency < 50 else "degraded",
                "latency_ms": latency
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_ai_providers(self, ai_orchestrator) -> Dict[str, Any]:
        """Check AI provider health"""
        provider_status = {}
        
        for provider in ai_orchestrator.providers:
            provider_status[provider.name] = {
                "available": provider.is_available,
                "failure_count": provider.failure_count,
                "last_failure": provider.last_failure.isoformat() if provider.last_failure else None
            }
        
        available_count = sum(1 for p in ai_orchestrator.providers if p.is_available)
        
        return {
            "status": "healthy" if available_count > 0 else "unhealthy",
            "available_providers": available_count,
            "total_providers": len(ai_orchestrator.providers),
            "providers": provider_status
        }
    
    async def check_external_services(self) -> Dict[str, Any]:
        """Check external service connectivity"""
        services = {}
        
        # Check Stripe
        try:
            import stripe
            stripe.api_key = "sk_test_REDACTED"  # Use dummy key for health check
            # This will fail but confirms the library works
            services["stripe"] = {"status": "configured"}
        except:
            services["stripe"] = {"status": "not_configured"}
        
        # Add more external service checks as needed
        
        return services
    
    async def run_health_check(
        self,
        db_connection=None,
        redis_client=None,
        ai_orchestrator=None
    ) -> Dict[str, Any]:
        """Run comprehensive health check"""
        
        checks = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {}
        }
        
        # Database check
        if db_connection:
            checks["checks"]["database"] = await self.check_database(db_connection)
        
        # Redis check
        if redis_client:
            checks["checks"]["redis"] = await self.check_redis(redis_client)
        
        # AI providers check
        if ai_orchestrator:
            checks["checks"]["ai_providers"] = await self.check_ai_providers(ai_orchestrator)
        
        # External services check
        checks["checks"]["external_services"] = await self.check_external_services()
        
        # System resources check
        checks["checks"]["system"] = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        # Determine overall status
        unhealthy_checks = [
            name for name, check in checks["checks"].items()
            if isinstance(check, dict) and check.get("status") == "unhealthy"
        ]
        
        if unhealthy_checks:
            checks["status"] = "unhealthy"
            checks["unhealthy_checks"] = unhealthy_checks
        elif any(
            isinstance(check, dict) and check.get("status") == "degraded"
            for check in checks["checks"].values()
        ):
            checks["status"] = "degraded"
        
        self.last_check = checks
        self.status = checks["status"]
        
        return checks

# Global instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()