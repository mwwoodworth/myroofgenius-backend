#!/usr/bin/env python3
"""
AI DevOps Monitoring and Auto-Healing System
Comprehensive monitoring, alerting, and automatic recovery for AI infrastructure
"""

import asyncio
import json
import logging
import time
import os
import subprocess
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import redis
import docker
from prometheus_client import CollectorRegistry, Gauge, Counter, start_http_server
import schedule

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    check_function: Callable
    interval_seconds: int
    timeout_seconds: int
    failure_threshold: int
    recovery_action: Optional[Callable] = None
    alert_on_failure: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Alert:
    """Alert message structure"""
    id: str
    timestamp: datetime
    severity: str  # critical, warning, info
    component: str
    message: str
    metadata: Dict[str, Any]
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }

class MetricsCollector:
    """Prometheus-style metrics collection"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # System metrics
        self.cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage', registry=self.registry)
        self.memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage', registry=self.registry)
        self.disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage', registry=self.registry)
        
        # AI service metrics
        self.ollama_status = Gauge('ollama_service_status', 'Ollama service status (1=up, 0=down)', registry=self.registry)
        self.redis_status = Gauge('redis_service_status', 'Redis service status (1=up, 0=down)', registry=self.registry)
        self.postgres_status = Gauge('postgres_service_status', 'PostgreSQL service status (1=up, 0=down)', registry=self.registry)
        self.docker_status = Gauge('docker_service_status', 'Docker service status (1=up, 0=down)', registry=self.registry)
        
        # Application metrics
        self.memory_system_errors = Counter('memory_system_errors_total', 'Memory system errors', registry=self.registry)
        self.api_requests = Counter('api_requests_total', 'API requests', ['endpoint', 'status'], registry=self.registry)
        self.model_inference_time = Gauge('model_inference_seconds', 'Model inference time', ['model'], registry=self.registry)
        
    def update_system_metrics(self):
        """Update system resource metrics"""
        self.cpu_usage.set(psutil.cpu_percent())
        self.memory_usage.set(psutil.virtual_memory().percent)
        self.disk_usage.set(psutil.disk_usage('/').percent)
    
    def check_service_status(self, service_name: str, port: int = None, path: str = None) -> bool:
        """Check if a service is running"""
        if port:
            try:
                response = requests.get(f"http://localhost:{port}{path or '/'}", timeout=5)
                return response.status_code < 500
            except:
                return False
        else:
            # Check if process is running
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if service_name.lower() in ' '.join(proc.info['cmdline'] or []).lower():
                        return True
                except:
                    continue
            return False

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.alerts_key = "system_alerts"
        self.alert_history_key = "alert_history"
        
        # Configuration
        self.smtp_config = {
            'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('ALERT_FROM_EMAIL'),
            'to_emails': os.getenv('ALERT_TO_EMAILS', '').split(',')
        }
        
        self.webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        
    def create_alert(self, severity: str, component: str, message: str, metadata: Dict = None) -> str:
        """Create a new alert"""
        alert_id = f"{component}_{int(time.time())}"
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            severity=severity,
            component=component,
            message=message,
            metadata=metadata or {}
        )
        
        # Store active alert
        self.redis.hset(self.alerts_key, alert_id, json.dumps(alert.to_dict()))
        
        # Add to history
        self.redis.lpush(self.alert_history_key, json.dumps(alert.to_dict()))
        self.redis.ltrim(self.alert_history_key, 0, 999)  # Keep last 1000 alerts
        
        # Send notifications
        self._send_notifications(alert)
        
        logger.warning(f"Alert created: [{severity}] {component} - {message}")
        return alert_id
    
    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved"""
        alert_data = self.redis.hget(self.alerts_key, alert_id)
        if alert_data:
            alert_dict = json.loads(alert_data)
            alert_dict['resolved'] = True
            alert_dict['resolved_at'] = datetime.now().isoformat()
            
            self.redis.hset(self.alerts_key, alert_id, json.dumps(alert_dict))
            logger.info(f"Alert resolved: {alert_id}")
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all active (unresolved) alerts"""
        active_alerts = []
        all_alerts = self.redis.hgetall(self.alerts_key)
        
        for alert_id, alert_data in all_alerts.items():
            alert_dict = json.loads(alert_data)
            if not alert_dict.get('resolved', False):
                active_alerts.append(alert_dict)
        
        return sorted(active_alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def _send_notifications(self, alert: Alert):
        """Send alert notifications via email and webhook"""
        asyncio.create_task(self._send_email_alert(alert))
        
        if self.webhook_url:
            asyncio.create_task(self._send_webhook_alert(alert))
    
    async def _send_email_alert(self, alert: Alert):
        """Send email notification"""
        if not all([self.smtp_config['username'], self.smtp_config['password'], 
                   self.smtp_config['from_email'], self.smtp_config['to_emails'][0]]):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = ', '.join(self.smtp_config['to_emails'])
            msg['Subject'] = f"[{alert.severity.upper()}] AI DevOps Alert: {alert.component}"
            
            body = f"""
