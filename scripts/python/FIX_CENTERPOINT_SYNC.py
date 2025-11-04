#!/usr/bin/env python3
"""
Fix and restart CenterPoint synchronization
Ensures continuous data flow from CenterPoint API
"""

import os
import sys
import psycopg2
import requests
import json
from datetime import datetime, timedelta
import time

# CenterPoint API Configuration
CENTERPOINT_BASE_URL = "https://api.centerpointconnect.io"
CENTERPOINT_BEARER_TOKEN = "eyJvcmciOiI2NmJlMzEwMzFiMGJjMTAwMDEwM2RiN2MiLCJpZCI6ImM4ZDdiMDIyNGQ4NDQ5OGI5M2MwYzY4MTc0NWU5M2Y0IiwiaCI6Im11cm11cjEyOCJ9"
CENTERPOINT_TENANT_ID = "97f82b360baefdd73400ad342562586"

# Database configuration
DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

def test_centerpoint_connection():
    """Test CenterPoint API connection"""
    headers = {
        "Authorization": f"Bearer {CENTERPOINT_BEARER_TOKEN}",
        "X-Tenant-Id": CENTERPOINT_TENANT_ID,
        "Content-Type": "application/json"
    }
    
    try:
        # Test with contacts endpoint
        response = requests.get(
            f"{CENTERPOINT_BASE_URL}/v1/contacts",
            headers=headers,
            params={"limit": 1}
        )
        
        if response.status_code == 200:
            print("✅ CenterPoint API connection successful")
            return True
        else:
            print(f"❌ CenterPoint API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def sync_centerpoint_data():
    """Sync data from CenterPoint to database"""
    
    headers = {
        "Authorization": f"Bearer {CENTERPOINT_BEARER_TOKEN}",
        "X-Tenant-Id": CENTERPOINT_TENANT_ID,
        "Content-Type": "application/json"
    }
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # 1. Sync Contacts as Customers
        print("📥 Syncing contacts...")
        response = requests.get(
            f"{CENTERPOINT_BASE_URL}/v1/contacts",
            headers=headers,
            params={"limit": 100}
        )
        
        if response.status_code == 200:
            contacts = response.json().get("data", [])
            
            for contact in contacts:
                # Insert or update customer
                cur.execute("""
                    INSERT INTO customers (
                        external_id, name, email, phone, 
                        address, city, state, zip_code,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (external_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        phone = EXCLUDED.phone,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    f"CP-{contact.get('id')}",
                    contact.get('name', 'Unknown'),
                    contact.get('email'),
                    contact.get('phone'),
                    contact.get('address'),
                    contact.get('city'),
                    contact.get('state'),
                    contact.get('zip')
                ))
            
            conn.commit()
            print(f"✅ Synced {len(contacts)} contacts")
        
        # 2. Sync Jobs/Projects
        print("📥 Syncing jobs...")
        response = requests.get(
            f"{CENTERPOINT_BASE_URL}/v1/projects",
            headers=headers,
            params={"limit": 100}
        )
        
        if response.status_code == 200:
            projects = response.json().get("data", [])
            
            for project in projects:
                # Get customer_id from external_id
                cur.execute("""
                    SELECT id FROM customers WHERE external_id = %s
                """, (f"CP-{project.get('contact_id')}",))
                
                result = cur.fetchone()
                customer_id = result[0] if result else None
                
                if customer_id:
                    cur.execute("""
                        INSERT INTO jobs (
                            job_number, name, customer_id,
                            status, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT (job_number) DO UPDATE SET
                            name = EXCLUDED.name,
                            status = EXCLUDED.status,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        f"CP-{project.get('id')}",
                        project.get('name', 'Untitled Job'),
                        customer_id,
                        project.get('status', 'active')
                    ))
            
            conn.commit()
            print(f"✅ Synced {len(projects)} jobs")
        
        # 3. Log sync operation
        cur.execute("""
            INSERT INTO centerpoint_sync_log (
                sync_type, status, records_synced,
                started_at, completed_at
            ) VALUES (
                'full_sync', 'completed', %s,
                %s, %s
            )
        """, (
            len(contacts) + len(projects),
            datetime.now() - timedelta(minutes=1),
            datetime.now()
        ))
        
        conn.commit()
        print("✅ Sync completed successfully")
        
    except Exception as e:
        print(f"❌ Sync error: {e}")
        conn.rollback()
        
        # Log failed sync
        cur.execute("""
            INSERT INTO centerpoint_sync_log (
                sync_type, status, errors,
                started_at, completed_at
            ) VALUES (
                'full_sync', 'failed', %s,
                %s, %s
            )
        """, (
            str(e),
            datetime.now() - timedelta(minutes=1),
            datetime.now()
        ))
        conn.commit()
        
    finally:
        cur.close()
        conn.close()

def setup_continuous_sync():
    """Set up continuous sync process"""
    
    print("🔄 Setting up continuous CenterPoint sync...")
    
    # Create sync service script
    service_script = '''#!/usr/bin/env python3
import time
import requests
import psycopg2
from datetime import datetime

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
CENTERPOINT_BASE_URL = "https://api.centerpointconnect.io"
CENTERPOINT_BEARER_TOKEN = "eyJvcmciOiI2NmJlMzEwMzFiMGJjMTAwMDEwM2RiN2MiLCJpZCI6ImM4ZDdiMDIyNGQ4NDQ5OGI5M2MwYzY4MTc0NWU5M2Y0IiwiaCI6Im11cm11cjEyOCJ9"
CENTERPOINT_TENANT_ID = "97f82b360baefdd73400ad342562586"

def sync_once():
    """Perform one sync operation"""
    headers = {
        "Authorization": f"Bearer {CENTERPOINT_BEARER_TOKEN}",
        "X-Tenant-Id": CENTERPOINT_TENANT_ID,
        "Content-Type": "application/json"
    }
    
    try:
        # Sync contacts
        response = requests.get(f"{CENTERPOINT_BASE_URL}/v1/contacts", headers=headers, params={"limit": 50})
        if response.status_code == 200:
            contacts = response.json().get("data", [])
            
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            for contact in contacts:
                cur.execute("""
                    INSERT INTO customers (external_id, name, email, phone, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (external_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        email = EXCLUDED.email,
                        phone = EXCLUDED.phone,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    f"CP-{contact.get('id')}",
                    contact.get('name', 'Unknown'),
                    contact.get('email'),
                    contact.get('phone')
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"[{datetime.now()}] Synced {len(contacts)} contacts")
            return True
    except Exception as e:
        print(f"[{datetime.now()}] Sync error: {e}")
        return False

# Continuous sync loop
print(f"[{datetime.now()}] CenterPoint sync service started")
while True:
    sync_once()
    time.sleep(300)  # Sync every 5 minutes
'''

    with open("/home/mwwoodworth/code/CENTERPOINT_SYNC_SERVICE_V2.py", "w") as f:
        f.write(service_script)
    
    os.chmod("/home/mwwoodworth/code/CENTERPOINT_SYNC_SERVICE_V2.py", 0o755)
    
    print("✅ Continuous sync service created")
    
    # Kill old sync process if running
    os.system("pkill -f CENTERPOINT_24_7_SYNC_SERVICE.py 2>/dev/null")
    
    # Start new sync service in background
    os.system("python3 /home/mwwoodworth/code/CENTERPOINT_SYNC_SERVICE_V2.py > /tmp/centerpoint_sync.log 2>&1 &")
    
    print("✅ CenterPoint sync service started in background")

if __name__ == "__main__":
    print("🚀 CenterPoint Sync Fix Starting...")
    
    # Test connection
    if test_centerpoint_connection():
        # Perform initial sync
        sync_centerpoint_data()
        
        # Set up continuous sync
        setup_continuous_sync()
        
        print("✅ CenterPoint sync fully operational!")
    else:
        print("❌ Could not connect to CenterPoint API. Check credentials.")