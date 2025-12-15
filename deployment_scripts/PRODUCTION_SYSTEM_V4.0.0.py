#!/usr/bin/env python3
"""
PRODUCTION SYSTEM V4.0.0 - Enterprise Grade with AI Self-Healing
================================================================
Complete production system with OS-level logging, LangGraph orchestration,
and continuous learning/improvement capabilities.
"""

import os
import sys
import json
import asyncio
import logging
import psutil
import signal
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import requests
import aiohttp
import asyncpg
from pathlib import Path
import yaml
import hashlib
import socket
import platform

# LangGraph imports for orchestration
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint import MemorySaver
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("WARNING: LangGraph not installed. AI orchestration limited.")

# Configure structured OS-level logging
LOG_DIR = Path("/var/log/brainops")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Setup multiple log handlers for different severity levels
class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': os.getpid(),
            'thread_id': record.thread,
            'hostname': socket.gethostname(),
            'system': platform.system(),
            'python_version': platform.python_version()
        }
        
        if hasattr(record, 'extra_data'):
            log_obj['data'] = record.extra_data
            
        if record.exc_info:
            log_obj['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_obj)

# Configure logging
def setup_logging():
    """Setup comprehensive logging system"""
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler for INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler for all logs (JSON structured)
    file_handler = logging.FileHandler(
        LOG_DIR / f"production_{datetime.now().strftime('%Y%m%d')}.json"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter())
    
    # Error file handler
    error_handler = logging.FileHandler(
        LOG_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.json"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Syslog handler for OS-level integration
    try:
        from logging.handlers import SysLogHandler
        syslog = SysLogHandler(address='/dev/log')
        syslog.setFormatter(logging.Formatter(
            'BrainOps[%(process)d]: %(levelname)s %(message)s'
        ))
        root_logger.addHandler(syslog)
    except Exception as e:
        print(f"Syslog not available: {e}")
    
    return root_logger

logger = setup_logging()

# System Configuration
@dataclass
class SystemConfig:
    """Central configuration for all systems"""
    
    # Database
    db_host: str = "db.yomagoqdmxszqtdwuhab.supabase.co"
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str = "postgres"
    db_password: str = "<DB_PASSWORD_REDACTED>"
    
    # APIs
    backend_url: str = "https://brainops-backend-prod.onrender.com"
    frontend_url: str = "https://myroofgenius.com"
    weathercraft_url: str = "https://weathercraft-app.vercel.app"
    weathercraft_erp_url: str = "https://weathercraft-erp.vercel.app"
    aios_url: str = "https://brainops-aios-ops.vercel.app"
    
    # Supabase
    supabase_url: str = "https://yomagoqdmxszqtdwuhab.supabase.co"
    supabase_key: str = "<JWT_REDACTED>"
    
    # Monitoring
    check_interval: int = 300  # 5 minutes
    alert_threshold: int = 3   # Failures before alert
    auto_heal: bool = True
    learning_enabled: bool = True
    
    # Performance
    max_workers: int = 10
    timeout: int = 30
    retry_count: int = 3
    
class ServiceStatus(Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """Health check result"""
    service: str
    status: ServiceStatus
    response_time: float
    details: Dict[str, Any]
    timestamp: datetime
    
class SystemMonitor:
    """Core system monitoring with AI learning"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.health_history: List[HealthCheck] = []
        self.incident_history: List[Dict] = []
        self.learning_data: Dict[str, Any] = {}
        self.db_pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize monitoring systems"""
        logger.info("Initializing System Monitor")
        
        # Create database connection pool
        try:
            self.db_pool = await asyncpg.create_pool(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            
    async def check_service_health(self, service_name: str, url: str) -> HealthCheck:
        """Check health of a specific service"""
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.status == 200:
                        status = ServiceStatus.HEALTHY
                    elif response.status < 500:
                        status = ServiceStatus.DEGRADED
                    else:
                        status = ServiceStatus.CRITICAL
                        
                    return HealthCheck(
                        service=service_name,
                        status=status,
                        response_time=response_time,
                        details={
                            'status_code': response.status,
                            'url': url,
                            'headers': dict(response.headers)
                        },
                        timestamp=datetime.now()
                    )
        except asyncio.TimeoutError:
            return HealthCheck(
                service=service_name,
                status=ServiceStatus.CRITICAL,
                response_time=self.config.timeout,
                details={'error': 'Timeout', 'url': url},
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheck(
                service=service_name,
                status=ServiceStatus.UNKNOWN,
                response_time=(datetime.now() - start_time).total_seconds(),
                details={'error': str(e), 'url': url},
                timestamp=datetime.now()
            )
            
    async def check_all_services(self) -> List[HealthCheck]:
        """Check all configured services"""
        services = [
            ("Backend API", f"{self.config.backend_url}/api/v1/health"),
            ("Frontend", self.config.frontend_url),
            ("WeatherCraft App", self.config.weathercraft_url),
            ("WeatherCraft ERP", self.config.weathercraft_erp_url),
            ("BrainOps AIOS", self.config.aios_url),
            ("Database", "database_check")
        ]
        
        tasks = []
        for service_name, url in services:
            if service_name == "Database":
                tasks.append(self.check_database_health())
            else:
                tasks.append(self.check_service_health(service_name, url))
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_checks = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Health check failed: {result}")
            else:
                health_checks.append(result)
                self.health_history.append(result)
                
        return health_checks
        
    async def check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance"""
        start_time = datetime.now()
        
        try:
            if not self.db_pool:
                await self.initialize()
                
            async with self.db_pool.acquire() as conn:
                # Simple query to test connection
                result = await conn.fetchval("SELECT COUNT(*) FROM pg_stat_activity")
                response_time = (datetime.now() - start_time).total_seconds()
                
                return HealthCheck(
                    service="Database",
                    status=ServiceStatus.HEALTHY,
                    response_time=response_time,
                    details={
                        'active_connections': result,
                        'pool_size': self.db_pool.get_size() if self.db_pool else 0
                    },
                    timestamp=datetime.now()
                )
        except Exception as e:
            return HealthCheck(
                service="Database",
                status=ServiceStatus.CRITICAL,
                response_time=(datetime.now() - start_time).total_seconds(),
                details={'error': str(e)},
                timestamp=datetime.now()
            )
            
    async def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze health patterns for learning"""
        if len(self.health_history) < 10:
            return {}
            
        analysis = {
            'services': {},
            'trends': [],
            'recommendations': []
        }
        
        # Group by service
        service_groups = {}
        for check in self.health_history[-100:]:  # Last 100 checks
            if check.service not in service_groups:
                service_groups[check.service] = []
            service_groups[check.service].append(check)
            
        # Analyze each service
        for service, checks in service_groups.items():
            healthy = sum(1 for c in checks if c.status == ServiceStatus.HEALTHY)
            total = len(checks)
            avg_response = sum(c.response_time for c in checks) / total
            
            analysis['services'][service] = {
                'health_rate': healthy / total,
                'avg_response_time': avg_response,
                'status': 'stable' if healthy/total > 0.95 else 'unstable'
            }
            
            # Generate recommendations
            if healthy/total < 0.95:
                analysis['recommendations'].append(
                    f"Service {service} showing instability ({healthy}/{total} healthy). Consider scaling or investigation."
                )
                
            if avg_response > 2.0:
                analysis['recommendations'].append(
                    f"Service {service} has high response time ({avg_response:.2f}s). Performance optimization needed."
                )
                
        return analysis

class SelfHealingEngine:
    """Autonomous self-healing system"""
    
    def __init__(self, config: SystemConfig, monitor: SystemMonitor):
        self.config = config
        self.monitor = monitor
        self.healing_actions: List[Dict] = []
        
    async def diagnose_issue(self, health_check: HealthCheck) -> Dict[str, Any]:
        """Diagnose the root cause of an issue"""
        diagnosis = {
            'service': health_check.service,
            'status': health_check.status.value,
            'possible_causes': [],
            'recommended_actions': []
        }
        
        if health_check.status == ServiceStatus.CRITICAL:
            if 'Timeout' in str(health_check.details.get('error', '')):
                diagnosis['possible_causes'].append('Network connectivity issue')
                diagnosis['possible_causes'].append('Service overload')
                diagnosis['recommended_actions'].append('restart_service')
                diagnosis['recommended_actions'].append('scale_service')
                
            elif 'status_code' in health_check.details:
                status_code = health_check.details['status_code']
                if status_code >= 500:
                    diagnosis['possible_causes'].append('Server error')
                    diagnosis['recommended_actions'].append('check_logs')
                    diagnosis['recommended_actions'].append('restart_service')
                elif status_code == 404:
                    diagnosis['possible_causes'].append('Deployment issue')
                    diagnosis['recommended_actions'].append('redeploy_service')
                    
        return diagnosis
        
    async def execute_healing(self, diagnosis: Dict[str, Any]) -> bool:
        """Execute healing actions based on diagnosis"""
        if not self.config.auto_heal:
            logger.info(f"Auto-heal disabled. Would execute: {diagnosis}")
            return False
            
        success = False
        service = diagnosis['service']
        
        for action in diagnosis['recommended_actions']:
            logger.info(f"Executing healing action: {action} for {service}")
            
            try:
                if action == 'restart_service':
                    success = await self.restart_service(service)
                elif action == 'redeploy_service':
                    success = await self.redeploy_service(service)
                elif action == 'scale_service':
                    success = await self.scale_service(service)
                elif action == 'check_logs':
                    await self.analyze_service_logs(service)
                    
                if success:
                    self.healing_actions.append({
                        'timestamp': datetime.now().isoformat(),
                        'service': service,
                        'action': action,
                        'success': success,
                        'diagnosis': diagnosis
                    })
                    break
                    
            except Exception as e:
                logger.error(f"Healing action {action} failed: {e}")
                
        return success
        
    async def restart_service(self, service: str) -> bool:
        """Restart a service"""
        restart_commands = {
            'Backend API': 'curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM',
            'Frontend': 'cd /home/mwwoodworth/code/myroofgenius-app && git push origin main',
            'WeatherCraft App': 'cd /home/mwwoodworth/code/weathercraft-app && vercel --prod',
        }
        
        if service in restart_commands:
            try:
                result = subprocess.run(
                    restart_commands[service],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return result.returncode == 0
            except Exception as e:
                logger.error(f"Failed to restart {service}: {e}")
                
        return False
        
    async def redeploy_service(self, service: str) -> bool:
        """Redeploy a service"""
        logger.info(f"Redeploying {service}")
        
        deploy_scripts = {
            'Backend API': '/home/mwwoodworth/code/DEPLOY_COMPLETE_SYSTEM_V3.1.222.sh',
            'Frontend': '/home/mwwoodworth/code/EMERGENCY_FRONTEND_DEPLOYMENT.sh',
            'WeatherCraft App': 'cd /home/mwwoodworth/code/weathercraft-app && npm run build && vercel --prod'
        }
        
        if service in deploy_scripts:
            try:
                result = subprocess.run(
                    deploy_scripts[service],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                return result.returncode == 0
            except Exception as e:
                logger.error(f"Failed to redeploy {service}: {e}")
                
        return False
        
    async def scale_service(self, service: str) -> bool:
        """Scale a service up"""
        logger.info(f"Scaling {service}")
        # Implement scaling logic based on service type
        return False
        
    async def analyze_service_logs(self, service: str):
        """Analyze service logs for issues"""
        logger.info(f"Analyzing logs for {service}")
        
        # Implement log analysis
        log_commands = {
            'Backend API': 'curl -s https://brainops-backend-prod.onrender.com/api/v1/events | tail -50',
            'Database': "psql -h db.yomagoqdmxszqtdwuhab.supabase.co -U postgres -d postgres -c 'SELECT * FROM pg_stat_activity'"
        }
        
        if service in log_commands:
            try:
                result = subprocess.run(
                    log_commands[service],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env={**os.environ, 'PGPASSWORD': self.config.db_password}
                )
                
                if result.stdout:
                    # Analyze logs for patterns
                    error_keywords = ['ERROR', 'FATAL', 'CRITICAL', 'Exception']
                    for keyword in error_keywords:
                        if keyword in result.stdout:
                            logger.warning(f"Found {keyword} in {service} logs")
                            
            except Exception as e:
                logger.error(f"Failed to analyze logs for {service}: {e}")

class LangGraphOrchestrator:
    """AI orchestration using LangGraph"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.memory = MemorySaver() if LANGGRAPH_AVAILABLE else None
        self.graph = self.build_graph() if LANGGRAPH_AVAILABLE else None
        
    def build_graph(self):
        """Build the LangGraph workflow"""
        if not LANGGRAPH_AVAILABLE:
            return None
            
        # Define the graph state
        from typing import TypedDict
        
        class SystemState(TypedDict):
            health_checks: List[Dict]
            diagnosis: Dict
            actions_taken: List[str]
            outcome: str
            
        # Create the graph
        workflow = StateGraph(SystemState)
        
        # Add nodes
        workflow.add_node("monitor", self.monitor_node)
        workflow.add_node("diagnose", self.diagnose_node)
        workflow.add_node("heal", self.heal_node)
        workflow.add_node("verify", self.verify_node)
        workflow.add_node("learn", self.learn_node)
        
        # Add edges
        workflow.add_edge("monitor", "diagnose")
        workflow.add_edge("diagnose", "heal")
        workflow.add_edge("heal", "verify")
        workflow.add_edge("verify", "learn")
        workflow.add_edge("learn", END)
        
        # Set entry point
        workflow.set_entry_point("monitor")
        
        return workflow.compile(checkpointer=self.memory)
        
    async def monitor_node(self, state: Dict) -> Dict:
        """Monitor system health"""
        monitor = SystemMonitor(self.config)
        await monitor.initialize()
        
        health_checks = await monitor.check_all_services()
        
        return {
            **state,
            'health_checks': [asdict(hc) for hc in health_checks]
        }
        
    async def diagnose_node(self, state: Dict) -> Dict:
        """Diagnose issues from health checks"""
        issues = []
        
        for check in state['health_checks']:
            if check['status'] != 'healthy':
                issues.append({
                    'service': check['service'],
                    'status': check['status'],
                    'details': check['details']
                })
                
        return {
            **state,
            'diagnosis': {'issues': issues}
        }
        
    async def heal_node(self, state: Dict) -> Dict:
        """Execute healing actions"""
        actions = []
        
        if state['diagnosis'].get('issues'):
            monitor = SystemMonitor(self.config)
            healer = SelfHealingEngine(self.config, monitor)
            
            for issue in state['diagnosis']['issues']:
                # Create health check from issue
                health_check = HealthCheck(
                    service=issue['service'],
                    status=ServiceStatus[issue['status'].upper()],
                    response_time=0,
                    details=issue['details'],
                    timestamp=datetime.now()
                )
                
                diagnosis = await healer.diagnose_issue(health_check)
                success = await healer.execute_healing(diagnosis)
                
                actions.append({
                    'service': issue['service'],
                    'actions': diagnosis['recommended_actions'],
                    'success': success
                })
                
        return {
            **state,
            'actions_taken': actions
        }
        
    async def verify_node(self, state: Dict) -> Dict:
        """Verify healing actions were successful"""
        monitor = SystemMonitor(self.config)
        await monitor.initialize()
        
        # Re-check services that had issues
        if state.get('actions_taken'):
            await asyncio.sleep(30)  # Wait for services to stabilize
            
            health_checks = await monitor.check_all_services()
            all_healthy = all(
                hc.status == ServiceStatus.HEALTHY 
                for hc in health_checks
            )
            
            outcome = 'success' if all_healthy else 'partial'
        else:
            outcome = 'no_action_needed'
            
        return {
            **state,
            'outcome': outcome
        }
        
    async def learn_node(self, state: Dict) -> Dict:
        """Learn from the experience"""
        # Store the experience for future learning
        experience = {
            'timestamp': datetime.now().isoformat(),
            'health_checks': state['health_checks'],
            'diagnosis': state['diagnosis'],
            'actions_taken': state.get('actions_taken', []),
            'outcome': state.get('outcome', 'unknown')
        }
        
        # Save to persistent storage
        await self.save_experience(experience)
        
        # Analyze patterns
        monitor = SystemMonitor(self.config)
        patterns = await monitor.analyze_patterns()
        
        if patterns.get('recommendations'):
            logger.info(f"Learning insights: {patterns['recommendations']}")
            
        return state
        
    async def save_experience(self, experience: Dict):
        """Save learning experience to database"""
        try:
            conn_str = f"postgresql://{self.config.db_user}:<DB_PASSWORD_REDACTED>@{self.config.db_host}/{self.config.db_name}"
            
            async with asyncpg.connect(conn_str) as conn:
                await conn.execute("""
                    INSERT INTO system_learning_log 
                    (timestamp, experience_data, outcome)
                    VALUES ($1, $2, $3)
                """, 
                datetime.now(), 
                json.dumps(experience),
                experience.get('outcome', 'unknown')
                )
        except Exception as e:
            logger.error(f"Failed to save learning experience: {e}")
            
    async def run_orchestration(self):
        """Run the complete orchestration workflow"""
        if not self.graph:
            logger.warning("LangGraph not available, running basic monitoring")
            monitor = SystemMonitor(self.config)
            await monitor.initialize()
            health_checks = await monitor.check_all_services()
            
            for check in health_checks:
                if check.status != ServiceStatus.HEALTHY:
                    logger.warning(f"{check.service}: {check.status.value}")
                    
            return
            
        # Run the graph
        initial_state = {
            'health_checks': [],
            'diagnosis': {},
            'actions_taken': [],
            'outcome': ''
        }
        
        result = await self.graph.ainvoke(initial_state)
        logger.info(f"Orchestration complete: {result['outcome']}")

class ProductionSystemManager:
    """Main production system manager"""
    
    def __init__(self):
        self.config = SystemConfig()
        self.monitor = SystemMonitor(self.config)
        self.healer = SelfHealingEngine(self.config, self.monitor)
        self.orchestrator = LangGraphOrchestrator(self.config)
        self.running = False
        
    async def start(self):
        """Start the production system"""
        logger.info("Starting Production System V4.0.0")
        
        self.running = True
        
        # Initialize components
        await self.monitor.initialize()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        # Main monitoring loop
        while self.running:
            try:
                # Run orchestration
                await self.orchestrator.run_orchestration()
                
                # Get system metrics
                metrics = self.get_system_metrics()
                logger.info(f"System metrics: {metrics}")
                
                # Check for critical issues
                health_checks = await self.monitor.check_all_services()
                critical_count = sum(
                    1 for hc in health_checks 
                    if hc.status == ServiceStatus.CRITICAL
                )
                
                if critical_count > 0:
                    logger.critical(f"{critical_count} services in critical state!")
                    
                    # Attempt healing
                    for check in health_checks:
                        if check.status == ServiceStatus.CRITICAL:
                            diagnosis = await self.healer.diagnose_issue(check)
                            await self.healer.execute_healing(diagnosis)
                            
                # Analyze patterns periodically
                patterns = await self.monitor.analyze_patterns()
                if patterns.get('recommendations'):
                    for rec in patterns['recommendations']:
                        logger.info(f"Recommendation: {rec}")
                        
                # Wait before next check
                await asyncio.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retry
                
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections()),
            'process_count': len(psutil.pids()),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
    def shutdown(self, signum, frame):
        """Graceful shutdown"""
        logger.info("Shutting down Production System")
        self.running = False
        
        # Cleanup
        if self.monitor.db_pool:
            asyncio.create_task(self.monitor.db_pool.close())
            
        sys.exit(0)

async def main():
    """Main entry point"""
    manager = ProductionSystemManager()
    
    try:
        await manager.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Ensure running as appropriate user
    if os.geteuid() != 0 and not os.access('/var/log', os.W_OK):
        logger.warning("Not running as root, log access may be limited")
        
    # Create necessary directories
    Path("/var/log/brainops").mkdir(parents=True, exist_ok=True)
    Path("/var/run/brainops").mkdir(parents=True, exist_ok=True)
    
    # Write PID file
    with open("/var/run/brainops/production.pid", "w") as f:
        f.write(str(os.getpid()))
        
    # Run the system
    asyncio.run(main())