AI DevOps System Alert

Severity: {alert.severity.upper()}
Component: {alert.component}
Time: {alert.timestamp}
Message: {alert.message}

Metadata: {json.dumps(alert.metadata, indent=2)}

Alert ID: {alert.id}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.smtp_config['from_email'], self.smtp_config['to_emails'], text)
            server.quit()
            
            logger.info(f"Email alert sent for {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send webhook notification"""
        try:
            payload = {
                'alert_id': alert.id,
                'severity': alert.severity,
                'component': alert.component,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'metadata': alert.metadata
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent for {alert.id}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

class AutoHealer:
    """Automatic healing actions for common failures"""
    
    def __init__(self, alert_manager: AlertManager, docker_client: docker.DockerClient = None):
        self.alert_manager = alert_manager
        self.docker_client = docker_client or docker.from_env()
        
        # Recovery actions registry
        self.recovery_actions = {
            'restart_service': self._restart_service,
            'restart_container': self._restart_container,
            'clear_cache': self._clear_cache,
            'cleanup_disk_space': self._cleanup_disk_space,
            'restart_ollama': self._restart_ollama,
            'restart_redis': self._restart_redis,
            'restart_postgres': self._restart_postgres
        }
    
    async def perform_healing_action(self, action_name: str, **kwargs) -> bool:
        """Execute a healing action"""
        if action_name not in self.recovery_actions:
            logger.error(f"Unknown healing action: {action_name}")
            return False
        
        try:
            logger.info(f"Performing healing action: {action_name}")
            success = await self.recovery_actions[action_name](**kwargs)
            
            if success:
                logger.info(f"Healing action successful: {action_name}")
            else:
                logger.error(f"Healing action failed: {action_name}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error in healing action {action_name}: {e}")
            return False
    
    async def _restart_service(self, service_name: str) -> bool:
        """Restart a systemd service"""
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', service_name], 
                         check=True, capture_output=True)
            await asyncio.sleep(5)  # Wait for service to start
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            return False
    
    async def _restart_container(self, container_name: str) -> bool:
        """Restart a Docker container"""
        try:
            container = self.docker_client.containers.get(container_name)
            container.restart()
            await asyncio.sleep(10)  # Wait for container to start
            return True
        except Exception as e:
            logger.error(f"Failed to restart container {container_name}: {e}")
            return False
    
    async def _clear_cache(self, cache_type: str = 'redis') -> bool:
        """Clear various caches"""
        try:
            if cache_type == 'redis':
                redis_client = redis.Redis(host='localhost', port=6379, db=0)
                redis_client.flushdb()
                logger.info("Redis cache cleared")
                return True
        except Exception as e:
            logger.error(f"Failed to clear {cache_type} cache: {e}")
            return False
    
    async def _cleanup_disk_space(self, threshold_gb: float = 1.0) -> bool:
        """Clean up disk space"""
        try:
            # Clean Docker system
            subprocess.run(['docker', 'system', 'prune', '-f'], capture_output=True)
            
            # Clean pip cache
            subprocess.run(['pip', 'cache', 'purge'], capture_output=True)
            
            # Clean system logs older than 7 days
            subprocess.run(['sudo', 'journalctl', '--vacuum-time=7d'], capture_output=True)
            
            logger.info("Disk space cleanup completed")
            return True
        except Exception as e:
            logger.error(f"Disk cleanup failed: {e}")
            return False
    
    async def _restart_ollama(self) -> bool:
        """Restart Ollama service"""
        return await self._restart_service('ollama')
    
    async def _restart_redis(self) -> bool:
        """Restart Redis service"""
        return await self._restart_service('redis-server')
    
    async def _restart_postgres(self) -> bool:
        """Restart PostgreSQL service"""
        return await self._restart_service('postgresql')

class MonitoringSystem:
    """Main monitoring and auto-healing system"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
        self.metrics = MetricsCollector()
        self.alert_manager = AlertManager(self.redis_client)
        self.auto_healer = AutoHealer(self.alert_manager)
        
        self.health_checks: List[HealthCheck] = []
        self.failure_counts = {}
        self.is_running = False
        
        # Initialize health checks
        self._setup_health_checks()
        
        # Start metrics server
        start_http_server(8000, registry=self.metrics.registry)
        logger.info("Metrics server started on port 8000")
    
    def _setup_health_checks(self):
        """Setup default health checks"""
        
        # System resource checks
        self.add_health_check(HealthCheck(
            name="cpu_usage",
            check_function=self._check_cpu_usage,
            interval_seconds=30,
            timeout_seconds=5,
            failure_threshold=3,
            recovery_action=self._handle_high_cpu
        ))
        
        self.add_health_check(HealthCheck(
            name="memory_usage",
            check_function=self._check_memory_usage,
            interval_seconds=30,
            timeout_seconds=5,
            failure_threshold=3,
            recovery_action=self._handle_high_memory
        ))
        
        self.add_health_check(HealthCheck(
            name="disk_usage",
            check_function=self._check_disk_usage,
            interval_seconds=60,
            timeout_seconds=5,
            failure_threshold=2,
            recovery_action=self._handle_high_disk_usage
        ))
        
        # Service health checks
        self.add_health_check(HealthCheck(
            name="ollama_service",
            check_function=self._check_ollama_service,
            interval_seconds=60,
            timeout_seconds=10,
            failure_threshold=2,
            recovery_action=self._handle_ollama_failure
        ))
        
        self.add_health_check(HealthCheck(
            name="redis_service",
            check_function=self._check_redis_service,
            interval_seconds=30,
            timeout_seconds=5,
            failure_threshold=2,
            recovery_action=self._handle_redis_failure
        ))
        
        self.add_health_check(HealthCheck(
            name="postgres_service",
            check_function=self._check_postgres_service,
            interval_seconds=60,
            timeout_seconds=10,
            failure_threshold=2,
            recovery_action=self._handle_postgres_failure
        ))
        
        self.add_health_check(HealthCheck(
            name="anythingllm_container",
            check_function=self._check_anythingllm_container,
            interval_seconds=60,
            timeout_seconds=10,
            failure_threshold=2,
            recovery_action=self._handle_anythingllm_failure
        ))
    
    def add_health_check(self, health_check: HealthCheck):
        """Add a custom health check"""
        self.health_checks.append(health_check)
        self.failure_counts[health_check.name] = 0
        logger.info(f"Added health check: {health_check.name}")
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.is_running = True
        logger.info("Starting monitoring system...")
        
        tasks = []
        for health_check in self.health_checks:
            task = asyncio.create_task(self._monitor_health_check(health_check))
            tasks.append(task)
        
        # Start periodic metrics collection
        metrics_task = asyncio.create_task(self._collect_metrics_loop())
        tasks.append(metrics_task)
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        finally:
            self.is_running = False
    
    async def _monitor_health_check(self, health_check: HealthCheck):
        """Monitor a single health check"""
        while self.is_running:
            try:
                start_time = time.time()
                
                # Run health check with timeout
                is_healthy = await asyncio.wait_for(
                    asyncio.to_thread(health_check.check_function),
                    timeout=health_check.timeout_seconds
                )
                
                execution_time = time.time() - start_time
                
                if is_healthy:
                    # Reset failure count on success
                    if self.failure_counts[health_check.name] > 0:
                        logger.info(f"Health check recovered: {health_check.name}")
                        self.failure_counts[health_check.name] = 0
                else:
                    # Increment failure count
                    self.failure_counts[health_check.name] += 1
                    
                    logger.warning(f"Health check failed: {health_check.name} "
                                 f"(failures: {self.failure_counts[health_check.name]})")
                    
                    # Trigger recovery if threshold reached
                    if self.failure_counts[health_check.name] >= health_check.failure_threshold:
                        await self._handle_health_check_failure(health_check)
                
            except asyncio.TimeoutError:
                logger.error(f"Health check timeout: {health_check.name}")
                self.failure_counts[health_check.name] += 1
                
                if self.failure_counts[health_check.name] >= health_check.failure_threshold:
                    await self._handle_health_check_failure(health_check)
                    
            except Exception as e:
                logger.error(f"Health check error: {health_check.name} - {e}")
                self.failure_counts[health_check.name] += 1
            
            # Wait for next check
            await asyncio.sleep(health_check.interval_seconds)
    
    async def _handle_health_check_failure(self, health_check: HealthCheck):
        """Handle health check failure"""
        if health_check.alert_on_failure:
            self.alert_manager.create_alert(
                severity="critical" if self.failure_counts[health_check.name] > 5 else "warning",
                component=health_check.name,
                message=f"Health check failed {self.failure_counts[health_check.name]} times",
                metadata=health_check.metadata
            )
        
        # Attempt recovery
        if health_check.recovery_action:
            try:
                logger.info(f"Attempting recovery for: {health_check.name}")
                success = await health_check.recovery_action()
                
                if success:
                    logger.info(f"Recovery successful for: {health_check.name}")
                    self.failure_counts[health_check.name] = 0
                else:
                    logger.error(f"Recovery failed for: {health_check.name}")
                    
            except Exception as e:
                logger.error(f"Recovery error for {health_check.name}: {e}")
    
    async def _collect_metrics_loop(self):
        """Collect system metrics periodically"""
        while self.is_running:
            try:
                self.metrics.update_system_metrics()
                
                # Update service status metrics
                self.metrics.ollama_status.set(1 if self._check_ollama_service() else 0)
                self.metrics.redis_status.set(1 if self._check_redis_service() else 0)
                self.metrics.postgres_status.set(1 if self._check_postgres_service() else 0)
                self.metrics.docker_status.set(1 if self._check_docker_service() else 0)
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
            
            await asyncio.sleep(30)  # Collect metrics every 30 seconds
    
    # Health check functions
    def _check_cpu_usage(self) -> bool:
        """Check if CPU usage is acceptable"""
        cpu_percent = psutil.cpu_percent(interval=1)
        return cpu_percent < 90.0
    
    def _check_memory_usage(self) -> bool:
        """Check if memory usage is acceptable"""
        memory_percent = psutil.virtual_memory().percent
        return memory_percent < 90.0
    
    def _check_disk_usage(self) -> bool:
        """Check if disk usage is acceptable"""
        disk_percent = psutil.disk_usage('/').percent
        return disk_percent < 85.0
    
    def _check_ollama_service(self) -> bool:
        """Check if Ollama is running"""
        return self.metrics.check_service_status('ollama', 11434, '/api/tags')
    
    def _check_redis_service(self) -> bool:
        """Check if Redis is running"""
        try:
            redis_client = redis.Redis(host='localhost', port=6379, socket_timeout=5)
            redis_client.ping()
            return True
        except:
            return False
    
    def _check_postgres_service(self) -> bool:
        """Check if PostgreSQL is running"""
        return self.metrics.check_service_status('postgres')
    
    def _check_docker_service(self) -> bool:
        """Check if Docker is running"""
        try:
            client = docker.from_env()
            client.ping()
            return True
        except:
            return False
    
    def _check_anythingllm_container(self) -> bool:
        """Check if AnythingLLM container is running"""
        try:
            client = docker.from_env()
            container = client.containers.get('anythingllm-container')
            return container.status == 'running'
        except:
            return False
    
    # Recovery action functions
    async def _handle_high_cpu(self) -> bool:
        """Handle high CPU usage"""
        logger.info("Handling high CPU usage")
        # Could implement process killing, scaling, etc.
        return True
    
    async def _handle_high_memory(self) -> bool:
        """Handle high memory usage"""
        logger.info("Handling high memory usage")
        return await self.auto_healer.perform_healing_action('clear_cache')
    
    async def _handle_high_disk_usage(self) -> bool:
        """Handle high disk usage"""
        logger.info("Handling high disk usage")
        return await self.auto_healer.perform_healing_action('cleanup_disk_space')
    
    async def _handle_ollama_failure(self) -> bool:
        """Handle Ollama service failure"""
        return await self.auto_healer.perform_healing_action('restart_ollama')
    
    async def _handle_redis_failure(self) -> bool:
        """Handle Redis service failure"""
        return await self.auto_healer.perform_healing_action('restart_redis')
    
    async def _handle_postgres_failure(self) -> bool:
        """Handle PostgreSQL service failure"""
        return await self.auto_healer.perform_healing_action('restart_postgres')
    
    async def _handle_anythingllm_failure(self) -> bool:
        """Handle AnythingLLM container failure"""
        return await self.auto_healer.perform_healing_action('restart_container', 
                                                           container_name='anythingllm-container')
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        active_alerts = self.alert_manager.get_active_alerts()
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy' if len(active_alerts) == 0 else 'degraded',
            'active_alerts_count': len(active_alerts),
            'active_alerts': active_alerts[:5],  # Show top 5 alerts
            'services': {
                'ollama': self._check_ollama_service(),
                'redis': self._check_redis_service(),
                'postgres': self._check_postgres_service(),
                'docker': self._check_docker_service(),
                'anythingllm': self._check_anythingllm_container()
            },
            'resources': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            },
            'failure_counts': self.failure_counts.copy()
        }
        
        return status

# Example usage and CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        # Quick status check
        monitoring = MonitoringSystem()
        status = monitoring.get_system_status()
        print(json.dumps(status, indent=2))
    else:
        # Start monitoring daemon
        monitoring = MonitoringSystem()
        try:
            asyncio.run(monitoring.start_monitoring())
        except KeyboardInterrupt:
            logger.info("Monitoring system stopped")