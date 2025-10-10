#!/usr/bin/env python3
"""
MASTER PERSISTENT MEMORY SYNC SYSTEM
Keeps local and production database in perfect sync
Ensures we NEVER lose context or forget anything
"""

import json
import os
import sqlite3
import psycopg2
from datetime import datetime
import hashlib
import threading
import time
from typing import Dict, Any, List, Optional

class PersistentMemorySync:
    def __init__(self):
        # Production database connection
        self.prod_db_url = "postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"
        
        # Local SQLite for fast access
        self.local_db = "/home/mwwoodworth/code/.ai_persistent/memory.db"
        
        # Sync interval in seconds
        self.sync_interval = 60  # Sync every minute
        
        # Initialize connections
        self.init_local_db()
        
    def init_local_db(self):
        """Initialize local SQLite database"""
        os.makedirs(os.path.dirname(self.local_db), exist_ok=True)
        conn = sqlite3.connect(self.local_db)
        
        # Create local tables that mirror production
        conn.execute('''
            CREATE TABLE IF NOT EXISTS persistent_memory (
                memory_key TEXT PRIMARY KEY,
                memory_value TEXT,
                category TEXT,
                importance INTEGER,
                updated_at TIMESTAMP,
                sync_status TEXT DEFAULT 'pending'
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_sops (
                sop_id TEXT PRIMARY KEY,
                title TEXT,
                steps TEXT,
                category TEXT,
                updated_at TIMESTAMP,
                sync_status TEXT DEFAULT 'pending'
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS system_state (
                component TEXT PRIMARY KEY,
                status TEXT,
                health_percentage REAL,
                version TEXT,
                last_check TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_production_connection(self):
        """Get connection to production PostgreSQL"""
        return psycopg2.connect(self.prod_db_url)
    
    def sync_to_production(self):
        """Sync local changes to production database"""
        local_conn = sqlite3.connect(self.local_db)
        prod_conn = self.get_production_connection()
        prod_cursor = prod_conn.cursor()
        
        try:
            # Sync pending memories
            pending = local_conn.execute(
                "SELECT * FROM persistent_memory WHERE sync_status = 'pending'"
            ).fetchall()
            
            for memory in pending:
                prod_cursor.execute('''
                    INSERT INTO persistent_memory (memory_key, memory_value, category, importance)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (memory_key) 
                    DO UPDATE SET 
                        memory_value = EXCLUDED.memory_value,
                        updated_at = NOW(),
                        access_count = persistent_memory.access_count + 1
                ''', (memory[0], json.dumps(json.loads(memory[1])), memory[2], memory[3]))
                
                # Mark as synced
                local_conn.execute(
                    "UPDATE persistent_memory SET sync_status = 'synced' WHERE memory_key = ?",
                    (memory[0],)
                )
            
            prod_conn.commit()
            local_conn.commit()
            
            return len(pending)
            
        except Exception as e:
            print(f"Sync error: {e}")
            prod_conn.rollback()
            return 0
        finally:
            prod_conn.close()
            local_conn.close()
    
    def sync_from_production(self):
        """Pull latest data from production to local"""
        local_conn = sqlite3.connect(self.local_db)
        prod_conn = self.get_production_connection()
        prod_cursor = prod_conn.cursor()
        
        try:
            # Get recent memories from production
            prod_cursor.execute('''
                SELECT memory_key, memory_value, category, importance, updated_at
                FROM persistent_memory
                WHERE is_active = true
                ORDER BY updated_at DESC
                LIMIT 100
            ''')
            
            memories = prod_cursor.fetchall()
            
            for memory in memories:
                local_conn.execute('''
                    INSERT OR REPLACE INTO persistent_memory 
                    (memory_key, memory_value, category, importance, updated_at, sync_status)
                    VALUES (?, ?, ?, ?, ?, 'synced')
                ''', (memory[0], json.dumps(memory[1]), memory[2], memory[3], memory[4]))
            
            # Get system state
            prod_cursor.execute('''
                SELECT component_id, health_status, health_percentage, version
                FROM system_architecture
                WHERE is_active = true
            ''')
            
            components = prod_cursor.fetchall()
            
            for comp in components:
                local_conn.execute('''
                    INSERT OR REPLACE INTO system_state
                    (component, status, health_percentage, version, last_check)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', comp)
            
            local_conn.commit()
            return len(memories)
            
        except Exception as e:
            print(f"Pull error: {e}")
            return 0
        finally:
            prod_conn.close()
            local_conn.close()
    
    def store_memory(self, key: str, value: Any, category: str = 'general', importance: int = 5):
        """Store a memory locally and mark for sync"""
        local_conn = sqlite3.connect(self.local_db)
        
        try:
            local_conn.execute('''
                INSERT OR REPLACE INTO persistent_memory
                (memory_key, memory_value, category, importance, updated_at, sync_status)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'pending')
            ''', (key, json.dumps(value), category, importance))
            
            local_conn.commit()
            
            # Trigger immediate sync for important memories
            if importance >= 8:
                self.sync_to_production()
                
        finally:
            local_conn.close()
    
    def get_memory(self, key: str) -> Optional[Dict]:
        """Get a memory from local cache"""
        local_conn = sqlite3.connect(self.local_db)
        
        try:
            result = local_conn.execute(
                "SELECT memory_value FROM persistent_memory WHERE memory_key = ?",
                (key,)
            ).fetchone()
            
            if result:
                return json.loads(result[0])
            return None
            
        finally:
            local_conn.close()
    
    def get_system_status(self) -> Dict:
        """Get current system status from local cache"""
        local_conn = sqlite3.connect(self.local_db)
        
        try:
            components = local_conn.execute(
                "SELECT component, status, health_percentage FROM system_state"
            ).fetchall()
            
            return {
                comp[0]: {
                    'status': comp[1],
                    'health': comp[2]
                }
                for comp in components
            }
            
        finally:
            local_conn.close()
    
    def record_action(self, action: str, details: Dict):
        """Record an action taken"""
        key = f"action_{datetime.utcnow().isoformat()}_{hashlib.md5(action.encode()).hexdigest()[:8]}"
        value = {
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.store_memory(key, value, 'actions', importance=6)
    
    def record_decision(self, decision: str, reasoning: str, outcome: Optional[str] = None):
        """Record a decision made"""
        prod_conn = self.get_production_connection()
        cursor = prod_conn.cursor()
        
        try:
            decision_id = f"decision_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            cursor.execute('''
                INSERT INTO decision_log 
                (decision_id, title, description, category, context, 
                 options_considered, decision_made, reasoning, actual_outcome)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                decision_id,
                decision[:100],  # Title is first 100 chars
                decision,
                'operational',
                json.dumps({'timestamp': datetime.utcnow().isoformat()}),
                json.dumps([]),
                decision,
                reasoning,
                json.dumps({'outcome': outcome}) if outcome else None
            ))
            
            prod_conn.commit()
            
        finally:
            prod_conn.close()
    
    def record_error(self, error_message: str, component: str, fix_applied: Optional[str] = None):
        """Record an error and its fix"""
        prod_conn = self.get_production_connection()
        cursor = prod_conn.cursor()
        
        try:
            error_id = f"error_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            cursor.execute('''
                INSERT INTO error_patterns 
                (error_id, error_message, error_type, component, immediate_fix)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (error_id) DO UPDATE
                SET frequency = error_patterns.frequency + 1,
                    last_seen = NOW()
            ''', (
                error_id,
                error_message,
                'runtime',
                component,
                json.dumps({'fix': fix_applied}) if fix_applied else None
            ))
            
            prod_conn.commit()
            
        finally:
            prod_conn.close()
    
    def start_sync_daemon(self):
        """Start background sync daemon"""
        def sync_loop():
            while True:
                try:
                    # Sync both ways
                    pushed = self.sync_to_production()
                    pulled = self.sync_from_production()
                    
                    if pushed > 0 or pulled > 0:
                        print(f"[{datetime.now()}] Synced: {pushed} to prod, {pulled} from prod")
                    
                except Exception as e:
                    print(f"Sync daemon error: {e}")
                
                time.sleep(self.sync_interval)
        
        daemon = threading.Thread(target=sync_loop, daemon=True)
        daemon.start()
        print("✅ Persistent Memory Sync Daemon started")
    
    def get_sop(self, sop_id: str) -> Optional[Dict]:
        """Get a specific SOP from production"""
        prod_conn = self.get_production_connection()
        cursor = prod_conn.cursor()
        
        try:
            cursor.execute('''
                SELECT title, description, steps, prerequisites, tools_required
                FROM system_sops
                WHERE sop_id = %s AND is_active = true
            ''', (sop_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'title': result[0],
                    'description': result[1],
                    'steps': result[2],
                    'prerequisites': result[3],
                    'tools': result[4]
                }
            return None
            
        finally:
            prod_conn.close()
    
    def search_memories(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search memories by keyword"""
        prod_conn = self.get_production_connection()
        cursor = prod_conn.cursor()
        
        try:
            if category:
                cursor.execute('''
                    SELECT memory_key, memory_value, category, importance
                    FROM persistent_memory
                    WHERE is_active = true
                    AND category = %s
                    AND (memory_key ILIKE %s OR memory_value::text ILIKE %s)
                    ORDER BY importance DESC, updated_at DESC
                    LIMIT 10
                ''', (category, f'%{query}%', f'%{query}%'))
            else:
                cursor.execute('''
                    SELECT memory_key, memory_value, category, importance
                    FROM persistent_memory
                    WHERE is_active = true
                    AND (memory_key ILIKE %s OR memory_value::text ILIKE %s)
                    ORDER BY importance DESC, updated_at DESC
                    LIMIT 10
                ''', (f'%{query}%', f'%{query}%'))
            
            results = cursor.fetchall()
            return [
                {
                    'key': r[0],
                    'value': r[1],
                    'category': r[2],
                    'importance': r[3]
                }
                for r in results
            ]
            
        finally:
            prod_conn.close()


# Singleton instance
_memory_sync = None

def get_memory_sync() -> PersistentMemorySync:
    """Get or create the singleton memory sync instance"""
    global _memory_sync
    if _memory_sync is None:
        _memory_sync = PersistentMemorySync()
        _memory_sync.start_sync_daemon()
    return _memory_sync


# Convenience functions
def remember(key: str, value: Any, category: str = 'general', importance: int = 5):
    """Store a memory"""
    get_memory_sync().store_memory(key, value, category, importance)

def recall(key: str) -> Optional[Dict]:
    """Recall a memory"""
    return get_memory_sync().get_memory(key)

def record_action(action: str, details: Dict):
    """Record an action"""
    get_memory_sync().record_action(action, details)

def record_decision(decision: str, reasoning: str, outcome: Optional[str] = None):
    """Record a decision"""
    get_memory_sync().record_decision(decision, reasoning, outcome)

def record_error(error: str, component: str, fix: Optional[str] = None):
    """Record an error"""
    get_memory_sync().record_error(error, component, fix)

def get_sop(sop_id: str) -> Optional[Dict]:
    """Get a Standard Operating Procedure"""
    return get_memory_sync().get_sop(sop_id)

def search(query: str, category: Optional[str] = None) -> List[Dict]:
    """Search memories"""
    return get_memory_sync().search_memories(query, category)

def status() -> Dict:
    """Get system status"""
    return get_memory_sync().get_system_status()


if __name__ == "__main__":
    # Initialize and test the system
    print("🧠 Initializing Persistent Memory Sync System...")
    
    sync = get_memory_sync()
    
    # Pull initial data from production
    count = sync.sync_from_production()
    print(f"✅ Pulled {count} memories from production")
    
    # Show current system status
    system_status = sync.get_system_status()
    print("\n📊 Current System Status:")
    for component, info in system_status.items():
        print(f"  {component}: {info['status']} ({info['health']}%)")
    
    # Test storing a new memory
    sync.store_memory(
        'last_sync_test',
        {'timestamp': datetime.utcnow().isoformat(), 'status': 'success'},
        'system',
        importance=7
    )
    
    print("\n✅ Persistent Memory Sync System is running!")
    print("   - Syncing every 60 seconds")
    print("   - Local cache at: /home/mwwoodworth/code/.ai_persistent/memory.db")
    print("   - Production sync to Supabase PostgreSQL")
    
    # Keep running if executed directly
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Shutting down sync system")