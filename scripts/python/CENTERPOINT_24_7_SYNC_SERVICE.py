#!/usr/bin/env python3
"""
CENTERPOINT 24/7 SYNC SERVICE
Runs permanently until CenterPoint is no longer needed
Self-healing, auto-recovering, continuous sync
"""

import os
import sys
import time
import json
import logging
import subprocess
import psycopg2
from datetime import datetime, timedelta
import signal
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/centerpoint_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

# CenterPoint configuration
CENTERPOINT_ENV = {
    "DATABASE_URL": DB_URL,
    "CENTERPOINT_BASE_URL": "https://api.centerpointconnect.io",
    "CENTERPOINT_BEARER_TOKEN": "eyJvcmciOiI2NmJlMzEwMzFiMGJjMTAwMDEwM2RiN2MiLCJpZCI6ImM4ZDdiMDIyNGQ4NDQ5OGI5M2MwYzY4MTc0NWU5M2Y0IiwiaCI6Im11cm11cjEyOCJ9",
    "CENTERPOINT_TENANT_ID": "97f82b360baefdd73400ad342562586"
}

class CenterPointSyncService:
    def __init__(self):
        self.running = True
        self.sync_interval = 300  # 5 minutes between syncs
        self.retry_delay = 60     # 1 minute retry on failure
        self.max_retries = 3
        self.consecutive_failures = 0
        self.total_syncs = 0
        self.successful_syncs = 0
        
    def signal_handler(self, signum, frame):
        logger.info("Shutdown signal received. Gracefully stopping...")
        self.running = False
        
    def log_to_db(self, sync_type, status, details=None, error=None):
        """Log sync status to database"""
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO centerpoint_sync_log 
                (sync_type, status, started_at, completed_at, details, errors)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                sync_type,
                status,
                datetime.now(),
                datetime.now() if status in ['completed', 'failed'] else None,
                json.dumps(details) if details else None,
                error
            ))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log to database: {e}")
            
    def update_persistent_memory(self, message):
        """Store sync status in persistent memory"""
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO copilot_messages 
                (title, content, memory_type, role, is_pinned, tags, meta_data, is_active, created_at, updated_at)
                VALUES (
                    'CENTERPOINT SYNC STATUS',
                    %s,
                    'operational_status',
                    'system',
                    false,
                    '{centerpoint,sync,status}',
                    %s,
                    true,
                    NOW(),
                    NOW()
                )
                ON CONFLICT ON CONSTRAINT copilot_messages_title_key
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    meta_data = EXCLUDED.meta_data,
                    updated_at = NOW()
            """, (
                message,
                json.dumps({
                    "total_syncs": self.total_syncs,
                    "successful_syncs": self.successful_syncs,
                    "last_sync": datetime.now().isoformat(),
                    "status": "running"
                })
            ))
            
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update persistent memory: {e}")
            
    def run_sync_script(self, script_name):
        """Execute a sync script with timeout and error handling"""
        try:
            logger.info(f"Executing sync script: {script_name}")
            
            # Set up environment
            env = os.environ.copy()
            env.update(CENTERPOINT_ENV)
            
            # Run the script with timeout
            result = subprocess.run(
                ["npx", "tsx", script_name],
                cwd="/home/mwwoodworth/code/weathercraft-erp",
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {script_name} completed successfully")
                return True, result.stdout
            else:
                logger.error(f"❌ {script_name} failed: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏱️ {script_name} timed out after 10 minutes")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"❌ Error running {script_name}: {e}")
            return False, str(e)
            
    def perform_sync(self):
        """Perform a complete sync cycle"""
        logger.info(f"🔄 Starting sync cycle #{self.total_syncs + 1}")
        self.total_syncs += 1
        
        sync_scripts = [
            "scripts/centerpoint-complete-sync.ts",
            "scripts/centerpoint-full-sync.ts",
            "scripts/populate-production-data.ts"
        ]
        
        for script in sync_scripts:
            if not self.running:
                break
                
            script_path = f"/home/mwwoodworth/code/weathercraft-erp/{script}"
            if os.path.exists(script_path):
                success, output = self.run_sync_script(script)
                
                if success:
                    self.successful_syncs += 1
                    self.consecutive_failures = 0
                    self.log_to_db("full_sync", "completed", {"script": script})
                    
                    # Parse output for counts if possible
                    if "customers" in output.lower():
                        logger.info(f"📊 Sync results from {script}:")
                        for line in output.split('\n'):
                            if any(word in line.lower() for word in ['customer', 'job', 'invoice', 'sync']):
                                logger.info(f"  {line.strip()}")
                    break
                else:
                    self.consecutive_failures += 1
                    self.log_to_db("full_sync", "failed", {"script": script}, output)
                    
                    if self.consecutive_failures >= self.max_retries:
                        logger.warning(f"Max retries reached. Waiting {self.retry_delay}s before next attempt")
                        time.sleep(self.retry_delay)
                        self.consecutive_failures = 0
        
        # Update persistent memory with status
        status_message = f"""
# CENTERPOINT 24/7 SYNC STATUS
- Total Sync Cycles: {self.total_syncs}
- Successful Syncs: {self.successful_syncs}
- Success Rate: {(self.successful_syncs/self.total_syncs*100):.1f}%
- Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Status: RUNNING 24/7
- Next Sync: In {self.sync_interval} seconds
        """
        self.update_persistent_memory(status_message)
        
    def get_database_stats(self):
        """Get current database statistics"""
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM customers WHERE external_id LIKE 'CP-%') as cp_customers,
                    (SELECT COUNT(*) FROM customers) as total_customers,
                    (SELECT COUNT(*) FROM jobs) as total_jobs,
                    (SELECT COUNT(*) FROM invoices) as total_invoices
            """)
            
            stats = cur.fetchone()
            cur.close()
            conn.close()
            
            logger.info(f"📊 Database Stats: CP Customers: {stats[0]}, Total Customers: {stats[1]}, Jobs: {stats[2]}, Invoices: {stats[3]}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return (0, 0, 0, 0)
            
    def run(self):
        """Main service loop - runs 24/7"""
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("🚀 CENTERPOINT 24/7 SYNC SERVICE STARTED")
        logger.info("This service will run permanently until manually stopped")
        logger.info(f"Sync interval: {self.sync_interval} seconds")
        
        # Initial status check
        self.get_database_stats()
        
        while self.running:
            try:
                # Perform sync
                self.perform_sync()
                
                # Get updated stats
                self.get_database_stats()
                
                # Wait for next sync
                logger.info(f"💤 Waiting {self.sync_interval} seconds until next sync...")
                for _ in range(self.sync_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                logger.error(traceback.format_exc())
                self.log_to_db("full_sync", "error", None, str(e))
                
                # Wait before retrying
                logger.info(f"Waiting {self.retry_delay} seconds before retry...")
                time.sleep(self.retry_delay)
                
        logger.info("🛑 CENTERPOINT 24/7 SYNC SERVICE STOPPED")
        
if __name__ == "__main__":
    service = CenterPointSyncService()
    service.run()
