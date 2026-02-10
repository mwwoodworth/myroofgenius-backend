"""
Monitoring System - Complete observability for the entire platform
"""

import os
import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncpg
import redis
import aiohttp
from prometheus_client import Counter, Histogram, Gauge, Summary
import traceback

logger = logging.getLogger(__name__)

class MonitoringSystem:
    """Comprehensive monitoring and observability"""
    
    def __init__(self, pg_pool, redis_client):
        self.pg_pool = pg_pool
        self.redis = redis_client
        
        # Metrics collectors
        self.api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method', 'status'])
        self.api_latency = Histogram('api_request_duration_seconds', 'API request latency', ['endpoint'])
        self.active_users = Gauge('active_users_total', 'Total active users')
        self.error_rate = Gauge('error_rate_percent', 'Error rate percentage')
        self.revenue_metrics = Gauge('revenue_total', 'Total revenue', ['type'])
        self.lead_metrics = Gauge('leads_total', 'Total leads', ['status'])
        self.ai_agent_calls = Counter('ai_agent_calls_total', 'AI agent calls', ['agent_type'])
        self.database_connections = Gauge('database_connections_active', 'Active database connections')
        self.cache_hits = Counter('cache_hits_total', 'Cache hits')
        self.cache_misses = Counter('cache_misses_total', 'Cache misses')
        
        # Alert thresholds
        self.alert_thresholds = {
            "error_rate": 5.0,  # 5% error rate
            "response_time": 2000,  # 2 seconds
            "cpu_usage": 85,  # 85% CPU
            "memory_usage": 90,  # 90% memory
            "disk_usage": 85,  # 85% disk
            "database_connections": 45,  # Near connection limit
            "failed_payments": 3,  # Failed payment attempts
            "security_threats": 1  # Any security threat
        }
        
        # Monitoring targets
        self.health_check_endpoints = [
            {"name": "database", "check": self.check_database_health},
            {"name": "redis", "check": self.check_redis_health},
            {"name": "ai_agents", "check": self.check_ai_agents_health},
            {"name": "payment_gateway", "check": self.check_payment_health},
            {"name": "external_apis", "check": self.check_external_apis}
        ]
    
    async def start(self):
        """Start monitoring system"""
        try:
            # Initialize monitoring tables
            await self._init_monitoring_tables()
            
            # Start monitoring tasks
            asyncio.create_task(self.continuous_monitoring())
            asyncio.create_task(self.aggregate_metrics())
            asyncio.create_task(self.check_sla_compliance())
            
            logger.info("Monitoring system started")
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
    
    async def _init_monitoring_tables(self):
        """Initialize monitoring tables"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS api_metrics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    endpoint TEXT,
                    method TEXT,
                    status_code INT,
                    duration_ms DOUBLE PRECISION,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    user_id TEXT,
                    tenant_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS ai_error_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    error_id VARCHAR NOT NULL,
                    error_type VARCHAR NOT NULL,
                    error_message TEXT,
                    stack_trace TEXT,
                    component VARCHAR,
                    function_name VARCHAR,
                    severity VARCHAR,
                    retry_count INT DEFAULT 0,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    occurred_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS system_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_type VARCHAR(50),
                    severity VARCHAR(20),
                    message TEXT,
                    metadata JSONB,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    resolved_at TIMESTAMP
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS health_checks (
                    id SERIAL PRIMARY KEY,
                    service VARCHAR(100),
                    status VARCHAR(20),
                    response_time FLOAT,
                    error_message TEXT,
                    checked_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS sla_compliance (
                    id SERIAL PRIMARY KEY,
                    metric VARCHAR(100),
                    target_value FLOAT,
                    actual_value FLOAT,
                    compliant BOOLEAN,
                    period_start TIMESTAMP,
                    period_end TIMESTAMP,
                    calculated_at TIMESTAMP DEFAULT NOW()
                )
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS hourly_reports (
                    id SERIAL PRIMARY KEY,
                    report_data JSONB,
                    period_start TIMESTAMPTZ,
                    period_end TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            # Create indexes for performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_api_metrics_endpoint ON api_metrics(endpoint, timestamp)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_error_logs_type_time ON ai_error_logs(error_type, occurred_at DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON system_alerts(severity, resolved)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_health_checks_service ON health_checks(service, checked_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_hourly_reports_period ON hourly_reports(period_start, period_end)")
    
    async def continuous_monitoring(self):
        """Continuous monitoring loop"""
        while True:
            try:
                # Perform health checks
                health_status = await self.perform_health_checks()
                
                # Check metrics
                metrics = await self.collect_current_metrics()
                
                # Check for anomalies
                anomalies = await self.detect_anomalies(metrics)
                
                # Generate alerts if needed
                if anomalies:
                    await self.generate_alerts(anomalies)
                
                # Store monitoring snapshot
                await self.store_monitoring_snapshot(health_status, metrics)
                
                # Update Prometheus metrics
                self.update_prometheus_metrics(metrics)
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await self.log_error("monitoring_loop", str(e), traceback.format_exc())
                await asyncio.sleep(60)
    
    async def perform_health_checks(self) -> Dict[str, Any]:
        """Perform all health checks"""
        results = {}
        
        for endpoint in self.health_check_endpoints:
            try:
                start_time = datetime.now()
                status = await endpoint["check"]()
                response_time = (datetime.now() - start_time).total_seconds()
                
                results[endpoint["name"]] = {
                    "status": "healthy" if status else "unhealthy",
                    "response_time": response_time
                }
                
                # Store health check result
                async with self.pg_pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO health_checks (service, status, response_time)
                        VALUES ($1, $2, $3)
                    ''', endpoint["name"], results[endpoint["name"]]["status"], response_time)
                
            except Exception as e:
                results[endpoint["name"]] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                
                # Store failed health check
                async with self.pg_pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO health_checks (service, status, error_message)
                        VALUES ($1, 'unhealthy', $2)
                    ''', endpoint["name"], str(e))
        
        return results
    
    async def check_database_health(self) -> bool:
        """Check database health"""
        try:
            async with self.pg_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                
                # Check connection pool health
                pool_size = self.pg_pool.get_size()
                pool_free = self.pg_pool.get_idle_size()
                
                self.database_connections.set(pool_size - pool_free)

                return result == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            return self.redis.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def check_ai_agents_health(self) -> bool:
        """Check AI agents health"""
        try:
            # Check if agents are responding
            agent_status = self.redis.get("ai_agents:status")
            if agent_status:
                status = json.loads(agent_status)
                active_agents = sum(1 for a in status.values() if a.get("active"))
                return active_agents > 0
            return False
        except Exception as e:
            logger.error(f"AI agents health check failed: {e}")
            return False
    
    async def check_payment_health(self) -> bool:
        """Check payment gateway health"""
        try:
            # Check Stripe API
            import stripe
            stripe.api_key = os.getenv("STRIPE_API_KEY")
            # Make a simple API call to check connectivity
            stripe.Balance.retrieve()
            return True
        except Exception as e:
            logger.error(f"Payment health check failed: {e}")
            return False

    async def check_external_apis(self) -> bool:
        """Check external API health"""
        try:
            apis_healthy = True
            
            # Check critical external APIs
            async with aiohttp.ClientSession() as session:
                # Check weather API
                async with session.get(
                    "https://api.weather.gov/",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status != 200:
                        apis_healthy = False

            return apis_healthy
        except Exception as e:
            logger.error(f"External API health check failed: {e}")
            return False
    
    async def collect_current_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        async with self.pg_pool.acquire() as conn:
            # API metrics
            api_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(duration_ms) / 1000.0 as avg_response_time,
                    MAX(duration_ms) / 1000.0 as max_response_time,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
                FROM api_metrics
                WHERE timestamp > NOW() - INTERVAL '5 minutes'
            ''')
            
            # Lead metrics
            lead_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_leads,
                    SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as converted,
                    AVG(value_score) as avg_value
                FROM leads
                WHERE captured_at > NOW() - INTERVAL '1 day'
            ''')
            
            # Revenue metrics
            revenue_stats = await conn.fetchrow('''
                SELECT 
                    SUM(amount) as total_revenue,
                    COUNT(*) as total_transactions
                FROM transactions
                WHERE created_at > NOW() - INTERVAL '1 day'
                AND status = 'completed'
            ''')
            
            # Error metrics
            error_stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_errors,
                    COUNT(DISTINCT error_type) as unique_errors
                FROM ai_error_logs
                WHERE occurred_at > NOW() - INTERVAL '1 hour'
            ''')
        
        # Calculate error rate
        error_rate = 0
        if api_stats["total_requests"] > 0:
            error_rate = (api_stats["errors"] / api_stats["total_requests"]) * 100
        
        return {
            "api": {
                "requests": api_stats["total_requests"] or 0,
                "avg_response_time": float(api_stats["avg_response_time"] or 0),
                "max_response_time": float(api_stats["max_response_time"] or 0),
                "errors": api_stats["errors"] or 0,
                "error_rate": error_rate
            },
            "leads": {
                "total": lead_stats["total_leads"] or 0,
                "converted": lead_stats["converted"] or 0,
                "avg_value": float(lead_stats["avg_value"] or 0),
                "conversion_rate": (lead_stats["converted"] / lead_stats["total_leads"] * 100) if lead_stats["total_leads"] else 0
            },
            "revenue": {
                "total": float(revenue_stats["total_revenue"] or 0),
                "transactions": revenue_stats["total_transactions"] or 0
            },
            "errors": {
                "total": error_stats["total_errors"] or 0,
                "unique": error_stats["unique_errors"] or 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def detect_anomalies(self, metrics: Dict) -> List[Dict]:
        """Detect anomalies in metrics"""
        anomalies = []
        
        # Check error rate
        if metrics["api"]["error_rate"] > self.alert_thresholds["error_rate"]:
            anomalies.append({
                "type": "error_rate",
                "severity": "high",
                "value": metrics["api"]["error_rate"],
                "threshold": self.alert_thresholds["error_rate"],
                "message": f"Error rate {metrics['api']['error_rate']:.2f}% exceeds threshold"
            })
        
        # Check response time
        if metrics["api"]["avg_response_time"] > self.alert_thresholds["response_time"] / 1000:
            anomalies.append({
                "type": "response_time",
                "severity": "medium",
                "value": metrics["api"]["avg_response_time"],
                "threshold": self.alert_thresholds["response_time"] / 1000,
                "message": f"Average response time {metrics['api']['avg_response_time']:.2f}s exceeds threshold"
            })
        
        # Check for sudden drop in leads
        if metrics["leads"]["total"] == 0:
            anomalies.append({
                "type": "no_leads",
                "severity": "high",
                "message": "No leads captured in the last 24 hours"
            })
        
        # Check conversion rate
        if metrics["leads"]["conversion_rate"] < 5 and metrics["leads"]["total"] > 10:
            anomalies.append({
                "type": "low_conversion",
                "severity": "medium",
                "value": metrics["leads"]["conversion_rate"],
                "message": f"Conversion rate {metrics['leads']['conversion_rate']:.2f}% is below expected"
            })
        
        return anomalies
    
    async def generate_alerts(self, anomalies: List[Dict]):
        """Generate alerts for anomalies"""
        for anomaly in anomalies:
            # Check if similar alert already exists
            async with self.pg_pool.acquire() as conn:
                existing = await conn.fetchval('''
                    SELECT id FROM system_alerts
                    WHERE alert_type = $1
                    AND resolved = FALSE
                    AND created_at > NOW() - INTERVAL '1 hour'
                ''', anomaly["type"])
                
                if not existing:
                    # Create new alert
                    await conn.execute('''
                        INSERT INTO system_alerts (alert_type, severity, message, metadata)
                        VALUES ($1, $2, $3, $4)
                    ''', anomaly["type"], anomaly["severity"], anomaly["message"], json.dumps(anomaly))
                    
                    # Send notifications based on severity
                    if anomaly["severity"] == "high":
                        await self.send_critical_alert(anomaly)
                    elif anomaly["severity"] == "medium":
                        await self.send_warning_alert(anomaly)
    
    async def send_critical_alert(self, alert: Dict):
        """Send critical alert notifications"""
        logger.critical(f"CRITICAL ALERT: {alert['message']}")
        
        # Send to multiple channels
        # SMS via Twilio
        if os.getenv("TWILIO_ACCOUNT_SID"):
            # Implementation here
            pass
        
        # Slack
        if os.getenv("SLACK_WEBHOOK_URL"):
            async with aiohttp.ClientSession() as session:
                await session.post(
                    os.getenv("SLACK_WEBHOOK_URL"),
                    json={
                        "text": f"🚨 CRITICAL: {alert['message']}",
                        "attachments": [{
                            "color": "danger",
                            "fields": [
                                {"title": "Type", "value": alert["type"], "short": True},
                                {"title": "Severity", "value": alert["severity"], "short": True}
                            ]
                        }]
                    }
                )
    
    async def send_warning_alert(self, alert: Dict):
        """Send warning alert notifications"""
        logger.warning(f"WARNING ALERT: {alert['message']}")
        
        # Log to monitoring dashboard
        self.redis.rpush("alerts:warning", json.dumps(alert))
    
    async def store_monitoring_snapshot(self, health: Dict, metrics: Dict):
        """Store monitoring snapshot for historical analysis"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "health": health,
            "metrics": metrics
        }
        
        # Store in Redis for quick access
        self.redis.set(
            "monitoring:current_snapshot",
            json.dumps(snapshot),
            ex=300  # 5 minutes
        )
        
        # Store recent snapshots
        self.redis.lpush("monitoring:snapshots", json.dumps(snapshot))
        self.redis.ltrim("monitoring:snapshots", 0, 100)  # Keep last 100
    
    def update_prometheus_metrics(self, metrics: Dict):
        """Update Prometheus metrics"""
        # Update gauges
        self.active_users.set(metrics["leads"]["total"])
        self.error_rate.set(metrics["api"]["error_rate"])
        self.revenue_metrics.labels(type="daily").set(metrics["revenue"]["total"])
        self.lead_metrics.labels(status="total").set(metrics["leads"]["total"])
        self.lead_metrics.labels(status="converted").set(metrics["leads"]["converted"])
    
    async def aggregate_metrics(self):
        """Aggregate metrics for reporting"""
        while True:
            try:
                await self.generate_hourly_report()
                await asyncio.sleep(3600)  # Every hour
            except Exception as e:
                logger.error(f"Aggregation error: {e}")
                await asyncio.sleep(3600)
    
    async def generate_hourly_report(self):
        """Generate hourly metrics report"""
        async with self.pg_pool.acquire() as conn:
            report = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(duration_ms) / 1000.0 as avg_response_time,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) / 1000.0 as p95_response_time,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) / 1000.0 as p99_response_time,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors
                FROM api_metrics
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            ''')
            
            # Store hourly report
            await conn.execute('''
                INSERT INTO hourly_reports (
                    report_data, 
                    period_start, 
                    period_end, 
                    created_at
                ) VALUES ($1, $2, $3, NOW())
            ''', json.dumps(dict(report)), 
                datetime.now() - timedelta(hours=1),
                datetime.now()
            )
    
    async def check_sla_compliance(self):
        """Check SLA compliance"""
        while True:
            try:
                # Define SLA targets
                sla_targets = {
                    "uptime": 99.9,  # 99.9% uptime
                    "response_time_p95": 1.0,  # 95% of requests under 1 second
                    "error_rate": 1.0,  # Less than 1% error rate
                    "lead_response": 300  # Respond to leads within 5 minutes
                }
                
                async with self.pg_pool.acquire() as conn:
                    # Check each SLA
                    for metric, target in sla_targets.items():
                        actual = await self.calculate_sla_metric(metric, conn)
                        compliant = actual >= target if metric == "uptime" else actual <= target
                        
                        # Store compliance record
                        await conn.execute('''
                            INSERT INTO sla_compliance (
                                metric, target_value, actual_value, compliant, 
                                period_start, period_end
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                        ''', metric, target, actual, compliant,
                            datetime.now() - timedelta(hours=1),
                            datetime.now()
                        )
                        
                        if not compliant:
                            await self.generate_sla_violation_alert(metric, target, actual)
                
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"SLA check error: {e}")
                await asyncio.sleep(3600)
    
    async def calculate_sla_metric(self, metric: str, conn) -> float:
        """Calculate specific SLA metric"""
        if metric == "uptime":
            # Calculate uptime percentage
            total_checks = await conn.fetchval('''
                SELECT COUNT(*) FROM health_checks
                WHERE checked_at > NOW() - INTERVAL '24 hours'
                AND service = 'database'
            ''')
            
            healthy_checks = await conn.fetchval('''
                SELECT COUNT(*) FROM health_checks
                WHERE checked_at > NOW() - INTERVAL '24 hours'
                AND service = 'database'
                AND status = 'healthy'
            ''')
            
            return (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        elif metric == "response_time_p95":
            return await conn.fetchval('''
                SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) / 1000.0
                FROM api_metrics
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            ''') or 0
        
        elif metric == "error_rate":
            total = await conn.fetchval('''
                SELECT COUNT(*) FROM api_metrics
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            ''')
            
            errors = await conn.fetchval('''
                SELECT COUNT(*) FROM api_metrics
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                AND status_code >= 400
            ''')
            
            return (errors / total * 100) if total > 0 else 0
        
        return 0
    
    async def generate_sla_violation_alert(self, metric: str, target: float, actual: float):
        """Generate SLA violation alert"""
        alert = {
            "type": "sla_violation",
            "severity": "high",
            "metric": metric,
            "target": target,
            "actual": actual,
            "message": f"SLA violation: {metric} is {actual:.2f} (target: {target})"
        }
        
        await self.generate_alerts([alert])
    
    async def log_error(self, error_type: str, message: str, stack_trace: str = None):
        """Log error to database"""
        async with self.pg_pool.acquire() as conn:
            error_id = f"err_{uuid.uuid4().hex}"
            await conn.execute('''
                INSERT INTO ai_error_logs (error_id, error_type, error_message, stack_trace, component, severity, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', error_id, error_type, message, stack_trace, "monitoring_system", "error", json.dumps({"source": "monitoring_system"}))
    
    async def get_current_metrics(self) -> Dict:
        """Get current metrics for API response"""
        return await self.collect_current_metrics()
