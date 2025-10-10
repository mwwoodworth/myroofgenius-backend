"""
MyRoofGeniusAgent - Master of Customer Acquisition & Revenue
Manages the MyRoofGenius SaaS platform and customer lifecycle.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncpg
import httpx
import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import Agent, MemoryType, MessageType, SystemComponent

logger = logging.getLogger(__name__)

class MyRoofGeniusAgent(Agent):
    """
    The revenue generator who manages customer acquisition, conversion, and retention.
    Monitors and optimizes the MyRoofGenius platform for maximum revenue.
    """
    
    def __init__(self):
        super().__init__(
            name="MyRoofGeniusAgent",
            specialization="revenue_generation",
            capabilities=[
                "customer_acquisition",
                "conversion_optimization",
                "revenue_tracking",
                "user_behavior_analysis",
                "marketing_automation",
                "subscription_management",
                "lead_scoring",
                "churn_prediction",
                "pricing_optimization",
                "customer_support_ai"
            ]
        )
        
        self.frontend_url = "https://myroofgenius.com"
        self.backend_url = "https://brainops-backend-prod.onrender.com"
        self.check_interval = 300  # 5 minutes
        
    async def monitor_customer_metrics(self) -> Dict[str, Any]:
        """Monitor customer acquisition and revenue metrics"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "customers": {},
            "revenue": {},
            "conversion": {},
            "engagement": {}
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Customer metrics
                total_customers = await conn.fetchval("""
                    SELECT COUNT(*) FROM customers WHERE is_active = true
                """)
                
                new_customers_today = await conn.fetchval("""
                    SELECT COUNT(*) FROM customers 
                    WHERE created_at >= CURRENT_DATE
                """)
                
                new_customers_week = await conn.fetchval("""
                    SELECT COUNT(*) FROM customers 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                
                metrics["customers"] = {
                    "total": total_customers,
                    "new_today": new_customers_today,
                    "new_week": new_customers_week,
                    "growth_rate": (new_customers_week / max(total_customers, 1)) * 100
                }
                
                # Revenue metrics
                total_revenue = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0) FROM invoices 
                    WHERE status = 'paid'
                """)
                
                mrr = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0) FROM subscriptions 
                    WHERE status = 'active'
                """)
                
                revenue_today = await conn.fetchval("""
                    SELECT COALESCE(SUM(amount), 0) FROM invoices 
                    WHERE status = 'paid' AND paid_at >= CURRENT_DATE
                """)
                
                metrics["revenue"] = {
                    "total": float(total_revenue or 0),
                    "mrr": float(mrr or 0),
                    "today": float(revenue_today or 0),
                    "arr": float(mrr or 0) * 12
                }
                
                # Conversion metrics
                total_leads = await conn.fetchval("""
                    SELECT COUNT(*) FROM leads
                """)
                
                converted_leads = await conn.fetchval("""
                    SELECT COUNT(*) FROM leads WHERE status = 'converted'
                """)
                
                metrics["conversion"] = {
                    "total_leads": total_leads,
                    "converted": converted_leads,
                    "rate": (converted_leads / max(total_leads, 1)) * 100
                }
                
                # Engagement metrics
                active_users_today = await conn.fetchval("""
                    SELECT COUNT(DISTINCT user_id) FROM user_activity 
                    WHERE activity_date = CURRENT_DATE
                """)
                
                avg_session_duration = await conn.fetchval("""
                    SELECT AVG(duration_seconds) FROM user_sessions 
                    WHERE session_date >= CURRENT_DATE - INTERVAL '7 days'
                """)
                
                metrics["engagement"] = {
                    "dau": active_users_today,
                    "avg_session": float(avg_session_duration or 0),
                    "engagement_rate": (active_users_today / max(total_customers, 1)) * 100
                }
                
                logger.info(f"Customer metrics collected: {metrics}")
                
        except Exception as e:
            logger.error(f"Failed to collect customer metrics: {e}")
            metrics["error"] = str(e)
            
        return metrics
    
    async def optimize_conversion_funnel(self) -> Dict[str, Any]:
        """Analyze and optimize the conversion funnel"""
        optimizations = []
        
        try:
            async with self.pool.acquire() as conn:
                # Analyze funnel drop-offs
                funnel_stats = await conn.fetch("""
                    SELECT 
                        funnel_stage,
                        COUNT(*) as users,
                        AVG(time_in_stage) as avg_time
                    FROM user_funnel_tracking
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY funnel_stage
                    ORDER BY funnel_stage
                """)
                
                # Identify bottlenecks
                for i, stage in enumerate(funnel_stats[:-1]):
                    next_stage = funnel_stats[i + 1]
                    drop_rate = 1 - (next_stage['users'] / stage['users'])
                    
                    if drop_rate > 0.3:  # More than 30% drop
                        optimizations.append({
                            "stage": stage['funnel_stage'],
                            "drop_rate": drop_rate,
                            "recommendation": f"High drop-off detected at {stage['funnel_stage']}",
                            "action": "Implement A/B testing for this stage"
                        })
                
                # Check abandoned carts
                abandoned_carts = await conn.fetchval("""
                    SELECT COUNT(*) FROM shopping_carts 
                    WHERE status = 'abandoned' 
                    AND updated_at >= CURRENT_DATE - INTERVAL '7 days'
                """)
                
                if abandoned_carts > 10:
                    optimizations.append({
                        "issue": "abandoned_carts",
                        "count": abandoned_carts,
                        "recommendation": "Implement cart recovery emails",
                        "potential_revenue": abandoned_carts * 97  # Avg subscription value
                    })
                
                # Store optimization recommendations
                for opt in optimizations:
                    await self.memory.remember(
                        memory_type=MemoryType.INSIGHT,
                        content={"optimization": opt, "timestamp": datetime.utcnow().isoformat()}
                    )
                    
        except Exception as e:
            logger.error(f"Failed to optimize funnel: {e}")
            
        return {"optimizations": optimizations}
    
    async def predict_churn(self) -> List[Dict[str, Any]]:
        """Predict customers at risk of churning"""
        at_risk_customers = []
        
        try:
            async with self.pool.acquire() as conn:
                # Find customers with declining engagement
                declining_users = await conn.fetch("""
                    SELECT 
                        c.id,
                        c.email,
                        c.name,
                        ua.last_active,
                        ua.activity_score
                    FROM customers c
                    JOIN user_activity_summary ua ON c.id = ua.user_id
                    WHERE ua.activity_score < 30
                    AND ua.last_active < CURRENT_DATE - INTERVAL '7 days'
                    AND c.is_active = true
                    LIMIT 20
                """)
                
                for user in declining_users:
                    risk_score = 0
                    reasons = []
                    
                    # Calculate risk score
                    days_inactive = (datetime.utcnow() - user['last_active']).days
                    if days_inactive > 14:
                        risk_score += 40
                        reasons.append("Inactive for 2+ weeks")
                    elif days_inactive > 7:
                        risk_score += 20
                        reasons.append("Inactive for 1+ week")
                    
                    if user['activity_score'] < 20:
                        risk_score += 30
                        reasons.append("Very low engagement")
                    
                    # Check support tickets
                    unresolved_tickets = await conn.fetchval("""
                        SELECT COUNT(*) FROM support_tickets 
                        WHERE customer_id = $1 AND status != 'resolved'
                    """, user['id'])
                    
                    if unresolved_tickets > 0:
                        risk_score += 20
                        reasons.append(f"{unresolved_tickets} unresolved support tickets")
                    
                    if risk_score > 50:
                        at_risk_customers.append({
                            "customer_id": str(user['id']),
                            "email": user['email'],
                            "name": user['name'],
                            "risk_score": risk_score,
                            "reasons": reasons,
                            "recommended_action": self._get_retention_action(risk_score)
                        })
                
                # Store churn predictions
                if at_risk_customers:
                    await self.memory.remember(
                        memory_type=MemoryType.PATTERN,
                        content={
                            "churn_predictions": at_risk_customers,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Failed to predict churn: {e}")
            
        return at_risk_customers
    
    def _get_retention_action(self, risk_score: int) -> str:
        """Get recommended retention action based on risk score"""
        if risk_score > 80:
            return "Immediate personal outreach with special offer"
        elif risk_score > 60:
            return "Send win-back email campaign with discount"
        elif risk_score > 40:
            return "Send engagement email with new features"
        else:
            return "Monitor and send helpful content"
    
    async def generate_revenue_report(self) -> Dict[str, Any]:
        """Generate comprehensive revenue report"""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": await self.monitor_customer_metrics(),
            "funnel_optimization": await self.optimize_conversion_funnel(),
            "churn_analysis": await self.predict_churn(),
            "recommendations": []
        }
        
        # Generate strategic recommendations
        metrics = report["metrics"]
        
        if metrics.get("revenue", {}).get("mrr", 0) < 10000:
            report["recommendations"].append({
                "priority": "high",
                "area": "revenue",
                "action": "Focus on customer acquisition - MRR below $10k target"
            })
        
        if metrics.get("conversion", {}).get("rate", 0) < 2:
            report["recommendations"].append({
                "priority": "high",
                "area": "conversion",
                "action": "Optimize landing pages - conversion rate below 2%"
            })
        
        if len(report["churn_analysis"]) > 5:
            report["recommendations"].append({
                "priority": "critical",
                "area": "retention",
                "action": f"Address churn risk - {len(report['churn_analysis'])} customers at risk"
            })
        
        return report
    
    async def run(self):
        """Main agent loop"""
        await self.initialize()
        logger.info(f"MyRoofGeniusAgent started with ID {self.agent_id}")
        
        while True:
            try:
                # Generate revenue report
                report = await self.generate_revenue_report()
                
                # Store report as knowledge
                await self.memory.remember(
                    memory_type=MemoryType.KNOWLEDGE,
                    content=report
                )
                
                # Update system state
                await self.update_system_state(
                    SystemComponent.FRONTEND_MRG,
                    "healthy" if not report.get("churn_analysis") else "warning",
                    {
                        "mrr": report["metrics"].get("revenue", {}).get("mrr", 0),
                        "customers": report["metrics"].get("customers", {}).get("total", 0),
                        "at_risk": len(report.get("churn_analysis", []))
                    }
                )
                
                # Communicate with SystemArchitect
                await self.communicate(
                    "SystemArchitect",
                    {
                        "type": MessageType.STATUS,
                        "content": {
                            "component": "MyRoofGenius",
                            "status": "operational",
                            "metrics": report["metrics"],
                            "issues": report.get("churn_analysis", [])[:3]  # Top 3 at-risk
                        }
                    }
                )
                
                # Learn from experience
                if self.memory.count() % 10 == 0:
                    await self.learn()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"MyRoofGeniusAgent error: {e}")
                await self.memory.remember(
                    memory_type=MemoryType.ERROR,
                    content={"error": str(e), "timestamp": datetime.utcnow().isoformat()}
                )
                await asyncio.sleep(60)

# Create singleton instance
myroofgenius_agent = MyRoofGeniusAgent()