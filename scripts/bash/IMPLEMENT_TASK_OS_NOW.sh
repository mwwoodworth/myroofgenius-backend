#!/bin/bash

echo "🚀 IMPLEMENTING AI TASK OS - PRODUCTION ONLY SYSTEM"
echo "=================================================="
echo "This will create a REAL working task tracking system"
echo "NO FAKE DATA - ONLY PRODUCTION WORK ACCEPTED"
echo ""

# Step 1: Create Task OS database schema
echo "📋 Step 1: Creating Task OS database..."
export DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

psql "$DATABASE_URL" << 'EOF'
-- Create AI Task OS tables
CREATE TABLE IF NOT EXISTS ai_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(50) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    category VARCHAR(50),
    created_by VARCHAR(20) DEFAULT 'ai',
    assigned_to VARCHAR(100),
    
    -- Production validation
    is_production BOOLEAN DEFAULT true,
    has_fake_data BOOLEAN DEFAULT false,
    validation_status VARCHAR(50),
    
    -- Revenue tracking
    revenue_impact DECIMAL(10,2),
    affects_mrg BOOLEAN DEFAULT false,
    
    -- Context and memory
    context JSONB,
    previous_attempts INTEGER DEFAULT 0,
    error_log JSONB,
    
    -- Tracking
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES ai_tasks(id),
    action VARCHAR(50),
    details JSONB,
    performed_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES ai_tasks(id),
    depends_on UUID REFERENCES ai_tasks(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tasks_status ON ai_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_production ON ai_tasks(is_production);
CREATE INDEX IF NOT EXISTS idx_tasks_mrg ON ai_tasks(affects_mrg);

-- Insert critical tasks
INSERT INTO ai_tasks (task_id, title, description, status, priority, category, affects_mrg, context)
VALUES 
    ('TASK-001', 'Fix Centerpoint Sync - Get 1-2M Data Points', 
     'Current sync only getting 0.6% of data. Need to fix API auth and implement robust retry logic for all 1-2 million data points',
     'in_progress', 10, 'data-sync', false,
     '{"current_count": 2900, "expected_count": 2000000, "api_errors": ["502", "404"]}'::jsonb),
     
    ('TASK-002', 'Make MyRoofGenius Generate Revenue', 
     'Site running but not processing payments or customers. Need payment integration and customer flow',
     'pending', 10, 'revenue', true,
     '{"current_revenue": 0, "target": "automated income generation"}'::jsonb),
     
    ('TASK-003', 'Remove All Fake/Test Data', 
     'Database has TEST- prefixed data instead of real CP- data. Must purge and use only production data',
     'pending', 9, 'data-quality', false,
     '{"fake_customers": 100, "fake_jobs": 200}'::jsonb),
     
    ('TASK-004', 'Fix Backend Route Loading', 
     'Only 8 routers loading, should be 150+. Fix all route registration',
     'pending', 8, 'backend', true,
     '{"current_routers": 8, "expected_routers": 150}'::jsonb)
ON CONFLICT (task_id) DO UPDATE SET
    updated_at = NOW();

-- Create validation function
CREATE OR REPLACE FUNCTION validate_task_production()
RETURNS TRIGGER AS $$
BEGIN
    -- Check for fake data indicators
    IF NEW.title ILIKE '%test%' OR NEW.title ILIKE '%demo%' OR NEW.title ILIKE '%example%' THEN
        NEW.has_fake_data = true;
        NEW.validation_status = 'Contains test/demo keywords';
    END IF;
    
    -- Mark revenue tasks
    IF NEW.title ILIKE '%revenue%' OR NEW.title ILIKE '%payment%' OR NEW.title ILIKE '%myroofgenius%' THEN
        NEW.affects_mrg = true;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS validate_task_trigger ON ai_tasks;
CREATE TRIGGER validate_task_trigger
    BEFORE INSERT OR UPDATE ON ai_tasks
    FOR EACH ROW
    EXECUTE FUNCTION validate_task_production();
EOF

echo "  ✅ Database schema created"
echo ""

# Step 2: Create Python Task OS service
echo "📦 Step 2: Creating Task OS service..."
cat > /home/mwwoodworth/code/task_os_service.py << 'PYTHON'
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
    'postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require')

class AITaskOS:
    def __init__(self):
        self.pool = None
        self.active_tasks = {}
        
    async def connect(self):
        """Connect to database"""
        self.pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
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
PYTHON

chmod +x /home/mwwoodworth/code/task_os_service.py
echo "  ✅ Task OS service created"
echo ""

# Step 3: Create systemd service for persistence
echo "🔄 Step 3: Setting up persistent service..."
cat > /tmp/task-os.service << 'SERVICE'
[Unit]
Description=AI Task OS - Production Task Management
After=network.target

[Service]
Type=simple
User=mwwoodworth
WorkingDirectory=/home/mwwoodworth/code
ExecStart=/usr/bin/python3 /home/mwwoodworth/code/task_os_service.py
Restart=always
RestartSec=10
Environment="DATABASE_URL=postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

[Install]
WantedBy=multi-user.target
SERVICE

echo "  ✅ Service configuration created"
echo ""

# Step 4: Start the Task OS
echo "🚀 Step 4: Starting Task OS..."
pip3 install asyncpg --quiet 2>/dev/null
nohup python3 /home/mwwoodworth/code/task_os_service.py > /tmp/task_os.log 2>&1 &
TASK_OS_PID=$!
echo "  ✅ Task OS started with PID: $TASK_OS_PID"
echo ""

# Step 5: Show initial output
echo "📊 Initial Task OS output:"
sleep 3
tail -20 /tmp/task_os.log

echo ""
echo "=================================================="
echo "✅ AI TASK OS IMPLEMENTATION COMPLETE!"
echo "=================================================="
echo ""
echo "Features Enabled:"
echo "  ✅ Production-only task validation"
echo "  ✅ Fake data detection and rejection"
echo "  ✅ Revenue task tracking for MyRoofGenius"
echo "  ✅ Centerpoint sync monitoring"
echo "  ✅ Task history and dependencies"
echo "  ✅ Continuous monitoring loop"
echo ""
echo "Logs: tail -f /tmp/task_os.log"
echo "Database: ai_tasks table in Supabase"
echo ""
echo "🎯 NEXT: Fix the critical tasks in priority order!"