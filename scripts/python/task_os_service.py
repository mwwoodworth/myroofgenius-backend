#!/usr/bin/env python3
"""
AI TASK OS - Production-Only Task Management
NO FAKE DATA ALLOWED - ONLY REAL WORK
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import asyncpg
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 
    'postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require')

class AITaskOS:
    def __init__(self):
        self.pool = None
        self.active_tasks = {}
        
    async def connect(self):
        """Connect to database"""
        # Disable statement caching for pgbouncer compatibility
        self.pool = await asyncpg.create_pool(
            DATABASE_URL, 
            min_size=2, 
            max_size=10,
            statement_cache_size=0  # Required for pgbouncer
        )
        logger.info("✅ Task OS connected to database")
        
    async def create_task(self, title: str, description: str, category: str, priority: int = 5) -> str:
        """Create a new task with production validation"""
        
        # Validate no fake data
        if any(word in title.lower() for word in ['test', 'demo', 'example', 'fake']):
            raise ValueError("❌ REJECTED: Task contains test/fake data keywords")
            
        async with self.pool.acquire() as conn:
            task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            result = await conn.fetchrow("""
                INSERT INTO ai_tasks (task_id, title, description, category, priority, created_by)
                VALUES ($1, $2, $3, $4, $5, 'ai')
                RETURNING id, task_id
            """, task_id, title, description, category, priority)
            
            logger.info(f"✅ Created task: {task_id} - {title}")
            return result['task_id']
            
    async def update_task_status(self, task_id: str, status: str, details: Dict = None):
        """Update task status with history tracking"""
        async with self.pool.acquire() as conn:
            # Update task
            await conn.execute("""
                UPDATE ai_tasks 
                SET status = $1, updated_at = NOW(),
                    started_at = CASE WHEN $1 = 'in_progress' THEN NOW() ELSE started_at END,
                    completed_at = CASE WHEN $1 = 'completed' THEN NOW() ELSE completed_at END
                WHERE task_id = $2
            """, status, task_id)
            
            # Add history
            task = await conn.fetchrow("SELECT id FROM ai_tasks WHERE task_id = $1", task_id)
            if task:
                await conn.execute("""
                    INSERT INTO task_history (task_id, action, details, performed_by)
                    VALUES ($1, $2, $3, 'ai')
                """, task['id'], f"status_change_{status}", json.dumps(details or {}))
                
            logger.info(f"📝 Updated {task_id} to {status}")
            
    async def get_pending_tasks(self) -> List[Dict]:
        """Get all pending production tasks"""
        async with self.pool.acquire() as conn:
            tasks = await conn.fetch("""
                SELECT task_id, title, description, priority, category, affects_mrg
                FROM ai_tasks 
                WHERE status = 'pending' 
                AND is_production = true 
                AND has_fake_data = false
                ORDER BY priority DESC, created_at ASC
            """)
            return [dict(t) for t in tasks]
            
    async def get_revenue_tasks(self) -> List[Dict]:
        """Get MyRoofGenius revenue-affecting tasks"""
        async with self.pool.acquire() as conn:
            tasks = await conn.fetch("""
                SELECT task_id, title, status, revenue_impact
                FROM ai_tasks 
                WHERE affects_mrg = true
                ORDER BY priority DESC
            """)
            return [dict(t) for t in tasks]
            
    async def validate_centerpoint_sync(self) -> Dict:
        """Check Centerpoint sync status"""
        async with self.pool.acquire() as conn:
            # Check actual data counts
            counts = await conn.fetchrow("""
                SELECT 
                    (SELECT COUNT(*) FROM customers WHERE external_id LIKE 'CP-%') as cp_customers,
                    (SELECT COUNT(*) FROM customers WHERE external_id LIKE 'TEST-%') as test_customers,
                    (SELECT COUNT(*) FROM centerpoint_files) as files,
                    (SELECT COUNT(*) FROM jobs WHERE external_id LIKE 'CP-%') as cp_jobs
            """)
            
            return {
                'centerpoint_customers': counts['cp_customers'],
                'test_customers': counts['test_customers'],
                'files_synced': counts['files'],
                'centerpoint_jobs': counts['cp_jobs'],
                'is_production': counts['test_customers'] == 0,
                'sync_percentage': (counts['files'] / 2000000) * 100
            }
            
    async def run_monitoring_loop(self):
        """Continuous monitoring and task management"""
        while True:
            try:
                # Check Centerpoint sync
                sync_status = await self.validate_centerpoint_sync()
                logger.info(f"📊 Centerpoint: {sync_status['sync_percentage']:.2f}% synced")
                
                if sync_status['test_customers'] > 0:
                    logger.warning(f"⚠️ FAKE DATA DETECTED: {sync_status['test_customers']} test customers")
                    
                # Check pending tasks
                pending = await self.get_pending_tasks()
                if pending:
                    logger.info(f"📋 {len(pending)} pending tasks")
                    for task in pending[:3]:  # Show top 3
                        logger.info(f"  - {task['task_id']}: {task['title']}")
                        
                # Check revenue tasks
                revenue_tasks = await self.get_revenue_tasks()
                mrg_pending = [t for t in revenue_tasks if t['status'] != 'completed']
                if mrg_pending:
                    logger.warning(f"💰 {len(mrg_pending)} MyRoofGenius revenue tasks pending!")
                    
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(10)

async def main():
    """Main Task OS service"""
    logger.info("🚀 Starting AI Task OS - Production Only Mode")
    
    task_os = AITaskOS()
    await task_os.connect()
    
    # Show current status
    sync_status = await task_os.validate_centerpoint_sync()
    logger.info(f"""
    =====================================
    📊 CURRENT SYSTEM STATUS:
    - Centerpoint Customers: {sync_status['centerpoint_customers']}
    - Test/Fake Customers: {sync_status['test_customers']}
    - Files Synced: {sync_status['files_synced']:,} / 2,000,000
    - Sync Progress: {sync_status['sync_percentage']:.2f}%
    - Production Mode: {'✅ YES' if sync_status['is_production'] else '❌ NO - FAKE DATA PRESENT'}
    =====================================
    """)
    
    # Get and show tasks
    pending = await task_os.get_pending_tasks()
    logger.info(f"\n📋 PENDING TASKS: {len(pending)}")
    for task in pending:
        logger.info(f"  [{task['priority']}] {task['task_id']}: {task['title']}")
        if task['affects_mrg']:
            logger.info(f"    💰 AFFECTS MYROOFGENIUS REVENUE")
    
    # Start monitoring
    await task_os.run_monitoring_loop()

if __name__ == "__main__":
    asyncio.run(main())
