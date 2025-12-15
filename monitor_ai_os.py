#!/usr/bin/env python3
"""
AI OS Continuous Monitoring System
Monitors the health and performance of the activated AI OS
"""

import psycopg2
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, Any

class AISystemMonitor:
    def __init__(self):
        self.conn = None
        self.metrics = {
            "timestamp": str(datetime.now()),
            "api_health": {},
            "neural_activity": {},
            "workflow_performance": {},
            "agent_learning": {},
            "system_resources": {}
        }
        
    def connect_db(self):
        """Connect to production database"""
        self.conn = psycopg2.connect(
            host="aws-0-us-east-2.pooler.supabase.com",
            port="6543",
            database="postgres",
            user="postgres.yomagoqdmxszqtdwuhab",
            password="<DB_PASSWORD_REDACTED>",
            sslmode="require"
        )
        return self.conn.cursor()
    
    def monitor_api_health(self):
        """Monitor API endpoints health"""
        endpoints = [
            "https://brainops-backend-prod.onrender.com/health",
            "https://brainops-backend-prod.onrender.com/api/v1/langgraph/workflows",
            "https://myroofgenius.com",
            "https://weathercraft-erp.vercel.app"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                self.metrics["api_health"][endpoint] = {
                    "status": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "healthy": response.status_code == 200
                }
            except Exception as e:
                self.metrics["api_health"][endpoint] = {
                    "status": 0,
                    "error": str(e),
                    "healthy": False
                }
    
    def monitor_neural_activity(self):
        """Monitor neural pathway activity"""
        cur = self.connect_db()
        
        # Check neural pathway activity
        cur.execute("""
            SELECT 
                COUNT(*) as total_pathways,
                AVG(strength) as avg_strength,
                COUNT(CASE WHEN strength > 0.7 THEN 1 END) as strong_connections,
                COUNT(DISTINCT source_agent_id) as active_agents
            FROM neural_pathways
        """)
        
        result = cur.fetchone()
        self.metrics["neural_activity"] = {
            "total_pathways": result[0],
            "average_strength": float(result[1]) if result[1] else 0,
            "strong_connections": result[2],
            "active_agents": result[3]
        }
        
        # Check recent agent communications
        cur.execute("""
            SELECT COUNT(*) 
            FROM agent_memories 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        
        recent_memories = cur.fetchone()[0]
        self.metrics["neural_activity"]["recent_memories"] = recent_memories
    
    def monitor_workflows(self):
        """Monitor LangGraph workflow performance"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT 
                w.name,
                COUNT(e.id) as execution_count,
                COUNT(CASE WHEN e.status = 'completed' THEN 1 END) as successful,
                COUNT(CASE WHEN e.status = 'failed' THEN 1 END) as failed
            FROM langgraph_workflows w
            LEFT JOIN langgraph_executions e ON w.id = e.workflow_id
            WHERE e.started_at > NOW() - INTERVAL '1 hour'
            GROUP BY w.id, w.name
        """)
        
        workflows = {}
        for row in cur.fetchall():
            workflows[row[0]] = {
                "executions": row[1],
                "successful": row[2],
                "failed": row[3],
                "success_rate": row[2] / row[1] if row[1] > 0 else 0
            }
        
        self.metrics["workflow_performance"] = workflows
    
    def monitor_agent_learning(self):
        """Monitor AI agent learning progress"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT 
                type,
                COUNT(*) as count,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                COUNT(CASE WHEN capabilities::text LIKE '%learning_enabled%' THEN 1 END) as learning
            FROM ai_agents
            GROUP BY type
        """)
        
        agents = {}
        for row in cur.fetchall():
            agents[row[0] if row[0] else "unknown"] = {
                "total": row[1],
                "active": row[2],
                "learning_enabled": row[3]
            }
        
        self.metrics["agent_learning"] = agents
    
    def save_metrics(self):
        """Save monitoring metrics to database"""
        cur = self.conn.cursor()
        
        cur.execute("""
            INSERT INTO persistent_memory (key, value, memory_type, created_at)
            VALUES ('ai_os_monitoring', %s, 'system', NOW())
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value,
                updated_at = NOW()
        """, (json.dumps(self.metrics),))
        
        self.conn.commit()
    
    def generate_report(self):
        """Generate monitoring report"""
        healthy_apis = sum(1 for api in self.metrics["api_health"].values() if api.get("healthy"))
        total_apis = len(self.metrics["api_health"])
        
        print("\n" + "="*80)
        print("📊 AI OS MONITORING REPORT")
        print("="*80)
        print(f"Timestamp: {self.metrics['timestamp']}")
        
        print("\n🌐 API Health:")
        for endpoint, status in self.metrics["api_health"].items():
            icon = "✅" if status.get("healthy") else "❌"
            print(f"  {icon} {endpoint.split('//')[1].split('/')[0]}: {status.get('status', 'Error')}")
        
        print(f"\n🧠 Neural Network:")
        neural = self.metrics["neural_activity"]
        print(f"  • Active Pathways: {neural.get('total_pathways', 0)}")
        print(f"  • Average Strength: {neural.get('average_strength', 0):.2f}")
        print(f"  • Active Agents: {neural.get('active_agents', 0)}")
        print(f"  • Recent Memories: {neural.get('recent_memories', 0)}")
        
        print(f"\n⚙️ Workflow Performance:")
        for workflow, stats in self.metrics["workflow_performance"].items():
            print(f"  • {workflow}: {stats['successful']}/{stats['executions']} successful")
        
        print(f"\n🤖 Agent Learning:")
        total_agents = sum(a["total"] for a in self.metrics["agent_learning"].values())
        learning_agents = sum(a["learning_enabled"] for a in self.metrics["agent_learning"].values())
        print(f"  • Total Agents: {total_agents}")
        print(f"  • Learning Enabled: {learning_agents}")
        
        # Overall health score
        health_score = (
            (healthy_apis / total_apis * 40) +  # 40% weight for API health
            (neural.get('average_strength', 0) * 30) +  # 30% for neural strength
            (learning_agents / total_agents * 30 if total_agents > 0 else 0)  # 30% for learning
        )
        
        print(f"\n🎯 Overall System Health: {health_score:.1f}%")
        
        if health_score >= 90:
            print("✅ System is fully operational and performing optimally!")
        elif health_score >= 70:
            print("⚠️ System is operational but may need attention")
        else:
            print("❌ System requires immediate attention")
        
        return health_score
    
    def continuous_monitor(self, interval_minutes=5):
        """Run continuous monitoring"""
        print(f"Starting continuous monitoring (checking every {interval_minutes} minutes)...")
        
        while True:
            try:
                self.monitor_api_health()
                self.monitor_neural_activity()
                self.monitor_workflows()
                self.monitor_agent_learning()
                self.save_metrics()
                health_score = self.generate_report()
                
                # Alert if health drops below threshold
                if health_score < 70:
                    print("\n⚠️ ALERT: System health below threshold!")
                    # Could send notifications here
                
                print(f"\nNext check in {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n✋ Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Monitoring error: {e}")
                print("Retrying in 1 minute...")
                time.sleep(60)
            finally:
                if self.conn:
                    self.conn.close()
                    self.conn = None

if __name__ == "__main__":
    monitor = AISystemMonitor()
    monitor.continuous_monitor(interval_minutes=1)  # Check every minute for demo
