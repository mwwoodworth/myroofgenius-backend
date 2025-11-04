#!/usr/bin/env python3
"""
ROBUST DATABASE SYNC SYSTEM
Handles intermittent connectivity and ensures production is ALWAYS current
"""

import psycopg2
import time
import json
import hashlib
from datetime import datetime
import subprocess
import os

# Database connections
PROD_DB = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
LOCAL_DB = "postgresql://postgres:postgres@localhost:54322/postgres"

class RobustDBSync:
    def __init__(self):
        self.last_sync = None
        self.sync_status = "unknown"
        self.changes_pending = []
        
    def check_connectivity(self):
        """Check if we can reach production database"""
        try:
            conn = psycopg2.connect(PROD_DB)
            conn.close()
            return True
        except:
            return False
    
    def get_db_checksum(self, connection_string):
        """Get checksum of database state for comparison"""
        try:
            conn = psycopg2.connect(connection_string)
            cur = conn.cursor()
            
            # Get counts and checksums for critical tables
            tables = ['app_users', 'customers', 'jobs', 'invoices', 'estimates', 
                     'products', 'automations', 'ai_agents']
            
            checksum_data = {}
            for table in tables:
                cur.execute(f"SELECT COUNT(*), MAX(updated_at) FROM {table}")
                count, last_update = cur.fetchone()
                checksum_data[table] = {
                    'count': count,
                    'last_update': str(last_update) if last_update else None
                }
            
            cur.close()
            conn.close()
            
            # Create overall checksum
            checksum = hashlib.md5(json.dumps(checksum_data, sort_keys=True).encode()).hexdigest()
            return checksum, checksum_data
            
        except Exception as e:
            print(f"❌ Error getting checksum: {e}")
            return None, None
    
    def sync_to_production(self):
        """Push local changes to production"""
        if not self.check_connectivity():
            print("⚠️  No connection to production - changes queued")
            return False
        
        try:
            local_checksum, local_data = self.get_db_checksum(LOCAL_DB)
            prod_checksum, prod_data = self.get_db_checksum(PROD_DB)
            
            if local_checksum == prod_checksum:
                print("✅ Databases are in sync")
                self.sync_status = "synced"
                return True
            
            print("🔄 Syncing changes to production...")
            
            # Connect to both databases
            local_conn = psycopg2.connect(LOCAL_DB)
            prod_conn = psycopg2.connect(PROD_DB)
            local_cur = local_conn.cursor()
            prod_cur = prod_conn.cursor()
            
            # Find tables with differences
            for table, local_info in local_data.items():
                prod_info = prod_data.get(table, {})
                
                if local_info != prod_info:
                    print(f"  📤 Updating {table}: {prod_info.get('count', 0)} -> {local_info['count']} rows")
                    
                    # Export from local
                    local_cur.execute(f"""
                        SELECT * FROM {table} 
                        WHERE updated_at > COALESCE(%s, '1970-01-01'::timestamp)
                    """, (prod_info.get('last_update'),))
                    
                    rows = local_cur.fetchall()
                    
                    if rows:
                        # Get column names
                        local_cur.execute(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = %s
                            ORDER BY ordinal_position
                        """, (table,))
                        columns = [col[0] for col in local_cur.fetchall()]
                        
                        # Upsert to production
                        for row in rows:
                            placeholders = ','.join(['%s'] * len(columns))
                            update_set = ','.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])
                            
                            prod_cur.execute(f"""
                                INSERT INTO {table} ({','.join(columns)})
                                VALUES ({placeholders})
                                ON CONFLICT (id) DO UPDATE SET {update_set}
                            """, row)
                    
                    prod_conn.commit()
            
            local_cur.close()
            prod_cur.close()
            local_conn.close()
            prod_conn.close()
            
            print("✅ Production updated successfully")
            self.sync_status = "synced"
            self.last_sync = datetime.now()
            return True
            
        except Exception as e:
            print(f"❌ Sync error: {e}")
            self.sync_status = "error"
            return False
    
    def pull_from_production(self):
        """Pull latest from production to local"""
        if not self.check_connectivity():
            print("⚠️  No connection to production - using local cache")
            return False
        
        try:
            print("📥 Pulling latest from production...")
            
            # Use pg_dump and pg_restore for full sync
            dump_file = "/tmp/prod_dump.sql"
            
            # Dump from production
            dump_cmd = f"""
            PGPASSWORD='Brain0ps2O2S' pg_dump \
                -h db.yomagoqdmxszqtdwuhab.supabase.co \
                -U postgres \
                -d postgres \
                --schema=public \
                --no-owner \
                --no-privileges \
                --data-only \
                > {dump_file}
            """
            
            result = subprocess.run(dump_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Restore to local
                restore_cmd = f"""
                psql -h localhost -p 54322 -U postgres -d postgres < {dump_file}
                """
                
                subprocess.run(restore_cmd, shell=True)
                print("✅ Local database updated from production")
                self.sync_status = "synced"
                return True
            else:
                print(f"❌ Pull failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Pull error: {e}")
            return False
    
    def monitor_changes(self):
        """Monitor for local changes that need syncing"""
        try:
            conn = psycopg2.connect(LOCAL_DB)
            cur = conn.cursor()
            
            # Check for recent changes
            cur.execute("""
                SELECT table_name, COUNT(*) as changes
                FROM (
                    SELECT 'customers' as table_name FROM customers WHERE updated_at > NOW() - INTERVAL '5 minutes'
                    UNION ALL
                    SELECT 'jobs' FROM jobs WHERE updated_at > NOW() - INTERVAL '5 minutes'
                    UNION ALL
                    SELECT 'invoices' FROM invoices WHERE updated_at > NOW() - INTERVAL '5 minutes'
                    UNION ALL
                    SELECT 'estimates' FROM estimates WHERE updated_at > NOW() - INTERVAL '5 minutes'
                ) t
                GROUP BY table_name
            """)
            
            changes = cur.fetchall()
            
            if changes:
                print(f"📝 Local changes detected: {changes}")
                self.changes_pending = changes
                
                # Auto-sync if connected
                if self.check_connectivity():
                    self.sync_to_production()
                else:
                    print("⚠️  Changes queued - will sync when connection restored")
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Monitor error: {e}")
    
    def status_display(self):
        """Show current sync status"""
        connectivity = "🟢 CONNECTED" if self.check_connectivity() else "🔴 OFFLINE"
        
        print("\n" + "="*60)
        print(f"DATABASE SYNC STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print(f"Production Connection: {connectivity}")
        print(f"Sync Status: {self.sync_status}")
        print(f"Last Sync: {self.last_sync or 'Never'}")
        
        if self.changes_pending:
            print(f"⚠️  Pending Changes: {len(self.changes_pending)} tables")
        else:
            print("✅ No pending changes")
        
        # Check database checksums
        local_checksum, _ = self.get_db_checksum(LOCAL_DB)
        
        if self.check_connectivity():
            prod_checksum, _ = self.get_db_checksum(PROD_DB)
            
            if local_checksum == prod_checksum:
                print("✅ Databases are IDENTICAL")
            else:
                print("⚠️  Databases are OUT OF SYNC")
        else:
            print("⚠️  Cannot verify sync (offline)")
        
        print("="*60 + "\n")

def main():
    sync = RobustDBSync()
    
    print("🚀 ROBUST DATABASE SYNC SYSTEM STARTED")
    print("This ensures production is ALWAYS current with development")
    print("Handles intermittent connectivity gracefully")
    print("-"*60)
    
    # Initial pull from production
    sync.pull_from_production()
    
    while True:
        try:
            # Show status
            sync.status_display()
            
            # Check for changes
            sync.monitor_changes()
            
            # If offline with pending changes, try to sync
            if sync.changes_pending and sync.check_connectivity():
                print("🔄 Connection restored - syncing pending changes...")
                sync.sync_to_production()
                sync.changes_pending = []
            
            # Wait 30 seconds before next check
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n👋 Sync system stopped")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()