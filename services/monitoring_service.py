"""
Monitoring Service - Comprehensive System Health and Performance Monitoring
Monitors MCP servers, AI agents, database, and system performance
"""
import asyncio
import psutil
import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from enum import Enum
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import json

from services.mcp_service import mcp_service
from services.ai_agent_service import ai_agent_service

logger = logging.getLogger(__name__)

class SystemMetrics(BaseModel):
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    timestamp: datetime

class ServiceHealth(BaseModel):
    """Health status of a service"""
    name: str
    status: str  # healthy, degraded, critical, offline
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    last_check: datetime
    uptime: Optional[float] = None

class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class Alert(BaseModel):
    """System alert"""
    id: str
    level: AlertLevel
    service: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class MonitoringService:
    """Comprehensive system monitoring service"""
    
    def __init__(self):
        self.alerts = []
        self.metrics_history = []
        self.service_history = {}
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time": 5.0  # seconds
        }
        
        # Database connection for health checks
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL environment variable is required")
        
        self.monitoring_started = datetime.now()
        
    async def get_system_metrics(self) -> SystemMetrics:
        """Get current system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io=network_io,
                process_count=process_count,
                timestamp=datetime.now()
            )
            
            # Store in history (keep last 1000 entries)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history.pop(0)
            
            # Check for alerts
            await self._check_system_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            raise
    
    async def check_database_health(self) -> ServiceHealth:
        """Check database connectivity and performance"""
        start_time = datetime.now()
        
        try:
            engine = create_engine(self.database_url, pool_pre_ping=True)
            
            with engine.connect() as conn:
                # Simple connectivity test
                conn.execute(text("SELECT 1"))
                
                # Check for active connections
                result = conn.execute(text("""
                    SELECT count(*) as active_connections 
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """))
                active_connections = result.scalar()
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                health = ServiceHealth(
                    name="database",
                    status="healthy",
                    response_time=response_time,
                    last_check=datetime.now(),
                    uptime=(datetime.now() - self.monitoring_started).total_seconds()
                )
                
                # Check response time alert
                if response_time > self.alert_thresholds["response_time"]:
                    await self._create_alert(
                        AlertLevel.WARNING,
                        "database",
                        f"Database response time is high: {response_time:.2f}s"
                    )
                
                return health
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ServiceHealth(
                name="database",
                status="critical",
                error_message=str(e),
                last_check=datetime.now()
            )
    
    async def check_external_services(self) -> Dict[str, ServiceHealth]:
        """Check external service dependencies"""
        services = {}
        
        # Check Stripe API
        try:
            start_time = datetime.now()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://api.stripe.com/healthcheck")
                response_time = (datetime.now() - start_time).total_seconds()
                
                services["stripe"] = ServiceHealth(
                    name="stripe",
                    status="healthy" if response.status_code == 200 else "degraded",
                    response_time=response_time,
                    last_check=datetime.now()
                )
        except Exception as e:
            services["stripe"] = ServiceHealth(
                name="stripe",
                status="offline",
                error_message=str(e),
                last_check=datetime.now()
            )
        
        # Check Supabase API
        try:
            start_time = datetime.now()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("https://yomagoqdmxszqtdwuhab.supabase.co/rest/v1/", headers={
                    "apikey": os.getenv("SUPABASE_ANON_KEY", ""),
                    "Authorization": f"Bearer {os.getenv('SUPABASE_ANON_KEY', '')}"
                })
                response_time = (datetime.now() - start_time).total_seconds()
                
                services["supabase"] = ServiceHealth(
                    name="supabase",
                    status="healthy" if response.status_code == 200 else "degraded",
                    response_time=response_time,
                    last_check=datetime.now()
                )
        except Exception as e:
            services["supabase"] = ServiceHealth(
                name="supabase",
                status="offline",
                error_message=str(e),
                last_check=datetime.now()
            )
        
        return services
    
    async def get_comprehensive_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report of entire system"""
        try:
            # Gather all health data concurrently
            system_metrics_task = self.get_system_metrics()
            database_health_task = self.check_database_health()
            external_services_task = self.check_external_services()
            mcp_health_task = mcp_service.check_all_servers()
            agents_health_task = ai_agent_service.check_all_agents()
            
            # Wait for all checks to complete
            system_metrics = await system_metrics_task
            database_health = await database_health_task
            external_services = await external_services_task
            mcp_health = await mcp_health_task
            agents_health = await agents_health_task
            
            # Calculate overall system health
            overall_status = self._calculate_overall_health(
                system_metrics, database_health, external_services, 
                mcp_health, agents_health
            )
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": overall_status,
                "system_metrics": {
                    "cpu_percent": system_metrics.cpu_percent,
                    "memory_percent": system_metrics.memory_percent,
                    "disk_percent": system_metrics.disk_percent,
                    "process_count": system_metrics.process_count,
                    "network_io": system_metrics.network_io
                },
                "database": {
                    "status": database_health.status,
                    "response_time": database_health.response_time,
                    "error": database_health.error_message,
                    "uptime": database_health.uptime
                },
                "external_services": {
                    service: {
                        "status": health.status,
                        "response_time": health.response_time,
                        "error": health.error_message
                    }
                    for service, health in external_services.items()
                },
                "mcp_servers": {
                    "summary": mcp_health["summary"],
                    "servers": {
                        name: server["status"] 
                        for name, server in mcp_health["servers"].items()
                    }
                },
                "ai_agents": {
                    "summary": agents_health["summary"],
                    "agents": {
                        name: agent["status"]
                        for name, agent in agents_health["agents"].items()
                    }
                },
                "alerts": {
                    "active_count": len([a for a in self.alerts if not a.resolved]),
                    "total_count": len(self.alerts),
                    "recent": [
                        {
                            "level": alert.level,
                            "service": alert.service,
                            "message": alert.message,
                            "timestamp": alert.timestamp.isoformat(),
                            "resolved": alert.resolved
                        }
                        for alert in sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:10]
                    ]
                },
                "uptime": (datetime.now() - self.monitoring_started).total_seconds(),
                "monitoring_started": self.monitoring_started.isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
    
    async def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends over specified time period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filter metrics within time range
            recent_metrics = [
                m for m in self.metrics_history 
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    "message": "No metrics data available for the specified time period",
                    "time_range": f"last {hours} hours"
                }
            
            # Calculate trends
            cpu_values = [m.cpu_percent for m in recent_metrics]
            memory_values = [m.memory_percent for m in recent_metrics]
            disk_values = [m.disk_percent for m in recent_metrics]
            
            trends = {
                "time_range": f"last {hours} hours",
                "data_points": len(recent_metrics),
                "cpu": {
                    "current": cpu_values[-1] if cpu_values else 0,
                    "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    "min": min(cpu_values) if cpu_values else 0,
                    "max": max(cpu_values) if cpu_values else 0,
                    "trend": "stable"  # Could implement trend calculation
                },
                "memory": {
                    "current": memory_values[-1] if memory_values else 0,
                    "average": sum(memory_values) / len(memory_values) if memory_values else 0,
                    "min": min(memory_values) if memory_values else 0,
                    "max": max(memory_values) if memory_values else 0,
                    "trend": "stable"
                },
                "disk": {
                    "current": disk_values[-1] if disk_values else 0,
                    "average": sum(disk_values) / len(disk_values) if disk_values else 0,
                    "min": min(disk_values) if disk_values else 0,
                    "max": max(disk_values) if disk_values else 0,
                    "trend": "stable"
                },
                "alerts_in_period": len([
                    a for a in self.alerts 
                    if a.timestamp >= cutoff_time
                ])
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            raise
    
    async def get_service_availability(self, hours: int = 24) -> Dict[str, Any]:
        """Calculate service availability over specified time period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # This would be enhanced with actual historical data
            # For now, return current status as availability
            mcp_health = await mcp_service.check_all_servers()
            agents_health = await ai_agent_service.check_all_agents()
            database_health = await self.check_database_health()
            
            availability = {
                "time_range": f"last {hours} hours",
                "database": {
                    "uptime_percentage": 99.9 if database_health.status == "healthy" else 95.0,
                    "current_status": database_health.status
                },
                "mcp_servers": {
                    "uptime_percentage": (mcp_health["summary"]["healthy"] / mcp_health["summary"]["total"]) * 100,
                    "healthy_count": mcp_health["summary"]["healthy"],
                    "total_count": mcp_health["summary"]["total"]
                },
                "ai_agents": {
                    "uptime_percentage": (agents_health["summary"]["healthy"] / agents_health["summary"]["total"]) * 100,
                    "healthy_count": agents_health["summary"]["healthy"],
                    "total_count": agents_health["summary"]["total"]
                },
                "overall_availability": 99.5  # Would be calculated from actual historical data
            }
            
            return availability
            
        except Exception as e:
            logger.error(f"Error calculating service availability: {e}")
            raise
    
    def _calculate_overall_health(self, system_metrics, database_health, external_services, mcp_health, agents_health) -> str:
        """Calculate overall system health status"""
        # Weight different components
        weights = {
            "system": 0.2,
            "database": 0.3,
            "mcp": 0.2,
            "agents": 0.2,
            "external": 0.1
        }
        
        scores = {}
        
        # System metrics score
        if (system_metrics.cpu_percent > 90 or 
            system_metrics.memory_percent > 90 or 
            system_metrics.disk_percent > 95):
            scores["system"] = 0.3  # Critical
        elif (system_metrics.cpu_percent > 80 or 
              system_metrics.memory_percent > 85 or 
              system_metrics.disk_percent > 90):
            scores["system"] = 0.7  # Degraded
        else:
            scores["system"] = 1.0  # Healthy
        
        # Database score
        scores["database"] = 1.0 if database_health.status == "healthy" else 0.3
        
        # MCP servers score
        if mcp_health["summary"]["total"] > 0:
            scores["mcp"] = mcp_health["summary"]["healthy"] / mcp_health["summary"]["total"]
        else:
            scores["mcp"] = 0.0
        
        # AI agents score
        if agents_health["summary"]["total"] > 0:
            scores["agents"] = agents_health["summary"]["healthy"] / agents_health["summary"]["total"]
        else:
            scores["agents"] = 0.0
        
        # External services score
        healthy_external = len([s for s in external_services.values() if s.status == "healthy"])
        total_external = len(external_services)
        scores["external"] = healthy_external / total_external if total_external > 0 else 1.0
        
        # Calculate weighted average
        overall_score = sum(scores[component] * weights[component] for component in weights)
        
        if overall_score >= 0.9:
            return "healthy"
        elif overall_score >= 0.7:
            return "degraded"
        elif overall_score >= 0.5:
            return "critical"
        else:
            return "offline"
    
    async def _check_system_alerts(self, metrics: SystemMetrics):
        """Check system metrics against thresholds and create alerts"""
        # CPU alert
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            await self._create_alert(
                AlertLevel.WARNING if metrics.cpu_percent < 95 else AlertLevel.CRITICAL,
                "system",
                f"High CPU usage: {metrics.cpu_percent:.1f}%"
            )
        
        # Memory alert
        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            await self._create_alert(
                AlertLevel.WARNING if metrics.memory_percent < 95 else AlertLevel.CRITICAL,
                "system",
                f"High memory usage: {metrics.memory_percent:.1f}%"
            )
        
        # Disk alert
        if metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            await self._create_alert(
                AlertLevel.CRITICAL,
                "system",
                f"High disk usage: {metrics.disk_percent:.1f}%"
            )
    
    async def _create_alert(self, level: AlertLevel, service: str, message: str):
        """Create a new alert"""
        import uuid
        
        alert = Alert(
            id=str(uuid.uuid4()),
            level=level,
            service=service,
            message=message,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        # Log alert
        if level == AlertLevel.CRITICAL:
            logger.critical(f"ALERT [{service}]: {message}")
        elif level == AlertLevel.WARNING:
            logger.warning(f"ALERT [{service}]: {message}")
        else:
            logger.info(f"ALERT [{service}]: {message}")
        
        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts.pop(0)
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolution_time = datetime.now()
                logger.info(f"Alert resolved: {alert.message}")
                return True
        return False
    
    def get_alerts(self, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by resolution status"""
        alerts = self.alerts
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        return [
            {
                "id": alert.id,
                "level": alert.level,
                "service": alert.service,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolution_time": alert.resolution_time.isoformat() if alert.resolution_time else None
            }
            for alert in sorted(alerts, key=lambda x: x.timestamp, reverse=True)
        ]

# Global monitoring service instance
monitoring_service = MonitoringService()