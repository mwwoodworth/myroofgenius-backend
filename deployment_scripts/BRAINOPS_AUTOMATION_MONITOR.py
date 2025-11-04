#!/usr/bin/env python3
"""
BrainOps Comprehensive Automation Monitor
Integrates and monitors all automation systems:
- AUREA QC
- LangGraph Orchestration
- Perplexity Audit System
- Claude Workflows
- Real-time Dashboard Updates
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import traceback
import os

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ"

# Ensure log directory exists
LOG_DIR = Path("/home/mwwoodworth/code/logs")
LOG_DIR.mkdir(exist_ok=True)

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "automation_monitor.log"),
        logging.FileHandler(LOG_DIR / "automation_errors.log", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BRAINOPS-AUTOMATION")


class BrainOpsAutomationMonitor:
    """Central monitoring system for all BrainOps automations"""
    
    def __init__(self):
        self.session = None
        self.automation_status = {
            "aurea_qc": {"status": "unknown", "last_check": None, "health": 0},
            "langgraph": {"status": "unknown", "last_check": None, "active_workflows": 0},
            "perplexity": {"status": "unknown", "last_check": None, "audits_performed": 0},
            "claude_workflows": {"status": "unknown", "last_check": None, "tasks_completed": 0},
            "memory_system": {"status": "unknown", "last_check": None, "entries": 0},
            "dashboard": {"status": "unknown", "last_check": None, "real_time": False}
        }
        self.metrics = {
            "total_checks": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "auto_recoveries": 0,
            "alerts_sent": 0
        }
        self.error_log = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def check_aurea_qc(self) -> Dict[str, Any]:
        """Monitor AUREA QC system health"""
        status = {"operational": False, "details": {}}
        
        try:
            # Check if AUREA QC process is running
            result = subprocess.run(
                ["pgrep", "-f", "AUREA_CLAUDEOS_QC_SYSTEM"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                status["operational"] = True
                status["details"]["process_id"] = result.stdout.strip()
                
                # Check AUREA health endpoint
                async with self.session.get(f"{BACKEND_URL}/api/v1/aurea/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        status["details"]["api_health"] = data
                    else:
                        status["details"]["api_status"] = resp.status
                        
            # Check recent logs
            log_path = Path("/tmp/aurea_qc_v2.log")
            if log_path.exists():
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    recent_logs = lines[-10:] if len(lines) > 10 else lines
                    status["details"]["recent_activity"] = len(recent_logs)
                    
        except Exception as e:
            status["error"] = str(e)
            logger.error(f"AUREA QC check failed: {e}")
            
        self.automation_status["aurea_qc"]["status"] = "operational" if status["operational"] else "down"
        self.automation_status["aurea_qc"]["last_check"] = datetime.now(timezone.utc).isoformat()
        self.automation_status["aurea_qc"]["health"] = 100 if status["operational"] else 0
        
        return status
        
    async def check_langgraph(self) -> Dict[str, Any]:
        """Monitor LangGraph orchestration system"""
        status = {"operational": False, "workflows": [], "details": {}}
        
        try:
            # Check LangGraph status endpoint
            async with self.session.get(f"{BACKEND_URL}/api/v1/langgraphos/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status["operational"] = True
                    status["workflows"] = data.get("active_workflows", [])
                    status["details"] = data
                elif resp.status == 404:
                    # LangGraph not configured yet
                    status["details"]["message"] = "LangGraph endpoints not deployed"
                    
            # Check for active workflows
            async with self.session.get(f"{BACKEND_URL}/api/v1/langgraphos/workflows") as resp:
                if resp.status == 200:
                    workflows = await resp.json()
                    status["details"]["total_workflows"] = len(workflows)
                    status["details"]["active"] = sum(1 for w in workflows if w.get("status") == "active")
                    
        except Exception as e:
            status["error"] = str(e)
            logger.error(f"LangGraph check failed: {e}")
            
        self.automation_status["langgraph"]["status"] = "operational" if status["operational"] else "not_configured"
        self.automation_status["langgraph"]["last_check"] = datetime.now(timezone.utc).isoformat()
        self.automation_status["langgraph"]["active_workflows"] = status["details"].get("active", 0)
        
        return status
        
    async def check_perplexity_audit(self) -> Dict[str, Any]:
        """Monitor Perplexity audit system"""
        status = {"operational": False, "audits": [], "details": {}}
        
        try:
            # Check Perplexity integration
            async with self.session.get(f"{BACKEND_URL}/api/v1/perplexity/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status["operational"] = True
                    status["details"] = data
                elif resp.status == 404:
                    status["details"]["message"] = "Perplexity integration not configured"
                    
            # Query recent audits from memory
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            
            params = {
                "select": "title,content,created_at",
                "memory_type": "eq.perplexity_audit",
                "created_at": f"gte.{(datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}",
                "order": "created_at.desc",
                "limit": "10"
            }
            
            async with self.session.get(
                f"{SUPABASE_URL}/rest/v1/copilot_messages",
                headers=headers,
                params=params
            ) as resp:
                if resp.status == 200:
                    audits = await resp.json()
                    status["audits"] = audits
                    status["details"]["recent_audits"] = len(audits)
                    
        except Exception as e:
            status["error"] = str(e)
            logger.error(f"Perplexity audit check failed: {e}")
            
        self.automation_status["perplexity"]["status"] = "operational" if status["operational"] else "not_configured"
        self.automation_status["perplexity"]["last_check"] = datetime.now(timezone.utc).isoformat()
        self.automation_status["perplexity"]["audits_performed"] = status["details"].get("recent_audits", 0)
        
        return status
        
    async def check_claude_workflows(self) -> Dict[str, Any]:
        """Monitor Claude workflow automation"""
        status = {"operational": False, "workflows": [], "details": {}}
        
        try:
            # Check Claude integration status
            async with self.session.get(f"{BACKEND_URL}/api/v1/claude/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status["operational"] = True
                    status["details"] = data
                    
            # Check active Claude workflows
            async with self.session.get(f"{BACKEND_URL}/api/v1/claude/workflows") as resp:
                if resp.status == 200:
                    workflows = await resp.json()
                    status["workflows"] = workflows
                    status["details"]["total_workflows"] = len(workflows)
                    status["details"]["completed_today"] = sum(
                        1 for w in workflows 
                        if w.get("status") == "completed" and 
                        w.get("completed_at", "").startswith(datetime.now(timezone.utc).date().isoformat())
                    )
                    
        except Exception as e:
            status["error"] = str(e)
            logger.error(f"Claude workflows check failed: {e}")
            
        self.automation_status["claude_workflows"]["status"] = "operational" if status["operational"] else "degraded"
        self.automation_status["claude_workflows"]["last_check"] = datetime.now(timezone.utc).isoformat()
        self.automation_status["claude_workflows"]["tasks_completed"] = status["details"].get("completed_today", 0)
        
        return status
        
    async def check_memory_system(self) -> Dict[str, Any]:
        """Monitor persistent memory system"""
        status = {"operational": False, "stats": {}, "details": {}}
        
        try:
            # Check memory system health
            async with self.session.get(f"{BACKEND_URL}/api/v1/memory/status") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status["operational"] = True
                    status["stats"] = data.get("statistics", {})
                    
            # Get memory entry count
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Prefer": "count=exact"
            }
            
            async with self.session.head(
                f"{SUPABASE_URL}/rest/v1/copilot_messages",
                headers=headers
            ) as resp:
                if resp.status == 200:
                    count = resp.headers.get("content-range", "0-0/0").split("/")[-1]
                    status["details"]["total_entries"] = int(count)
                    
        except Exception as e:
            status["error"] = str(e)
            logger.error(f"Memory system check failed: {e}")
            
        self.automation_status["memory_system"]["status"] = "operational" if status["operational"] else "degraded"
        self.automation_status["memory_system"]["last_check"] = datetime.now(timezone.utc).isoformat()
        self.automation_status["memory_system"]["entries"] = status["details"].get("total_entries", 0)
        
        return status
        
    async def update_dashboard_data(self) -> bool:
        """Push real-time data to dashboard"""
        try:
            # Prepare dashboard data
            dashboard_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "automations": self.automation_status,
                "metrics": self.metrics,
                "alerts": self.get_active_alerts(),
                "health_score": self.calculate_health_score()
            }
            
            # Store in memory for dashboard access
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            memory_entry = {
                "title": "Dashboard Real-Time Data",
                "content": json.dumps(dashboard_data, indent=2),
                "role": "system",
                "memory_type": "dashboard_data",
                "meta_data": {
                    "component": "automation_monitor",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "health_score": dashboard_data["health_score"]
                },
                "is_active": True,
                "is_pinned": True
            }
            
            async with self.session.post(
                f"{SUPABASE_URL}/rest/v1/copilot_messages",
                headers=headers,
                json=memory_entry
            ) as resp:
                if resp.status in [200, 201]:
                    logger.info("✅ Dashboard data updated")
                    return True
                else:
                    logger.error(f"Failed to update dashboard: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Dashboard update error: {e}")
            
        return False
        
    def calculate_health_score(self) -> float:
        """Calculate overall system health score"""
        operational_count = sum(
            1 for system in self.automation_status.values()
            if system["status"] == "operational"
        )
        total_systems = len(self.automation_status)
        
        base_score = (operational_count / total_systems) * 100 if total_systems > 0 else 0
        
        # Adjust for error rate
        error_rate = self.metrics["failed_operations"] / max(self.metrics["total_checks"], 1)
        adjusted_score = base_score * (1 - error_rate * 0.5)
        
        return round(adjusted_score, 2)
        
    def get_active_alerts(self) -> List[Dict]:
        """Get current system alerts"""
        alerts = []
        
        for system_name, status in self.automation_status.items():
            if status["status"] not in ["operational", "unknown"]:
                alerts.append({
                    "system": system_name,
                    "severity": "high" if status["status"] == "down" else "medium",
                    "message": f"{system_name} is {status['status']}",
                    "timestamp": status["last_check"]
                })
                
        # Add error alerts
        if len(self.error_log) > 5:
            alerts.append({
                "system": "automation_monitor",
                "severity": "high",
                "message": f"High error rate: {len(self.error_log)} errors in recent checks",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        return alerts
        
    async def apply_self_healing(self):
        """Attempt to recover failed systems"""
        recoveries = 0
        
        for system_name, status in self.automation_status.items():
            if status["status"] == "down":
                logger.info(f"🔧 Attempting to recover {system_name}")
                
                if system_name == "aurea_qc":
                    # Restart AUREA QC
                    try:
                        subprocess.run(
                            ["python3", "/home/mwwoodworth/code/AUREA_CLAUDEOS_QC_SYSTEM_V2.py"],
                            capture_output=True,
                            timeout=5
                        )
                        recoveries += 1
                    except:
                        pass
                        
                elif system_name == "memory_system":
                    # Clear memory cache
                    try:
                        async with self.session.post(
                            f"{BACKEND_URL}/api/v1/memory/clear-cache"
                        ) as resp:
                            if resp.status == 200:
                                recoveries += 1
                    except:
                        pass
                        
        self.metrics["auto_recoveries"] += recoveries
        return recoveries
        
    async def log_to_persistent_storage(self, log_type: str, data: Dict):
        """Store logs in persistent memory"""
        try:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            memory_entry = {
                "title": f"Automation Log: {log_type}",
                "content": json.dumps(data, indent=2),
                "role": "system",
                "memory_type": f"automation_log_{log_type}",
                "meta_data": {
                    "component": "automation_monitor",
                    "log_type": log_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **data
                },
                "is_active": True
            }
            
            async with self.session.post(
                f"{SUPABASE_URL}/rest/v1/copilot_messages",
                headers=headers,
                json=memory_entry
            ) as resp:
                if resp.status in [200, 201]:
                    logger.debug(f"Logged {log_type} to memory")
                    
        except Exception as e:
            logger.error(f"Persistent logging error: {e}")
            
    async def generate_daily_report(self) -> Dict[str, Any]:
        """Generate comprehensive daily automation report"""
        report = {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "summary": {
                "health_score": self.calculate_health_score(),
                "total_operations": self.metrics["total_checks"],
                "success_rate": (self.metrics["successful_operations"] / max(self.metrics["total_checks"], 1)) * 100,
                "auto_recoveries": self.metrics["auto_recoveries"],
                "alerts_generated": self.metrics["alerts_sent"]
            },
            "system_status": self.automation_status.copy(),
            "top_errors": self.analyze_error_patterns(),
            "recommendations": self.generate_recommendations()
        }
        
        # Store report
        await self.log_to_persistent_storage("daily_report", report)
        
        return report
        
    def analyze_error_patterns(self) -> List[Dict]:
        """Analyze error patterns for insights"""
        error_counts = {}
        
        for error in self.error_log[-100:]:  # Last 100 errors
            error_type = error.get("type", "unknown")
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
        # Sort by frequency
        patterns = [
            {"error_type": k, "frequency": v, "percentage": (v / len(self.error_log)) * 100}
            for k, v in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        ][:5]  # Top 5
        
        return patterns
        
    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check system-specific issues
        if self.automation_status["aurea_qc"]["health"] < 50:
            recommendations.append("AUREA QC system needs attention - consider restarting")
            
        if self.automation_status["langgraph"]["active_workflows"] == 0:
            recommendations.append("No active LangGraph workflows - verify configuration")
            
        if self.metrics["failed_operations"] > self.metrics["successful_operations"]:
            recommendations.append("High failure rate detected - review error logs")
            
        if not recommendations:
            recommendations.append("All systems operating within normal parameters")
            
        return recommendations
        
    async def run_continuous_monitoring(self):
        """Main monitoring loop"""
        logger.info("🚀 BrainOps Automation Monitor Starting")
        
        # Initial startup log
        await self.log_to_persistent_storage("startup", {
            "version": "1.0",
            "features": [
                "Multi-system monitoring",
                "Self-healing capabilities",
                "Real-time dashboard updates",
                "Persistent error logging",
                "Daily reporting"
            ]
        })
        
        check_interval = 300  # 5 minutes
        report_interval = 86400  # 24 hours
        last_report_time = datetime.now(timezone.utc)
        
        while True:
            try:
                self.metrics["total_checks"] += 1
                
                # Check all systems
                aurea_status = await self.check_aurea_qc()
                langgraph_status = await self.check_langgraph()
                perplexity_status = await self.check_perplexity_audit()
                claude_status = await self.check_claude_workflows()
                memory_status = await self.check_memory_system()
                
                # Update dashboard
                dashboard_updated = await self.update_dashboard_data()
                self.automation_status["dashboard"]["status"] = "operational" if dashboard_updated else "degraded"
                self.automation_status["dashboard"]["real_time"] = dashboard_updated
                
                # Count successes/failures
                operational_count = sum(
                    1 for status in [aurea_status, langgraph_status, claude_status, memory_status]
                    if status.get("operational", False)
                )
                
                if operational_count >= 3:
                    self.metrics["successful_operations"] += 1
                else:
                    self.metrics["failed_operations"] += 1
                    
                # Apply self-healing if needed
                if operational_count < 2:
                    recoveries = await self.apply_self_healing()
                    if recoveries > 0:
                        logger.info(f"🔧 Applied {recoveries} self-healing actions")
                        
                # Check for alerts
                alerts = self.get_active_alerts()
                if alerts:
                    self.metrics["alerts_sent"] += len(alerts)
                    await self.log_to_persistent_storage("alerts", {"alerts": alerts})
                    
                # Generate daily report
                if (datetime.now(timezone.utc) - last_report_time).total_seconds() >= report_interval:
                    report = await self.generate_daily_report()
                    logger.info(f"📊 Daily Report Generated - Health Score: {report['summary']['health_score']}%")
                    last_report_time = datetime.now(timezone.utc)
                    
                # Log current status
                if self.metrics["total_checks"] % 12 == 0:  # Every hour
                    logger.info(f"📈 Status Update - Health: {self.calculate_health_score()}%, Checks: {self.metrics['total_checks']}")
                    
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {str(e)}")
                logger.error(traceback.format_exc())
                
                self.error_log.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": type(e).__name__,
                    "message": str(e)
                })
                
                # Keep only last 1000 errors
                if len(self.error_log) > 1000:
                    self.error_log = self.error_log[-1000:]
                    
                await asyncio.sleep(60)  # Wait 1 minute on error


async def main():
    """Main entry point"""
    async with BrainOpsAutomationMonitor() as monitor:
        try:
            await monitor.run_continuous_monitoring()
        except KeyboardInterrupt:
            logger.info("👋 BrainOps Automation Monitor shutting down")
            
            # Final status log
            await monitor.log_to_persistent_storage("shutdown", {
                "reason": "user_requested",
                "final_metrics": monitor.metrics,
                "final_health": monitor.calculate_health_score()
            })


if __name__ == "__main__":
    asyncio.run(main())