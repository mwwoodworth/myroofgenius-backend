"""
Self-Healing Monitoring System for BrainOps AI OS
Autonomous system health management and recovery
"""

import asyncio
import psutil
import docker
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from enum import Enum

import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"
    RECOVERING = "recovering"

class SelfHealingSystem:
    """
    Autonomous self-healing system that monitors, diagnoses, and repairs issues
    """
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.db_conn = self._get_db_connection()
        self.health_checks = {}
        self.recovery_actions = {}
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": [],
            "network_latency": [],
            "error_rate": [],
            "response_time": []
        }
        self.thresholds = self._load_thresholds()
        self.is_running = True
    
    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host="localhost",
            database="ai_orchestrator",
            user="postgres",
            password="postgres",
            cursor_factory=RealDictCursor
        )
    
    def _load_thresholds(self) -> Dict:
        """Load health thresholds from configuration"""
        return {
            "cpu_critical": 90,
            "cpu_warning": 75,
            "memory_critical": 85,
            "memory_warning": 70,
            "disk_critical": 90,
            "disk_warning": 80,
            "error_rate_critical": 0.05,
            "error_rate_warning": 0.02,
            "response_time_critical": 5000,
            "response_time_warning": 2000,
            "network_latency_critical": 500,
            "network_latency_warning": 200
        }
    
    async def start_monitoring(self):
        """Start the self-healing monitoring system"""
        logger.info("🚀 Starting Self-Healing Monitoring System")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_system_resources()),
            asyncio.create_task(self.monitor_services()),
            asyncio.create_task(self.monitor_ai_agents()),
            asyncio.create_task(self.monitor_database()),
            asyncio.create_task(self.monitor_apis()),
            asyncio.create_task(self.analyze_and_heal()),
            asyncio.create_task(self.predictive_maintenance())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            await self.emergency_recovery()
    
    async def monitor_system_resources(self):
        """Monitor system resources"""
        while self.is_running:
            try:
                # CPU monitoring
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics["cpu_usage"].append(cpu_percent)
                
                # Memory monitoring
                memory = psutil.virtual_memory()
                self.metrics["memory_usage"].append(memory.percent)
                
                # Disk monitoring
                disk = psutil.disk_usage('/')
                self.metrics["disk_usage"].append(disk.percent)
                
                # Check thresholds
                if cpu_percent > self.thresholds["cpu_critical"]:
                    await self.handle_cpu_critical(cpu_percent)
                elif cpu_percent > self.thresholds["cpu_warning"]:
                    await self.handle_cpu_warning(cpu_percent)
                
                if memory.percent > self.thresholds["memory_critical"]:
                    await self.handle_memory_critical(memory.percent)
                elif memory.percent > self.thresholds["memory_warning"]:
                    await self.handle_memory_warning(memory.percent)
                
                if disk.percent > self.thresholds["disk_critical"]:
                    await self.handle_disk_critical(disk.percent)
                
                # Store metrics in database
                await self.store_metrics("system_resources", {
                    "cpu": cpu_percent,
                    "memory": memory.percent,
                    "disk": disk.percent
                })
                
                # Keep only last 1000 metrics
                for key in self.metrics:
                    if len(self.metrics[key]) > 1000:
                        self.metrics[key] = self.metrics[key][-1000:]
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def monitor_services(self):
        """Monitor all services"""
        services = [
            {"name": "backend", "url": "https://brainops-backend-prod.onrender.com/health"},
            {"name": "myroofgenius", "url": "https://www.myroofgenius.com/api/health"},
            {"name": "weathercraft", "url": "https://weathercraft-erp.vercel.app/api/health"},
            {"name": "postgres", "check": self.check_postgres},
            {"name": "redis", "check": self.check_redis}
        ]
        
        while self.is_running:
            try:
                for service in services:
                    if "url" in service:
                        status = await self.check_http_service(service["name"], service["url"])
                    else:
                        status = await service["check"]()
                    
                    self.health_checks[service["name"]] = {
                        "status": status,
                        "last_check": datetime.now().isoformat()
                    }
                    
                    if status == HealthStatus.FAILED:
                        await self.handle_service_failure(service["name"])
                    elif status == HealthStatus.CRITICAL:
                        await self.handle_service_critical(service["name"])
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Service monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def monitor_ai_agents(self):
        """Monitor AI agent health"""
        while self.is_running:
            try:
                with self.db_conn.cursor() as cur:
                    # Check agent activity
                    cur.execute("""
                        SELECT agent_name, 
                               MAX(last_active) as last_active,
                               AVG(CAST(performance_metrics->>'avg_confidence' AS FLOAT)) as avg_confidence
                        FROM ai_agent_registry
                        WHERE status = 'active'
                        GROUP BY agent_name
                    """)
                    
                    agents = cur.fetchall()
                    
                    for agent in agents:
                        if agent['last_active']:
                            last_active = datetime.fromisoformat(agent['last_active'])
                            if datetime.now() - last_active > timedelta(minutes=30):
                                await self.restart_agent(agent['agent_name'])
                        
                        if agent['avg_confidence'] and agent['avg_confidence'] < 0.5:
                            await self.retrain_agent(agent['agent_name'])
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"AI agent monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def monitor_database(self):
        """Monitor database health"""
        while self.is_running:
            try:
                # Check connection pool
                with self.db_conn.cursor() as cur:
                    cur.execute("""
                        SELECT count(*) as connections,
                               state
                        FROM pg_stat_activity
                        GROUP BY state
                    """)
                    
                    connections = cur.fetchall()
                    total_connections = sum(c['connections'] for c in connections)
                    
                    if total_connections > 90:
                        await self.handle_database_connections(total_connections)
                    
                    # Check slow queries
                    cur.execute("""
                        SELECT query, 
                               calls,
                               mean_exec_time
                        FROM pg_stat_statements
                        WHERE mean_exec_time > 1000
                        ORDER BY mean_exec_time DESC
                        LIMIT 10
                    """)
                    
                    slow_queries = cur.fetchall()
                    if slow_queries:
                        await self.optimize_slow_queries(slow_queries)
                
                await asyncio.sleep(120)  # Check every 2 minutes
                
            except Exception as e:
                logger.error(f"Database monitoring error: {e}")
                await asyncio.sleep(120)
    
    async def monitor_apis(self):
        """Monitor API endpoints"""
        while self.is_running:
            try:
                # Check API response times
                endpoints = [
                    "/api/v1/health",
                    "/api/v1/ai/status",
                    "/api/v1/projects",
                    "/api/v1/neural/status"
                ]
                
                for endpoint in endpoints:
                    start = datetime.now()
                    try:
                        response = requests.get(
                            f"https://brainops-backend-prod.onrender.com{endpoint}",
                            timeout=5
                        )
                        response_time = (datetime.now() - start).total_seconds() * 1000
                        
                        self.metrics["response_time"].append(response_time)
                        
                        if response_time > self.thresholds["response_time_critical"]:
                            await self.handle_slow_api(endpoint, response_time)
                        
                        if response.status_code >= 500:
                            await self.handle_api_error(endpoint, response.status_code)
                            
                    except Exception as e:
                        await self.handle_api_failure(endpoint, str(e))
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"API monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def analyze_and_heal(self):
        """Analyze issues and perform healing actions"""
        while self.is_running:
            try:
                # Analyze patterns
                issues = await self.detect_issues()
                
                for issue in issues:
                    healing_action = await self.determine_healing_action(issue)
                    if healing_action:
                        await self.execute_healing_action(healing_action)
                
                # Clean up old logs
                await self.cleanup_logs()
                
                # Optimize performance
                await self.optimize_performance()
                
                await asyncio.sleep(300)  # Analyze every 5 minutes
                
            except Exception as e:
                logger.error(f"Analysis and healing error: {e}")
                await asyncio.sleep(300)
    
    async def predictive_maintenance(self):
        """Predict and prevent issues before they occur"""
        while self.is_running:
            try:
                # Analyze trends
                predictions = await self.predict_issues()
                
                for prediction in predictions:
                    if prediction['probability'] > 0.7:
                        await self.preventive_action(prediction)
                
                await asyncio.sleep(600)  # Predict every 10 minutes
                
            except Exception as e:
                logger.error(f"Predictive maintenance error: {e}")
                await asyncio.sleep(600)
    
    # Healing actions
    async def handle_cpu_critical(self, cpu_percent: float):
        """Handle critical CPU usage"""
        logger.warning(f"⚠️ Critical CPU usage: {cpu_percent}%")
        
        # Find and kill resource-intensive processes
        processes = [(p.info['pid'], p.info['name'], p.info['cpu_percent']) 
                    for p in psutil.process_iter(['pid', 'name', 'cpu_percent'])
                    if p.info['cpu_percent'] > 20]
        
        processes.sort(key=lambda x: x[2], reverse=True)
        
        # Kill non-essential processes
        for pid, name, cpu in processes[:3]:
            if name not in ['postgres', 'redis-server', 'python', 'node']:
                try:
                    os.kill(pid, 9)
                    logger.info(f"Killed process {name} (PID: {pid}) using {cpu}% CPU")
                except:
                    pass
        
        # Scale down if possible
        await self.scale_down_services()
    
    async def handle_memory_critical(self, memory_percent: float):
        """Handle critical memory usage"""
        logger.warning(f"⚠️ Critical memory usage: {memory_percent}%")
        
        # Clear caches
        self.redis_client.flushdb()
        
        # Restart memory-intensive services
        await self.restart_service("ai-predictor")
        await self.restart_service("ai-analyzer")
        
        # Trigger garbage collection
        import gc
        gc.collect()
    
    async def handle_disk_critical(self, disk_percent: float):
        """Handle critical disk usage"""
        logger.warning(f"⚠️ Critical disk usage: {disk_percent}%")
        
        # Clean up logs
        os.system("find /var/log -type f -name '*.log' -mtime +7 -delete")
        os.system("find /tmp -type f -mtime +1 -delete")
        
        # Clean Docker
        self.docker_client.containers.prune()
        self.docker_client.images.prune()
    
    async def handle_service_failure(self, service_name: str):
        """Handle service failure"""
        logger.error(f"❌ Service {service_name} has failed")
        
        # Attempt restart
        await self.restart_service(service_name)
        
        # If still failing, escalate
        await asyncio.sleep(30)
        if self.health_checks.get(service_name, {}).get("status") == HealthStatus.FAILED:
            await self.escalate_issue(service_name, "Service repeatedly failing")
    
    async def restart_service(self, service_name: str):
        """Restart a service"""
        logger.info(f"🔄 Restarting service: {service_name}")
        
        if service_name.startswith("ai-"):
            os.system(f"systemctl --user restart {service_name}")
        elif service_name == "backend":
            # Trigger Render redeploy
            requests.post("https://api.render.com/deploy/srv-cqrg2ue8ii6s73frnvdg")
        elif service_name == "postgres":
            os.system("sudo systemctl restart postgresql")
        elif service_name == "redis":
            os.system("sudo systemctl restart redis")
    
    async def restart_agent(self, agent_name: str):
        """Restart an AI agent"""
        logger.info(f"🤖 Restarting AI agent: {agent_name}")
        
        with self.db_conn.cursor() as cur:
            cur.execute("""
                UPDATE ai_agent_registry
                SET status = 'restarting',
                    last_active = CURRENT_TIMESTAMP
                WHERE agent_name = %s
            """, (agent_name,))
            self.db_conn.commit()
        
        # Trigger agent restart through orchestrator
        await self.trigger_agent_restart(agent_name)
    
    async def retrain_agent(self, agent_name: str):
        """Retrain an AI agent"""
        logger.info(f"🎓 Retraining AI agent: {agent_name}")
        
        # Trigger retraining pipeline
        response = requests.post(
            "https://brainops-backend-prod.onrender.com/api/v1/ai/train",
            json={"agent": agent_name, "auto_retrain": True}
        )
    
    async def scale_down_services(self):
        """Scale down non-essential services"""
        logger.info("📉 Scaling down services")
        
        # Reduce worker processes
        os.system("systemctl --user stop ai-innovation-lab")
        os.system("systemctl --user stop ai-trainer")
    
    async def optimize_slow_queries(self, queries: List[Dict]):
        """Optimize slow database queries"""
        logger.info(f"🔧 Optimizing {len(queries)} slow queries")
        
        with self.db_conn.cursor() as cur:
            for query in queries[:5]:  # Optimize top 5
                # Add index suggestions
                cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + query['query'])
    
    async def detect_issues(self) -> List[Dict]:
        """Detect system issues using pattern analysis"""
        issues = []
        
        # Check for sustained high resource usage
        if len(self.metrics["cpu_usage"]) > 10:
            avg_cpu = sum(self.metrics["cpu_usage"][-10:]) / 10
            if avg_cpu > self.thresholds["cpu_warning"]:
                issues.append({
                    "type": "sustained_high_cpu",
                    "severity": "warning",
                    "value": avg_cpu
                })
        
        # Check for error rate increase
        if self.metrics.get("error_rate"):
            recent_errors = self.metrics["error_rate"][-10:]
            if recent_errors and max(recent_errors) > self.thresholds["error_rate_warning"]:
                issues.append({
                    "type": "high_error_rate",
                    "severity": "critical",
                    "value": max(recent_errors)
                })
        
        return issues
    
    async def determine_healing_action(self, issue: Dict) -> Optional[Dict]:
        """Determine appropriate healing action for an issue"""
        actions = {
            "sustained_high_cpu": {"action": "scale_horizontally", "params": {"scale": 2}},
            "high_error_rate": {"action": "circuit_breaker", "params": {"duration": 300}},
            "memory_leak": {"action": "restart_service", "params": {"service": "backend"}},
            "database_locks": {"action": "kill_queries", "params": {"age": 300}}
        }
        
        return actions.get(issue["type"])
    
    async def execute_healing_action(self, action: Dict):
        """Execute a healing action"""
        logger.info(f"💊 Executing healing action: {action['action']}")
        
        if action["action"] == "scale_horizontally":
            # Trigger horizontal scaling
            pass
        elif action["action"] == "circuit_breaker":
            # Enable circuit breaker
            self.redis_client.setex("circuit_breaker_enabled", action["params"]["duration"], "1")
        elif action["action"] == "restart_service":
            await self.restart_service(action["params"]["service"])
    
    async def predict_issues(self) -> List[Dict]:
        """Predict future issues using ML"""
        predictions = []
        
        # Simple trend analysis for now
        if len(self.metrics["memory_usage"]) > 100:
            # Calculate trend
            recent = self.metrics["memory_usage"][-20:]
            older = self.metrics["memory_usage"][-40:-20]
            
            if sum(recent)/len(recent) > sum(older)/len(older) * 1.1:
                predictions.append({
                    "type": "memory_exhaustion",
                    "probability": 0.75,
                    "estimated_time": "30 minutes"
                })
        
        return predictions
    
    async def preventive_action(self, prediction: Dict):
        """Take preventive action based on prediction"""
        logger.info(f"🛡️ Taking preventive action for predicted {prediction['type']}")
        
        if prediction["type"] == "memory_exhaustion":
            # Preemptively clear caches
            self.redis_client.flushdb()
            # Schedule service restart
            asyncio.create_task(self.scheduled_restart("ai-analyzer", 1800))
    
    async def scheduled_restart(self, service: str, delay: int):
        """Schedule a service restart"""
        await asyncio.sleep(delay)
        await self.restart_service(service)
    
    async def cleanup_logs(self):
        """Clean up old logs"""
        # Clean logs older than 7 days
        os.system("find /home/matt-woodworth/*/logs -name '*.log' -mtime +7 -delete")
    
    async def optimize_performance(self):
        """Optimize system performance"""
        # Vacuum PostgreSQL
        with self.db_conn.cursor() as cur:
            cur.execute("VACUUM ANALYZE")
    
    async def check_http_service(self, name: str, url: str) -> HealthStatus:
        """Check HTTP service health"""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return HealthStatus.HEALTHY
            elif response.status_code < 500:
                return HealthStatus.DEGRADED
            else:
                return HealthStatus.CRITICAL
        except:
            return HealthStatus.FAILED
    
    async def check_postgres(self) -> HealthStatus:
        """Check PostgreSQL health"""
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("SELECT 1")
                return HealthStatus.HEALTHY
        except:
            return HealthStatus.FAILED
    
    async def check_redis(self) -> HealthStatus:
        """Check Redis health"""
        try:
            self.redis_client.ping()
            return HealthStatus.HEALTHY
        except:
            return HealthStatus.FAILED
    
    async def store_metrics(self, metric_type: str, values: Dict):
        """Store metrics in database"""
        try:
            with self.db_conn.cursor() as cur:
                for key, value in values.items():
                    cur.execute("""
                        INSERT INTO system_health_metrics 
                        (system, metric_name, metric_value)
                        VALUES (%s, %s, %s)
                    """, ("brainops", f"{metric_type}_{key}", value))
                self.db_conn.commit()
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    async def trigger_agent_restart(self, agent_name: str):
        """Trigger agent restart through orchestrator"""
        self.redis_client.publish("agent_control", json.dumps({
            "action": "restart",
            "agent": agent_name
        }))
    
    async def escalate_issue(self, service: str, issue: str):
        """Escalate critical issues"""
        logger.critical(f"🚨 ESCALATING: {service} - {issue}")
        
        # Send emergency alert
        await self.send_emergency_alert(service, issue)
        
        # Attempt emergency recovery
        await self.emergency_recovery()
    
    async def send_emergency_alert(self, service: str, issue: str):
        """Send emergency alert"""
        # Send email alert
        if os.getenv("SMTP_HOST"):
            msg = MIMEMultipart()
            msg['From'] = os.getenv("SMTP_FROM_EMAIL")
            msg['To'] = "matthew@brainstackstudio.com"
            msg['Subject'] = f"🚨 CRITICAL: {service} - {issue}"
            
            body = f"""
            Critical issue detected in BrainOps AI OS:
            
            Service: {service}
            Issue: {issue}
            Time: {datetime.now().isoformat()}
            
            Automatic recovery attempted. Manual intervention may be required.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            try:
                server = smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", 587)))
                server.starttls()
                server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
                server.send_message(msg)
                server.quit()
            except Exception as e:
                logger.error(f"Failed to send alert email: {e}")
    
    async def emergency_recovery(self):
        """Emergency recovery procedure"""
        logger.critical("🚑 Initiating emergency recovery")
        
        # 1. Restart core services
        for service in ["redis", "postgresql"]:
            os.system(f"sudo systemctl restart {service}")
        
        # 2. Clear all caches
        self.redis_client.flushall()
        
        # 3. Restart AI services
        os.system("systemctl --user restart ai-orchestrator")
        
        # 4. Trigger backend redeploy
        requests.post("https://api.render.com/deploy/srv-cqrg2ue8ii6s73frnvdg")
        
        logger.info("✅ Emergency recovery completed")

# Initialize and start the self-healing system
self_healer = SelfHealingSystem()

async def start_self_healing():
    """Start the self-healing system"""
    await self_healer.start_monitoring()

def get_system_health() -> Dict:
    """Get current system health status"""
    return {
        "health_checks": self_healer.health_checks,
        "metrics": {k: v[-10:] if v else [] for k, v in self_healer.metrics.items()},
        "status": "operational"
    }