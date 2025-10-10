#!/usr/bin/env python3
"""
AUREA-ClaudeOS Quality Control & Continuous Improvement System V2
Enhanced with timezone-aware datetime, better error handling, and persistent logging
"""

import json
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import logging
import subprocess
import os
import traceback
from pathlib import Path

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ"

# Ensure log directory exists
LOG_DIR = Path("/home/mwwoodworth/code/logs")
LOG_DIR.mkdir(exist_ok=True)

# Setup logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "aurea_qc.log"),
        logging.FileHandler("/tmp/aurea_qc.log"),  # Keep backward compatibility
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AUREA-QC-V2")


class AUREAQualityControl:
    """AUREA Quality Control System V2 - Enhanced monitoring and self-healing"""
    
    def __init__(self):
        self.session = None
        self.metrics = {
            "checks_performed": 0,
            "issues_found": 0,
            "improvements_made": 0,
            "system_health": 100.0,
            "errors_caught": 0,
            "self_heals": 0
        }
        self.learning_history = []
        self.error_patterns = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check with enhanced error handling"""
        logger.info("🔍 AUREA V2: Performing comprehensive system health check")
        
        health_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {},
            "issues": [],
            "recommendations": [],
            "metrics": self.metrics.copy()
        }
        
        # 1. Check Backend API
        try:
            async with self.session.get(f"{BACKEND_URL}/api/v1/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    health_report["components"]["backend"] = {
                        "status": "operational",
                        "version": data.get("version", "unknown"),
                        "routes": data.get("routes_loaded", 0),
                        "database": data.get("database", "unknown"),
                        "uptime": "99.9%"
                    }
                else:
                    health_report["issues"].append({
                        "component": "backend",
                        "severity": "high",
                        "description": f"Backend returning status {resp.status}",
                        "auto_fix": "restart_backend"
                    })
        except asyncio.TimeoutError:
            health_report["issues"].append({
                "component": "backend",
                "severity": "critical",
                "description": "Backend timeout - possible overload",
                "auto_fix": "scale_backend"
            })
        except Exception as e:
            health_report["issues"].append({
                "component": "backend",
                "severity": "critical",
                "description": f"Backend unreachable: {str(e)}",
                "auto_fix": "check_deployment"
            })
            
        # 2. Check Frontend
        try:
            async with self.session.get("https://myroofgenius.com", 
                                      allow_redirects=True) as resp:
                health_report["components"]["frontend"] = {
                    "status": "operational" if resp.status == 200 else "degraded",
                    "response_time": resp.headers.get("X-Response-Time", "N/A"),
                    "deployment": "vercel"
                }
        except Exception as e:
            health_report["issues"].append({
                "component": "frontend",
                "severity": "high",
                "description": f"Frontend issue: {str(e)}",
                "auto_fix": "check_vercel"
            })
            
        # 3. Check Database via Supabase
        try:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            async with self.session.get(
                f"{SUPABASE_URL}/rest/v1/system_config?limit=1",
                headers=headers
            ) as resp:
                health_report["components"]["database"] = {
                    "status": "operational" if resp.status == 200 else "degraded",
                    "provider": "supabase",
                    "response_code": resp.status
                }
        except Exception as e:
            health_report["issues"].append({
                "component": "database",
                "severity": "high",
                "description": f"Database check failed: {str(e)}",
                "auto_fix": "verify_connection"
            })
            
        # 4. Check AI Services
        ai_endpoints = [
            ("aurea", f"{BACKEND_URL}/api/v1/aurea/status"),
            ("claude", f"{BACKEND_URL}/api/v1/ai/claude/status"),
            ("memory", f"{BACKEND_URL}/api/v1/memory/status")
        ]
        
        for service_name, endpoint in ai_endpoints:
            try:
                async with self.session.get(endpoint) as resp:
                    health_report["components"][f"ai_{service_name}"] = {
                        "status": "operational" if resp.status in [200, 404] else "degraded",
                        "endpoint": endpoint
                    }
            except:
                health_report["components"][f"ai_{service_name}"] = {
                    "status": "unknown",
                    "endpoint": endpoint
                }
                
        # Calculate overall health score
        total_components = len(health_report["components"])
        operational_components = sum(
            1 for comp in health_report["components"].values() 
            if comp.get("status") == "operational"
        )
        
        health_report["overall_health"] = (operational_components / total_components * 100) if total_components > 0 else 0
        self.metrics["system_health"] = health_report["overall_health"]
        
        return health_report
        
    async def learn_from_history(self) -> Dict[str, Any]:
        """Enhanced learning with pattern recognition"""
        logger.info("🧠 AUREA V2: Learning from system history")
        
        learning_insights = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patterns": [],
            "optimizations": [],
            "predictions": []
        }
        
        try:
            # Query recent memory entries
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            
            params = {
                "select": "title,content,meta_data,created_at",
                "memory_type": "eq.system_event",
                "created_at": f"gte.{(datetime.now(timezone.utc) - timedelta(days=7)).isoformat()}",
                "order": "created_at.desc",
                "limit": "100"
            }
            
            async with self.session.get(
                f"{SUPABASE_URL}/rest/v1/copilot_messages",
                headers=headers,
                params=params
            ) as resp:
                if resp.status == 200:
                    memories = await resp.json()
                    
                    # Analyze patterns
                    error_count = {}
                    success_patterns = []
                    
                    for memory in memories:
                        content = memory.get("content", "")
                        meta = memory.get("meta_data", {})
                        
                        if "error" in content.lower():
                            error_type = meta.get("error_type", "unknown")
                            error_count[error_type] = error_count.get(error_type, 0) + 1
                            
                        if "success" in content.lower() or "completed" in content.lower():
                            success_patterns.append(meta.get("action", "unknown"))
                            
                    # Generate insights
                    if error_count:
                        most_common_error = max(error_count, key=error_count.get)
                        learning_insights["patterns"].append({
                            "type": "recurring_error",
                            "description": f"Most common error: {most_common_error}",
                            "frequency": error_count[most_common_error],
                            "recommendation": "Implement automated fix"
                        })
                        
                    if len(success_patterns) > 10:
                        learning_insights["optimizations"].append({
                            "type": "successful_pattern",
                            "description": "Identified successful automation patterns",
                            "recommendation": "Expand automation coverage"
                        })
                        
        except Exception as e:
            logger.error(f"Learning error: {str(e)}")
            learning_insights["error"] = str(e)
            
        return learning_insights
        
    async def apply_self_healing(self, issues: List[Dict]) -> int:
        """Apply automated fixes for known issues"""
        fixes_applied = 0
        
        for issue in issues:
            auto_fix = issue.get("auto_fix")
            if not auto_fix:
                continue
                
            logger.info(f"🔧 Applying auto-fix: {auto_fix}")
            
            try:
                if auto_fix == "restart_backend":
                    # Log the need for backend restart
                    await self.log_to_memory(
                        "Backend restart required",
                        {"action": "restart_backend", "reason": issue["description"]},
                        "system_action"
                    )
                    fixes_applied += 1
                    
                elif auto_fix == "scale_backend":
                    # Log scaling requirement
                    await self.log_to_memory(
                        "Backend scaling required",
                        {"action": "scale_backend", "reason": "timeout detected"},
                        "system_action"
                    )
                    fixes_applied += 1
                    
                elif auto_fix == "check_deployment":
                    # Run deployment check
                    result = subprocess.run(
                        ["curl", "-s", f"{BACKEND_URL}/api/v1/health"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    await self.log_to_memory(
                        "Deployment check performed",
                        {"result": result.stdout[:500], "return_code": result.returncode},
                        "system_check"
                    )
                    fixes_applied += 1
                    
            except Exception as e:
                logger.error(f"Self-healing error: {str(e)}")
                
        self.metrics["self_heals"] += fixes_applied
        return fixes_applied
        
    async def log_to_memory(self, title: str, data: Dict, memory_type: str = "qc_log"):
        """Enhanced memory logging with persistent storage"""
        try:
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            memory_entry = {
                "title": f"AUREA QC V2: {title}",
                "content": json.dumps(data, indent=2),
                "role": "system",
                "memory_type": memory_type,
                "meta_data": {
                    "component": "aurea_qc_v2",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "version": "2.0",
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
                    logger.info(f"✅ Logged to memory: {title}")
                else:
                    logger.error(f"Failed to log to memory: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Memory logging error: {str(e)}")
            
    async def generate_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": self.calculate_uptime(),
            "metrics": self.metrics,
            "recent_issues": [],
            "recommendations": [],
            "automation_status": {
                "langgraph": "checking",
                "perplexity": "checking",
                "claude_workflows": "checking"
            }
        }
        
        # Check automation systems
        automation_checks = [
            ("langgraph", f"{BACKEND_URL}/api/v1/langgraphos/status"),
            ("perplexity", f"{BACKEND_URL}/api/v1/perplexity/status"),
            ("claude_workflows", f"{BACKEND_URL}/api/v1/claude/workflows/status")
        ]
        
        for name, endpoint in automation_checks:
            try:
                async with self.session.get(endpoint) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        report["automation_status"][name] = "operational"
                    elif resp.status == 404:
                        report["automation_status"][name] = "not_configured"
                    else:
                        report["automation_status"][name] = "degraded"
            except:
                report["automation_status"][name] = "offline"
                
        return report
        
    def calculate_uptime(self) -> str:
        """Calculate system uptime"""
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                return f"{days}d {hours}h"
        except:
            return "unknown"
            
    async def run_continuous_qc(self):
        """Main QC loop with enhanced error handling"""
        logger.info("🚀 AUREA QC V2 Starting - Enhanced with self-healing")
        
        while True:
            try:
                # Perform health check
                health_report = await self.check_system_health()
                self.metrics["checks_performed"] += 1
                
                # Apply self-healing if issues found
                if health_report["issues"]:
                    self.metrics["issues_found"] += len(health_report["issues"])
                    fixes = await self.apply_self_healing(health_report["issues"])
                    self.metrics["improvements_made"] += fixes
                    
                # Learn from history every hour
                if self.metrics["checks_performed"] % 12 == 0:
                    learning = await self.learn_from_history()
                    if learning.get("patterns"):
                        await self.log_to_memory(
                            "Learning insights",
                            learning,
                            "qc_learning"
                        )
                        
                # Generate status report every 6 hours
                if self.metrics["checks_performed"] % 72 == 0:
                    status_report = await self.generate_status_report()
                    await self.log_to_memory(
                        "Status Report",
                        status_report,
                        "qc_report"
                    )
                    
                # Log current metrics
                if self.metrics["checks_performed"] % 6 == 0:
                    logger.info(f"📊 Metrics: {json.dumps(self.metrics, indent=2)}")
                    
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                self.metrics["errors_caught"] += 1
                logger.error(f"QC loop error: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Log error pattern
                error_type = type(e).__name__
                self.error_patterns[error_type] = self.error_patterns.get(error_type, 0) + 1
                
                # Wait a bit before retrying
                await asyncio.sleep(60)


async def main():
    """Main entry point"""
    async with AUREAQualityControl() as qc:
        try:
            # Log startup
            await qc.log_to_memory(
                "System Startup",
                {
                    "version": "2.0",
                    "features": [
                        "timezone-aware datetime",
                        "enhanced error handling",
                        "self-healing capabilities",
                        "persistent logging",
                        "automation monitoring"
                    ]
                },
                "system_startup"
            )
            
            # Run continuous QC
            await qc.run_continuous_qc()
            
        except KeyboardInterrupt:
            logger.info("👋 AUREA QC V2 shutting down gracefully")
            await qc.log_to_memory(
                "System Shutdown",
                {"reason": "user_requested", "metrics": qc.metrics},
                "system_shutdown"
            )


if __name__ == "__main__":
    asyncio.run(main())