"""
Infrastructure Manager - Handles all infrastructure, scaling, and resource management
"""

import os
import asyncio
import psutil
import docker
import asyncpg
import redis
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import subprocess
import aiohttp

logger = logging.getLogger(__name__)

class InfrastructureManager:
    """Manages all infrastructure components"""
    
    def __init__(self, pg_pool, redis_client):
        self.pg_pool = pg_pool
        self.redis = redis_client
        self.docker_client = None
        self.scaling_rules = {
            "cpu_threshold": 80,  # Scale up at 80% CPU
            "memory_threshold": 85,  # Scale up at 85% memory
            "request_rate_threshold": 1000,  # Requests per minute
            "response_time_threshold": 2.0,  # Seconds
            "scale_up_increment": 1,
            "scale_down_decrement": 1,
            "min_instances": 1,
            "max_instances": 10,
            "cooldown_period": 300  # 5 minutes
        }
        self.last_scale_time = None
        
    async def initialize(self):
        """Initialize infrastructure manager"""
        try:
            # Initialize Docker client if available
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker client initialized")
            except Exception as e:
                logger.warning(f"Docker not available: {e}")
            
            # Initialize infrastructure tables
            await self._init_infrastructure_tables()
            
            # Start resource monitoring
            asyncio.create_task(self.monitor_resources())
            
            logger.info("Infrastructure manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize infrastructure: {e}")
    
    async def _init_infrastructure_tables(self):
        """Initialize infrastructure tables"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS infrastructure_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_type VARCHAR(50),
                    value FLOAT,
                    metadata JSONB,
                    recorded_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS scaling_events (
                    id SERIAL PRIMARY KEY,
                    action VARCHAR(50),
                    reason TEXT,
                    old_instances INT,
                    new_instances INT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS resource_allocation (
                    id SERIAL PRIMARY KEY,
                    resource_type VARCHAR(50),
                    allocated_to VARCHAR(100),
                    amount FLOAT,
                    unit VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW(),
                    released_at TIMESTAMP
                )
            ''')
    
    async def monitor_resources(self):
        """Continuously monitor system resources"""
        while True:
            try:
                metrics = await self.collect_metrics()
                await self.store_metrics(metrics)
                await self.check_resource_alerts(metrics)
                
                # Store in Redis for real-time access
                self.redis.set(
                    "infrastructure:current_metrics",
                    json.dumps(metrics),
                    ex=60
                )
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics
        network = psutil.net_io_counters()
        
        # Process metrics
        process = psutil.Process()
        
        # Docker metrics if available
        docker_stats = {}
        if self.docker_client:
            try:
                containers = self.docker_client.containers.list()
                docker_stats = {
                    "running_containers": len(containers),
                    "container_stats": []
                }
                
                for container in containers:
                    stats = container.stats(stream=False)
                    docker_stats["container_stats"].append({
                        "name": container.name,
                        "status": container.status,
                        "cpu": self._calculate_cpu_percent(stats),
                        "memory": stats.get("memory_stats", {}).get("usage", 0)
                    })
            except Exception as e:
                logger.warning(f"Error getting Docker stats: {e}")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "load_average": os.getloadavg()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            "process": {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0
            },
            "docker": docker_stats
        }
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU percentage from Docker stats"""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            
            if system_delta > 0 and cpu_delta > 0:
                return (cpu_delta / system_delta) * 100.0
        except Exception as e:
            logger.warning(f"Error calculating CPU percent: {e}")
        return 0.0
    
    async def store_metrics(self, metrics: Dict):
        """Store metrics in database"""
        async with self.pg_pool.acquire() as conn:
            # Store key metrics
            await conn.execute('''
                INSERT INTO infrastructure_metrics (metric_type, value, metadata)
                VALUES 
                    ('cpu_percent', $1, $2),
                    ('memory_percent', $3, $4),
                    ('disk_percent', $5, $6)
            ''',
                metrics["cpu"]["percent"], json.dumps(metrics["cpu"]),
                metrics["memory"]["percent"], json.dumps(metrics["memory"]),
                metrics["disk"]["percent"], json.dumps(metrics["disk"])
            )
    
    async def check_resource_alerts(self, metrics: Dict):
        """Check for resource alerts and trigger actions"""
        alerts = []
        
        # CPU alert
        if metrics["cpu"]["percent"] > 90:
            alerts.append({
                "type": "critical",
                "resource": "cpu",
                "value": metrics["cpu"]["percent"],
                "message": f"CPU usage critical: {metrics['cpu']['percent']}%"
            })
        elif metrics["cpu"]["percent"] > 75:
            alerts.append({
                "type": "warning",
                "resource": "cpu",
                "value": metrics["cpu"]["percent"],
                "message": f"CPU usage high: {metrics['cpu']['percent']}%"
            })
        
        # Memory alert
        if metrics["memory"]["percent"] > 90:
            alerts.append({
                "type": "critical",
                "resource": "memory",
                "value": metrics["memory"]["percent"],
                "message": f"Memory usage critical: {metrics['memory']['percent']}%"
            })
        
        # Disk alert
        if metrics["disk"]["percent"] > 90:
            alerts.append({
                "type": "critical",
                "resource": "disk",
                "value": metrics["disk"]["percent"],
                "message": f"Disk usage critical: {metrics['disk']['percent']}%"
            })
        
        # Send alerts
        for alert in alerts:
            await self.send_alert(alert)
    
    async def send_alert(self, alert: Dict):
        """Send infrastructure alert"""
        # Store alert
        async with self.pg_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO system_alerts (alert_type, severity, message, metadata, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            ''', alert["resource"], alert["type"], alert["message"], json.dumps(alert))
        
        # Send to monitoring endpoints
        if alert["type"] == "critical":
            # Send to PagerDuty, Slack, etc.
            logger.critical(f"INFRASTRUCTURE ALERT: {alert['message']}")
    
    async def auto_scaling_monitor(self):
        """Monitor and perform auto-scaling"""
        while True:
            try:
                # Check if we should scale
                should_scale = await self.check_scaling_conditions()
                
                if should_scale:
                    await self.perform_scaling(should_scale)
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Auto-scaling error: {e}")
                await asyncio.sleep(120)
    
    async def check_scaling_conditions(self) -> Optional[str]:
        """Check if scaling is needed"""
        # Check cooldown period
        if self.last_scale_time:
            time_since_scale = (datetime.now() - self.last_scale_time).seconds
            if time_since_scale < self.scaling_rules["cooldown_period"]:
                return None
        
        # Get current metrics
        metrics_json = self.redis.get("infrastructure:current_metrics")
        if not metrics_json:
            return None
        
        metrics = json.loads(metrics_json)
        
        # Check CPU
        if metrics["cpu"]["percent"] > self.scaling_rules["cpu_threshold"]:
            return "scale_up"
        elif metrics["cpu"]["percent"] < 30:  # Scale down threshold
            return "scale_down"
        
        # Check memory
        if metrics["memory"]["percent"] > self.scaling_rules["memory_threshold"]:
            return "scale_up"
        
        # Check response time (from monitoring system)
        response_time = await self.get_average_response_time()
        if response_time and response_time > self.scaling_rules["response_time_threshold"]:
            return "scale_up"
        
        return None
    
    async def get_average_response_time(self) -> Optional[float]:
        """Get average response time from monitoring"""
        try:
            async with self.pg_pool.acquire() as conn:
                avg_time = await conn.fetchval('''
                    SELECT AVG(duration_ms) / 1000.0
                    FROM api_metrics 
                    WHERE timestamp > NOW() - INTERVAL '5 minutes'
                ''')
                return avg_time
        except Exception as e:
            logger.error(f"Error getting average response time: {e}")
            return None
    
    async def perform_scaling(self, action: str):
        """Perform scaling action"""
        try:
            current_instances = await self.get_current_instances()
            
            if action == "scale_up":
                new_instances = min(
                    current_instances + self.scaling_rules["scale_up_increment"],
                    self.scaling_rules["max_instances"]
                )
            else:  # scale_down
                new_instances = max(
                    current_instances - self.scaling_rules["scale_down_decrement"],
                    self.scaling_rules["min_instances"]
                )
            
            if new_instances != current_instances:
                # Perform actual scaling (platform-specific)
                await self.scale_to_instances(new_instances)
                
                # Record scaling event
                async with self.pg_pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO scaling_events (action, reason, old_instances, new_instances)
                        VALUES ($1, $2, $3, $4)
                    ''', action, f"Auto-scaling based on metrics", current_instances, new_instances)
                
                self.last_scale_time = datetime.now()
                
                logger.info(f"Scaled from {current_instances} to {new_instances} instances")
        except Exception as e:
            logger.error(f"Scaling failed: {e}")
    
    async def get_current_instances(self) -> int:
        """Get current number of instances"""
        # This would be platform-specific (Render, AWS, etc.)
        # For now, return from Redis cache
        instances = self.redis.get("infrastructure:current_instances")
        return int(instances) if instances else 1
    
    async def scale_to_instances(self, count: int):
        """Scale to specific number of instances"""
        # Platform-specific implementation
        # For Render.com
        if os.getenv("RENDER_SERVICE_ID"):
            await self.scale_render_service(count)
        # For AWS
        elif os.getenv("AWS_REGION"):
            await self.scale_aws_service(count)
        # For local Docker
        elif self.docker_client:
            await self.scale_docker_containers(count)
        
        # Update cache
        self.redis.set("infrastructure:current_instances", count)
    
    async def scale_render_service(self, count: int):
        """Scale Render.com service"""
        api_key = os.getenv("RENDER_API_KEY")
        service_id = os.getenv("RENDER_SERVICE_ID")
        
        if not api_key or not service_id:
            logger.warning("Render scaling not configured")
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"https://api.render.com/v1/services/{service_id}",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={"numInstances": count}
            ) as response:
                if response.status == 200:
                    logger.info(f"Render service scaled to {count} instances")
                else:
                    logger.error(f"Render scaling failed: {await response.text()}")
    
    async def scale_aws_service(self, count: int):
        """Scale AWS ECS/Fargate service"""
        # AWS scaling implementation
        pass
    
    async def scale_docker_containers(self, count: int):
        """Scale local Docker containers"""
        if not self.docker_client:
            return
        
        try:
            # Get current containers
            containers = self.docker_client.containers.list(
                filters={"label": "app=myroofgenius"}
            )
            current_count = len(containers)
            
            if count > current_count:
                # Start new containers
                for i in range(count - current_count):
                    self.docker_client.containers.run(
                        "myroofgenius:latest",
                        detach=True,
                        labels={"app": "myroofgenius"},
                        environment=os.environ,
                        network="myroofgenius-network"
                    )
            elif count < current_count:
                # Stop excess containers
                to_stop = current_count - count
                for container in containers[:to_stop]:
                    container.stop()
                    container.remove()
            
            logger.info(f"Docker containers scaled to {count}")
        except Exception as e:
            logger.error(f"Docker scaling failed: {e}")
    
    async def optimize_resources(self):
        """Optimize resource allocation"""
        # Clean up old data
        async with self.pg_pool.acquire() as conn:
            # Clean old metrics
            await conn.execute('''
                DELETE FROM infrastructure_metrics 
                WHERE recorded_at < NOW() - INTERVAL '7 days'
            ''')
            
            # Clean old alerts
            await conn.execute('''
                DELETE FROM system_alerts 
                WHERE created_at < NOW() - INTERVAL '30 days'
            ''')
        
        # Optimize database
        await self.optimize_database()
        
        # Clean Redis
        self.clean_redis_cache()
    
    async def optimize_database(self):
        """Optimize database performance"""
        async with self.pg_pool.acquire() as conn:
            # Analyze tables
            await conn.execute("ANALYZE")
            
            # Reindex if needed
            await conn.execute("REINDEX DATABASE CONCURRENTLY myroofgenius")
    
    def clean_redis_cache(self):
        """Clean up Redis cache"""
        # Remove expired keys
        for key in self.redis.scan_iter("temp:*"):
            self.redis.delete(key)
    
    async def get_infrastructure_status(self) -> Dict:
        """Get current infrastructure status"""
        metrics = json.loads(self.redis.get("infrastructure:current_metrics") or "{}")
        instances = self.redis.get("infrastructure:current_instances") or "1"
        
        # Get recent scaling events
        async with self.pg_pool.acquire() as conn:
            recent_scaling = await conn.fetch('''
                SELECT * FROM scaling_events 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
        
        return {
            "current_metrics": metrics,
            "instances": int(instances),
            "scaling_rules": self.scaling_rules,
            "recent_scaling_events": [dict(r) for r in recent_scaling],
            "status": "healthy" if metrics.get("cpu", {}).get("percent", 0) < 80 else "stressed"
        }
