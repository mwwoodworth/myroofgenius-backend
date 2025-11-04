"""
WeatherCraftAgent - Master of CenterPoint Data & Operations
Manages the WeatherCraft ERP and 1M+ CenterPoint records.
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

class WeatherCraftAgent(Agent):
    """
    The operations maestro who manages CenterPoint data, jobs, and ERP functionality.
    Ensures data integrity and operational efficiency for WeatherCraft.
    """
    
    def __init__(self):
        super().__init__(
            name="WeatherCraftAgent",
            specialization="operations_management",
            capabilities=[
                "centerpoint_data_management",
                "job_scheduling",
                "inventory_tracking",
                "crew_management",
                "invoice_generation",
                "estimate_creation",
                "material_optimization",
                "route_planning",
                "weather_monitoring",
                "compliance_tracking"
            ]
        )
        
        self.erp_url = "https://weathercraft-erp.vercel.app"
        self.backend_url = "https://brainops-backend-prod.onrender.com"
        self.check_interval = 300  # 5 minutes
        
    async def monitor_centerpoint_data(self) -> Dict[str, Any]:
        """Monitor CenterPoint data integrity and statistics"""
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_records": 0,
            "data_quality": {},
            "recent_updates": [],
            "issues": []
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Get total CenterPoint records
                total_records = await conn.fetchval("""
                    SELECT COUNT(*) FROM centerpoint_data
                """)
                stats["total_records"] = total_records
                
                # Check data quality
                missing_addresses = await conn.fetchval("""
                    SELECT COUNT(*) FROM centerpoint_data 
                    WHERE address IS NULL OR address = ''
                """)
                
                missing_phones = await conn.fetchval("""
                    SELECT COUNT(*) FROM centerpoint_data 
                    WHERE phone IS NULL OR phone = ''
                """)
                
                duplicate_records = await conn.fetchval("""
                    SELECT COUNT(*) FROM (
                        SELECT address, COUNT(*) as cnt 
                        FROM centerpoint_data 
                        GROUP BY address 
                        HAVING COUNT(*) > 1
                    ) as duplicates
                """)
                
                stats["data_quality"] = {
                    "completeness": ((total_records - missing_addresses - missing_phones) / max(total_records, 1)) * 100,
                    "missing_addresses": missing_addresses,
                    "missing_phones": missing_phones,
                    "duplicates": duplicate_records
                }
                
                # Get recent updates
                recent_updates = await conn.fetch("""
                    SELECT 
                        id,
                        customer_name,
                        address,
                        updated_at
                    FROM centerpoint_data
                    WHERE updated_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                    ORDER BY updated_at DESC
                    LIMIT 10
                """)
                
                stats["recent_updates"] = [
                    {
                        "id": str(row["id"]),
                        "customer": row["customer_name"],
                        "address": row["address"],
                        "updated": row["updated_at"].isoformat() if row["updated_at"] else None
                    }
                    for row in recent_updates
                ]
                
                # Check for issues
                if missing_addresses > 1000:
                    stats["issues"].append({
                        "type": "data_quality",
                        "severity": "high",
                        "message": f"{missing_addresses} records missing addresses",
                        "action": "Run address enrichment process"
                    })
                
                if duplicate_records > 100:
                    stats["issues"].append({
                        "type": "data_integrity",
                        "severity": "medium",
                        "message": f"{duplicate_records} duplicate address records",
                        "action": "Run deduplication process"
                    })
                
                logger.info(f"CenterPoint data stats: {total_records} records, {len(stats['issues'])} issues")
                
        except Exception as e:
            logger.error(f"Failed to monitor CenterPoint data: {e}")
            stats["error"] = str(e)
            
        return stats
    
    async def optimize_job_scheduling(self) -> Dict[str, Any]:
        """Optimize job scheduling and crew assignments"""
        optimizations = {
            "timestamp": datetime.utcnow().isoformat(),
            "jobs_analyzed": 0,
            "optimizations": [],
            "estimated_savings": 0
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Get upcoming jobs
                upcoming_jobs = await conn.fetch("""
                    SELECT 
                        j.id,
                        j.customer_id,
                        j.address,
                        j.scheduled_date,
                        j.estimated_hours,
                        j.crew_size,
                        j.status,
                        ST_X(j.location::geometry) as lng,
                        ST_Y(j.location::geometry) as lat
                    FROM jobs j
                    WHERE j.status IN ('scheduled', 'pending')
                    AND j.scheduled_date >= CURRENT_DATE
                    AND j.scheduled_date <= CURRENT_DATE + INTERVAL '7 days'
                    ORDER BY j.scheduled_date, j.address
                """)
                
                optimizations["jobs_analyzed"] = len(upcoming_jobs)
                
                # Group jobs by date and area for route optimization
                jobs_by_date = {}
                for job in upcoming_jobs:
                    date = job["scheduled_date"]
                    if date not in jobs_by_date:
                        jobs_by_date[date] = []
                    jobs_by_date[date].append(job)
                
                # Analyze each day's schedule
                for date, jobs in jobs_by_date.items():
                    if len(jobs) > 3:
                        # Check for route optimization opportunities
                        total_distance = self._calculate_route_distance(jobs)
                        optimized_distance = self._optimize_route(jobs)
                        
                        if optimized_distance < total_distance * 0.8:  # 20% improvement
                            savings = (total_distance - optimized_distance) * 0.5  # $0.50 per mile
                            optimizations["optimizations"].append({
                                "date": date.isoformat(),
                                "type": "route_optimization",
                                "jobs_count": len(jobs),
                                "current_distance": total_distance,
                                "optimized_distance": optimized_distance,
                                "estimated_savings": savings
                            })
                            optimizations["estimated_savings"] += savings
                
                # Check for crew optimization
                crew_utilization = await conn.fetch("""
                    SELECT 
                        scheduled_date,
                        SUM(crew_size * estimated_hours) as total_crew_hours,
                        COUNT(*) as job_count
                    FROM jobs
                    WHERE status IN ('scheduled', 'pending')
                    AND scheduled_date >= CURRENT_DATE
                    AND scheduled_date <= CURRENT_DATE + INTERVAL '7 days'
                    GROUP BY scheduled_date
                """)
                
                for day in crew_utilization:
                    if day["total_crew_hours"] < 40:  # Less than 5 crew members * 8 hours
                        optimizations["optimizations"].append({
                            "date": day["scheduled_date"].isoformat(),
                            "type": "crew_underutilization",
                            "utilization": (day["total_crew_hours"] / 40) * 100,
                            "recommendation": "Consider scheduling more jobs or reducing crew size"
                        })
                
        except Exception as e:
            logger.error(f"Failed to optimize job scheduling: {e}")
            optimizations["error"] = str(e)
            
        return optimizations
    
    def _calculate_route_distance(self, jobs: List[Dict]) -> float:
        """Calculate total distance for current route"""
        # Simplified distance calculation (would use real routing API in production)
        total = 0
        for i in range(len(jobs) - 1):
            lat1, lng1 = jobs[i].get("lat", 0), jobs[i].get("lng", 0)
            lat2, lng2 = jobs[i+1].get("lat", 0), jobs[i+1].get("lng", 0)
            # Haversine formula simplified
            total += ((lat2 - lat1)**2 + (lng2 - lng1)**2)**0.5 * 69  # Convert to miles
        return total
    
    def _optimize_route(self, jobs: List[Dict]) -> float:
        """Optimize route using nearest neighbor (simplified TSP)"""
        if not jobs:
            return 0
        
        # Start from first job
        optimized = [jobs[0]]
        remaining = jobs[1:]
        total_distance = 0
        
        while remaining:
            current = optimized[-1]
            nearest = min(remaining, key=lambda j: (
                (j.get("lat", 0) - current.get("lat", 0))**2 + 
                (j.get("lng", 0) - current.get("lng", 0))**2
            )**0.5)
            
            lat1, lng1 = current.get("lat", 0), current.get("lng", 0)
            lat2, lng2 = nearest.get("lat", 0), nearest.get("lng", 0)
            total_distance += ((lat2 - lat1)**2 + (lng2 - lng1)**2)**0.5 * 69
            
            optimized.append(nearest)
            remaining.remove(nearest)
        
        return total_distance
    
    async def manage_inventory(self) -> Dict[str, Any]:
        """Monitor and manage inventory levels"""
        inventory_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "materials": [],
            "reorder_needed": [],
            "total_value": 0
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Get inventory levels
                materials = await conn.fetch("""
                    SELECT 
                        m.id,
                        m.name,
                        m.sku,
                        m.quantity,
                        m.reorder_point,
                        m.unit_cost,
                        m.category
                    FROM materials m
                    WHERE m.is_active = true
                    ORDER BY m.category, m.name
                """)
                
                for material in materials:
                    value = material["quantity"] * material["unit_cost"]
                    inventory_status["total_value"] += value
                    
                    material_info = {
                        "id": str(material["id"]),
                        "name": material["name"],
                        "sku": material["sku"],
                        "quantity": material["quantity"],
                        "value": value,
                        "category": material["category"]
                    }
                    
                    inventory_status["materials"].append(material_info)
                    
                    # Check if reorder needed
                    if material["quantity"] <= material["reorder_point"]:
                        inventory_status["reorder_needed"].append({
                            "material": material["name"],
                            "current": material["quantity"],
                            "reorder_point": material["reorder_point"],
                            "suggested_order": material["reorder_point"] * 2
                        })
                
                # Store inventory insights
                if inventory_status["reorder_needed"]:
                    await self.memory.remember(
                        memory_type=MemoryType.INSIGHT,
                        content={
                            "type": "inventory_alert",
                            "reorder_needed": inventory_status["reorder_needed"],
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Failed to manage inventory: {e}")
            inventory_status["error"] = str(e)
            
        return inventory_status
    
    async def generate_operations_report(self) -> Dict[str, Any]:
        """Generate comprehensive operations report"""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "centerpoint_data": await self.monitor_centerpoint_data(),
            "job_optimization": await self.optimize_job_scheduling(),
            "inventory": await self.manage_inventory(),
            "kpis": {},
            "recommendations": []
        }
        
        try:
            async with self.pool.acquire() as conn:
                # Calculate KPIs
                jobs_completed = await conn.fetchval("""
                    SELECT COUNT(*) FROM jobs 
                    WHERE status = 'completed' 
                    AND completed_at >= CURRENT_DATE - INTERVAL '30 days'
                """)
                
                avg_job_duration = await conn.fetchval("""
                    SELECT AVG(EXTRACT(EPOCH FROM (completed_at - started_at))/3600)
                    FROM jobs 
                    WHERE status = 'completed' 
                    AND completed_at >= CURRENT_DATE - INTERVAL '30 days'
                """)
                
                revenue_generated = await conn.fetchval("""
                    SELECT COALESCE(SUM(total), 0) 
                    FROM invoices 
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                """)
                
                report["kpis"] = {
                    "jobs_completed_30d": jobs_completed,
                    "avg_job_duration_hours": float(avg_job_duration or 0),
                    "revenue_30d": float(revenue_generated or 0),
                    "centerpoint_records": report["centerpoint_data"]["total_records"],
                    "inventory_value": report["inventory"]["total_value"]
                }
                
                # Generate recommendations
                if report["centerpoint_data"]["data_quality"]["completeness"] < 90:
                    report["recommendations"].append({
                        "priority": "high",
                        "area": "data_quality",
                        "action": "Improve CenterPoint data completeness - currently at {:.1f}%".format(
                            report["centerpoint_data"]["data_quality"]["completeness"]
                        )
                    })
                
                if report["job_optimization"]["estimated_savings"] > 1000:
                    report["recommendations"].append({
                        "priority": "high",
                        "area": "operations",
                        "action": f"Implement route optimization - potential savings ${report['job_optimization']['estimated_savings']:.2f}"
                    })
                
                if report["inventory"]["reorder_needed"]:
                    report["recommendations"].append({
                        "priority": "medium",
                        "area": "inventory",
                        "action": f"Reorder {len(report['inventory']['reorder_needed'])} materials below threshold"
                    })
                    
        except Exception as e:
            logger.error(f"Failed to generate operations report: {e}")
            report["error"] = str(e)
            
        return report
    
    async def run(self):
        """Main agent loop"""
        await self.initialize()
        logger.info(f"WeatherCraftAgent started with ID {self.agent_id}")
        
        while True:
            try:
                # Generate operations report
                report = await self.generate_operations_report()
                
                # Store report as knowledge
                await self.memory.remember(
                    memory_type=MemoryType.KNOWLEDGE,
                    content=report
                )
                
                # Update system state
                health_status = "healthy"
                if report["centerpoint_data"].get("issues"):
                    health_status = "warning"
                if report.get("error"):
                    health_status = "error"
                    
                await self.update_system_state(
                    SystemComponent.FRONTEND_WC,
                    health_status,
                    {
                        "centerpoint_records": report["centerpoint_data"]["total_records"],
                        "jobs_scheduled": report["job_optimization"]["jobs_analyzed"],
                        "inventory_value": report["inventory"]["total_value"]
                    }
                )
                
                # Communicate with SystemArchitect
                await self.communicate(
                    "SystemArchitect",
                    {
                        "type": MessageType.STATUS,
                        "content": {
                            "component": "WeatherCraft",
                            "status": "operational",
                            "kpis": report["kpis"],
                            "issues": report["centerpoint_data"].get("issues", [])
                        }
                    }
                )
                
                # Communicate with DatabaseAgent about data quality
                if report["centerpoint_data"]["data_quality"]["duplicates"] > 100:
                    await self.communicate(
                        "DatabaseAgent",
                        {
                            "type": MessageType.REQUEST,
                            "content": {
                                "action": "deduplicate",
                                "table": "centerpoint_data",
                                "duplicates": report["centerpoint_data"]["data_quality"]["duplicates"]
                            }
                        }
                    )
                
                # Learn from experience
                if self.memory.count() % 10 == 0:
                    await self.learn()
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"WeatherCraftAgent error: {e}")
                await self.memory.remember(
                    memory_type=MemoryType.ERROR,
                    content={"error": str(e), "timestamp": datetime.utcnow().isoformat()}
                )
                await asyncio.sleep(60)

# Create singleton instance
weathercraft_agent = WeatherCraftAgent()