#!/usr/bin/env python3
"""
AI Agent: System Monitor
Continuously monitors all BrainOps systems and performs auto-healing
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SystemMonitor")

class SystemMonitorAgent:
    """AI Agent for monitoring and auto-healing BrainOps systems"""
    
    def __init__(self):
        self.name = "SystemMonitor"
        self.role = "Monitor system health and auto-heal"
        self.capabilities = [
            "health_check",
            "error_detection", 
            "auto_recovery",
            "alert_escalation",
            "performance_monitoring"
        ]
        
        # System endpoints
        self.systems = {
            "backend_api": {
                "url": "https://brainops-backend-prod.onrender.com/api/v1/health",
                "critical": True,
                "timeout": 10
            },
            "myroofgenius": {
                "url": "https://myroofgenius.com",
                "critical": True,
                "timeout": 10
            },
            "weathercraft_erp": {
                "url": "https://weathercraft-erp.vercel.app",
                "critical": False,
                "timeout": 10
            },
            "task_os": {
                "url": "https://brainops-task-os.vercel.app",
                "critical": False,
                "timeout": 10
            }
        }
        
        # Database connection
        self.db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
        )
        
        # Health history
        self.health_history = {}
        self.failure_counts = {}
        
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    async def check_system_health(self, name: str, config: Dict) -> Dict:
        """Check health of a single system"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    config["url"],
                    timeout=aiohttp.ClientTimeout(total=config["timeout"])
                ) as response:
                    if response.status == 200:
                        return {
                            "system": name,
                            "status": "healthy",
                            "response_time": config["timeout"],
                            "status_code": response.status
                        }
                    else:
                        return {
                            "system": name,
                            "status": "unhealthy",
                            "status_code": response.status,
                            "error": f"HTTP {response.status}"
                        }
        except asyncio.TimeoutError:
            return {
                "system": name,
                "status": "unhealthy",
                "error": "Timeout"
            }
        except Exception as e:
            return {
                "system": name,
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_database_health(self) -> Dict:
        """Check database connectivity and status"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check connection
            cur.execute("SELECT 1")
            
            # Get table count
            cur.execute("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = cur.fetchone()['table_count']
            
            # Get recent activity
            cur.execute("""
                SELECT COUNT(*) as recent_activity
                FROM persistent_memory
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """)
            recent_activity = cur.fetchone()['recent_activity']
            
            cur.close()
            conn.close()
            
            return {
                "system": "database",
                "status": "healthy",
                "table_count": table_count,
                "recent_activity": recent_activity
            }
        except Exception as e:
            return {
                "system": "database",
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def attempt_recovery(self, system: str, error: str) -> bool:
        """Attempt to auto-heal a failing system"""
        logger.warning(f"Attempting recovery for {system}: {error}")
        
        recovery_actions = {
            "backend_api": self.recover_backend,
            "database": self.recover_database,
            "myroofgenius": self.recover_frontend,
            "weathercraft_erp": self.recover_frontend,
            "task_os": self.recover_frontend
        }
        
        if system in recovery_actions:
            return await recovery_actions[system](error)
        return False
    
    async def recover_backend(self, error: str) -> bool:
        """Attempt to recover backend API"""
        try:
            # Try to trigger Render deploy hook
            deploy_hook = "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"
            async with aiohttp.ClientSession() as session:
                async with session.post(deploy_hook) as response:
                    if response.status == 200:
                        logger.info("Backend redeploy triggered successfully")
                        return True
        except Exception as e:
            logger.error(f"Backend recovery failed: {e}")
        return False
    
    async def recover_database(self, error: str) -> bool:
        """Attempt to recover database issues"""
        try:
            # Run database sync script
            result = subprocess.run(
                ["python3", "/home/mwwoodworth/code/scripts/python/ROBUST_DB_SYNC_SYSTEM.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.info("Database sync completed successfully")
                return True
        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
        return False
    
    async def recover_frontend(self, error: str) -> bool:
        """Attempt to recover frontend applications"""
        # Frontend apps on Vercel usually self-heal
        # Just log for now
        logger.info(f"Frontend issue logged, Vercel should auto-recover")
        return True
    
    async def save_to_memory(self, data: Dict):
        """Save monitoring data to persistent memory"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO persistent_memory 
                (type, key, value, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """, (
                'system_health',
                f'health_check_{datetime.now().isoformat()}',
                json.dumps(data),
                json.dumps({"agent": self.name})
            ))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save to memory: {e}")
    
    async def escalate_critical_issue(self, system: str, error: str):
        """Escalate critical issues that can't be auto-healed"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": "CRITICAL",
            "system": system,
            "error": error,
            "message": f"CRITICAL: {system} is down and auto-recovery failed",
            "agent": self.name
        }
        
        # Save to database for review
        await self.save_to_memory(alert)
        
        # Log critical alert
        logger.critical(f"ESCALATION: {alert['message']}")
        
        # TODO: Send notification (email, Slack, etc.)
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Starting {self.name} agent...")
        
        while True:
            try:
                # Check all systems
                results = []
                
                # Check web systems
                for name, config in self.systems.items():
                    result = await self.check_system_health(name, config)
                    results.append(result)
                    
                    # Track failures
                    if result["status"] == "unhealthy":
                        self.failure_counts[name] = self.failure_counts.get(name, 0) + 1
                        
                        # Attempt recovery after 3 failures
                        if self.failure_counts[name] >= 3:
                            recovered = await self.attempt_recovery(name, result.get("error", "Unknown"))
                            if recovered:
                                self.failure_counts[name] = 0
                            elif config.get("critical"):
                                await self.escalate_critical_issue(name, result.get("error", "Unknown"))
                    else:
                        self.failure_counts[name] = 0
                
                # Check database
                db_result = await self.check_database_health()
                results.append(db_result)
                
                # Calculate overall health
                healthy_count = sum(1 for r in results if r["status"] == "healthy")
                total_count = len(results)
                health_percentage = (healthy_count / total_count) * 100
                
                # Create health report
                health_report = {
                    "timestamp": datetime.now().isoformat(),
                    "total_systems": total_count,
                    "healthy_systems": healthy_count,
                    "unhealthy_systems": total_count - healthy_count,
                    "health_percentage": health_percentage,
                    "systems": {r["system"]: r for r in results}
                }
                
                # Save to memory
                await self.save_to_memory(health_report)
                
                # Log status
                if health_percentage == 100:
                    logger.info(f"✅ All systems healthy ({healthy_count}/{total_count})")
                elif health_percentage >= 80:
                    logger.warning(f"⚠️ System health at {health_percentage:.1f}% ({healthy_count}/{total_count})")
                else:
                    logger.error(f"❌ Critical: System health at {health_percentage:.1f}% ({healthy_count}/{total_count})")
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the agent"""
        logger.info(f"""
        ========================================
        🤖 AI Agent: {self.name}
        Role: {self.role}
        Capabilities: {', '.join(self.capabilities)}
        ========================================
        """)
        
        # Start monitoring
        await self.monitor_loop()

async def main():
    """Main entry point"""
    agent = SystemMonitorAgent()
    await agent.start()

if __name__ == "__main__":
    # Run the agent
    asyncio.run(main())