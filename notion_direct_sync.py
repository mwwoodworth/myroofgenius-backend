#!/usr/bin/env python3
"""
Direct Notion Database Sync - Populates existing databases
"""

import os
import psycopg2
import logging
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import requests
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Validate required environment variables
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
if not NOTION_TOKEN:
    raise RuntimeError("NOTION_TOKEN environment variable is required")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

if not all([DB_HOST, DB_USER, DB_PASSWORD]):
    raise RuntimeError("DB_HOST, DB_USER, and DB_PASSWORD environment variables are required")


class DirectNotionSync:
    def __init__(self):
        self.notion_token = NOTION_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.base_url = "https://api.notion.com/v1"

        # Database configuration from environment variables
        self.db_config = {
            "host": DB_HOST,
            "database": DB_NAME or "postgres",
            "user": DB_USER,
            "password": DB_PASSWORD,
            "port": int(DB_PORT) if DB_PORT else 5432
        }
        
        # Your database IDs from the URLs
        self.databases = {
            "customers": "1e9e33af7eb480a2aa14d3deccfe8b70",
            "jobs": "1e9e33af7eb48086ac76d62564699a94",
            "inventory": "1f3e33af7eb48009b303fd0fde3c1e5c"
        }
        
    def test_database_access(self):
        """Test if we can access the databases"""
        print("\n🔍 Testing Notion database access...")
        for name, db_id in self.databases.items():
            try:
                response = requests.get(
                    f"{self.base_url}/databases/{db_id}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    print(f"  ✅ {name}: Accessible")
                else:
                    print(f"  ❌ {name}: {response.status_code} - {response.json().get('message', 'Unknown error')}")
            except Exception as e:
                print(f"  ❌ {name}: {str(e)}")
                
    def connect_db(self):
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return None
            
    def sync_customers(self):
        """Sync customer data to Notion"""
        print("\n📊 Syncing Customers...")
        conn = self.connect_db()
        if not conn:
            return
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT
                    id, name, email, phone, company_name,
                    address, city, state, zip, created_at
                FROM customers
                WHERE name IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 20
            """)
            
            customers = cursor.fetchall()
            print(f"  Found {len(customers)} customers to sync")
            
            success_count = 0
            for customer in customers[:5]:  # Sync first 5 as test
                try:
                    properties = {
                        "Name": {
                            "title": [{
                                "text": {
                                    "content": customer.get('name', 'Unknown')
                                }
                            }]
                        }
                    }
                    
                    # Add email if exists
                    if customer.get('email'):
                        properties["Email"] = {"email": customer['email']}
                    
                    # Add phone if exists  
                    if customer.get('phone'):
                        properties["Phone"] = {
                            "rich_text": [{
                                "text": {"content": customer['phone']}
                            }]
                        }
                    
                    response = requests.post(
                        f"{self.base_url}/pages",
                        headers=self.headers,
                        json={
                            "parent": {"database_id": self.databases['customers']},
                            "properties": properties
                        }
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                        print(f"    ✅ Synced: {customer.get('name')}")
                    else:
                        print(f"    ❌ Failed: {response.json().get('message', 'Unknown')}")
                        
                    time.sleep(0.3)  # Rate limiting
                    
                except Exception as e:
                    print(f"    ❌ Error syncing customer: {e}")
                    
            print(f"  ✅ Successfully synced {success_count} customers")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        finally:
            cursor.close()
            conn.close()
            
    def sync_jobs(self):
        """Sync jobs data to Notion"""
        print("\n🔧 Syncing Jobs...")
        conn = self.connect_db()
        if not conn:
            return
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT
                    j.id, j.job_number, j.status, j.description,
                    j.scheduled_date, j.total_amount,
                    c.name as customer_name
                FROM jobs j
                LEFT JOIN customers c ON j.customer_id = c.id
                ORDER BY j.created_at DESC
                LIMIT 20
            """)
            
            jobs = cursor.fetchall()
            print(f"  Found {len(jobs)} jobs to sync")
            
            success_count = 0
            for job in jobs[:5]:  # Sync first 5 as test
                try:
                    properties = {
                        "Name": {
                            "title": [{
                                "text": {
                                    "content": job.get('job_number', 'Unknown Job')
                                }
                            }]
                        }
                    }
                    
                    # Add customer name
                    if job.get('customer_name'):
                        properties["Customer"] = {
                            "rich_text": [{
                                "text": {
                                    "content": job.get('customer_name', '')
                                }
                            }]
                        }
                    
                    # Add status
                    if job.get('status'):
                        properties["Status"] = {
                            "rich_text": [{
                                "text": {"content": job['status']}
                            }]
                        }
                    
                    response = requests.post(
                        f"{self.base_url}/pages",
                        headers=self.headers,
                        json={
                            "parent": {"database_id": self.databases['jobs']},
                            "properties": properties
                        }
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                        print(f"    ✅ Synced: {job.get('job_number')}")
                    else:
                        print(f"    ❌ Failed: {response.json().get('message', 'Unknown')}")
                        
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"    ❌ Error syncing job: {e}")
                    
            print(f"  ✅ Successfully synced {success_count} jobs")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        finally:
            cursor.close()
            conn.close()
            
    def create_webhook_endpoint(self):
        """Create webhook endpoint for real-time sync"""
        print("\n🔄 Setting up webhook for real-time sync...")
        
        webhook_config = {
            "endpoint": "https://brainops-backend-prod.onrender.com/api/v1/webhooks/notion",
            "databases": self.databases,
            "sync_enabled": True,
            "events": ["insert", "update", "delete"]
        }
        
        print("  Webhook configuration:")
        print(json.dumps(webhook_config, indent=4))
        
        # Save webhook config
        with open('/home/matt-woodworth/fastapi-operator-env/notion_webhook_config.json', 'w') as f:
            json.dump(webhook_config, f, indent=2)
            
        print("  ✅ Webhook configuration saved")
        
    def get_stats(self):
        """Get database statistics"""
        conn = self.connect_db()
        if not conn:
            return {}
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        stats = {}
        
        try:
            tables = ['customers', 'jobs', 'invoices', 'estimates', 'inventory', 'ai_agents']
            for table in tables:
                try:
                    cursor.execute(sql.SQL("SELECT COUNT(*) as count FROM {}").format(sql.Identifier(table)))
                    result = cursor.fetchone()
                    stats[table] = result['count'] if result else 0
                except Exception as e:
                    logger.warning(f"Error querying {table}: {e}")
                    stats[table] = 0
                    
        finally:
            cursor.close()
            conn.close()
            
        return stats

def main():
    print("\n" + "="*60)
    print("  🚀 DIRECT NOTION DATABASE SYNC")
    print("="*60)
    print(f"Time: {datetime.now()}")
    print("="*60)
    
    sync = DirectNotionSync()
    
    # Test database access
    sync.test_database_access()
    
    # Get stats
    stats = sync.get_stats()
    print("\n📊 Database Statistics:")
    for table, count in stats.items():
        print(f"  • {table.capitalize()}: {count:,}")
    
    # Sync data
    sync.sync_customers()
    sync.sync_jobs()
    
    # Setup webhook
    sync.create_webhook_endpoint()
    
    print("\n" + "="*60)
    print("  ✅ SYNC COMPLETE!")
    print("="*60)
    print("\n📝 Next Steps:")
    print("  1. Check your Notion databases for synced data")
    print("  2. Configure webhook endpoint in backend")
    print("  3. Run full sync for remaining records")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
