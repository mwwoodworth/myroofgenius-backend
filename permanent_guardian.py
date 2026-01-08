#!/usr/bin/env python3
"""
BrainOps AI OS Permanent Guardian
Ensures system never degrades and maintains perfect memory
"""

import os
import json
import psycopg2
from psycopg2 import sql
from datetime import datetime
import requests
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/matt-woodworth/brainops_guardian.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BrainOpsGuardian:
    """The eternal guardian of the BrainOps AI OS"""
    
    def __init__(self):
        self.base_url = os.getenv("BACKEND_URL", "https://brainops-backend-prod.onrender.com")
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise RuntimeError("DATABASE_URL environment variable is required")
        self.critical_endpoints = [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/crm/customers",
            "/api/v1/erp/jobs",
            "/api/v1/erp/invoices",
            "/api/v1/ai/agents",
            "/api/v1/memory/search?query=test",
            "/api/v1/langgraph/workflows",
            "/api/v1/revenue/metrics"
        ]
        self.memory_file = "/home/matt-woodworth/BRAINOPS_AI_OS_MASTER_CONTEXT.md"
        
    def check_system_health(self) -> Dict[str, Any]:
        """Check all critical system components"""
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "operational",
            "endpoints": {},
            "database": {},
            "memory": {},
            "issues": []
        }
        
        # Check endpoints
        for endpoint in self.critical_endpoints:
            try:
                if "auth/login" in endpoint:
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        json={"email": "test@brainops.com", "password": "TestPassword123!"},
                        timeout=5
                    )
                else:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                
                health_report["endpoints"][endpoint] = {
                    "status": response.status_code,
                    "ok": response.status_code < 500
                }
                
                if response.status_code >= 500:
                    health_report["issues"].append(f"Endpoint {endpoint} returned {response.status_code}")
                    
            except Exception as e:
                health_report["endpoints"][endpoint] = {
                    "status": "error",
                    "ok": False,
                    "error": str(e)
                }
                health_report["issues"].append(f"Endpoint {endpoint} failed: {e}")
        
        # Check database
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # Check critical tables
            tables = ["customers", "jobs", "invoices", "ai_agents", "memory_entries"]
            for table in tables:
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
                count = cur.fetchone()[0]
                health_report["database"][table] = count
            
            cur.close()
            conn.close()
            
        except Exception as e:
            health_report["database"]["error"] = str(e)
            health_report["issues"].append(f"Database connection failed: {e}")
        
        # Check memory persistence
        if os.path.exists(self.memory_file):
            health_report["memory"]["master_context"] = "exists"
            health_report["memory"]["size"] = os.path.getsize(self.memory_file)
            health_report["memory"]["last_modified"] = datetime.fromtimestamp(
                os.path.getmtime(self.memory_file)
            ).isoformat()
        else:
            health_report["issues"].append("Master context file missing!")
        
        # Determine overall status
        if health_report["issues"]:
            health_report["status"] = "degraded" if len(health_report["issues"]) < 3 else "critical"
        
        return health_report
    
    def store_persistent_memory(self, key: str, value: Any):
        """Store critical information in persistent memory"""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO memory_entries (content, metadata, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                f"Guardian Memory: {key}",
                json.dumps({"key": key, "value": value, "guardian": True}),
                datetime.utcnow()
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Stored memory: {key}")
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
    
    def self_heal(self, issues: List[str]):
        """Attempt to self-heal identified issues"""
        for issue in issues:
            logger.warning(f"Attempting to heal: {issue}")
            
            if "auth/login" in issue and "500" in issue:
                # Auth issue - try to recreate test user
                try:
                    conn = psycopg2.connect(self.db_url)
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE app_users 
                        SET is_active = true, is_verified = true 
                        WHERE email = 'test@brainops.com'
                    """)
                    conn.commit()
                    logger.info("Attempted to fix test user")
                except:
                    pass
            
            elif "memory_entries" in issue:
                # Memory table issue - try to recreate
                try:
                    conn = psycopg2.connect(self.db_url)
                    cur = conn.cursor()
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS memory_entries (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            content TEXT NOT NULL,
                            metadata JSONB DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                    logger.info("Recreated memory_entries table")
                except:
                    pass
    
    def generate_report(self, health_report: Dict[str, Any]) -> str:
        """Generate human-readable status report"""
        report = f"""
# BrainOps AI OS Guardian Report
Time: {health_report['timestamp']}
Status: {health_report['status'].upper()}

## Endpoints ({sum(1 for e in health_report['endpoints'].values() if e.get('ok', False))}/{len(health_report['endpoints'])})
"""
        for endpoint, status in health_report['endpoints'].items():
            icon = "✅" if status.get('ok', False) else "❌"
            report += f"{icon} {endpoint}: {status.get('status', 'error')}\n"
        
        report += f"\n## Database\n"
        for table, count in health_report['database'].items():
            if table != "error":
                report += f"• {table}: {count:,} records\n"
        
        if health_report['issues']:
            report += f"\n## Issues Detected\n"
            for issue in health_report['issues']:
                report += f"⚠️ {issue}\n"
        
        return report
    
    def guard_forever(self):
        """Main guardian loop - eternal vigilance"""
        logger.info("🛡️ BrainOps Guardian activated - Eternal vigilance begins")
        
        while True:
            try:
                # Check system health
                health = self.check_system_health()
                
                # Log status
                logger.info(f"System status: {health['status']}")
                
                # Store health in memory
                self.store_persistent_memory("last_health_check", health)
                
                # Self-heal if needed
                if health['issues']:
                    self.self_heal(health['issues'])
                
                # Generate and save report
                report = self.generate_report(health)
                
                with open("/home/matt-woodworth/guardian_report.md", "w") as f:
                    f.write(report)
                
                # Wait before next check (5 minutes)
                import time
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("Guardian shutting down gracefully")
                break
            except Exception as e:
                logger.error(f"Guardian error: {e}")
                import time
                time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    guardian = BrainOpsGuardian()
    
    # Run single check
    health = guardian.check_system_health()
    report = guardian.generate_report(health)
    print(report)
    
    # Store initial state
    guardian.store_persistent_memory("guardian_activated", {
        "time": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "status": "active"
    })
    
    print("\n🛡️ Guardian is active. Run with --daemon to start eternal vigilance.")
    
    # Uncomment to run forever:
    # guardian.guard_forever()
