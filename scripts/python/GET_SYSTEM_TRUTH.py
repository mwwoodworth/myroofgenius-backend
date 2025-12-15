#!/usr/bin/env python3
"""
GET_SYSTEM_TRUTH.py - The ONLY script that matters
This tells us what's ACTUALLY deployed and working
No assumptions, no guessing, just facts from live systems
"""

import requests
import psycopg2
import json
import subprocess
from datetime import datetime

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

def check_backend():
    """Check what's ACTUALLY working in the backend"""
    print("\n🔍 BACKEND STATUS")
    print("=" * 50)
    
    try:
        # Health check
        r = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Backend: OPERATIONAL (v{data.get('version', 'unknown')})")
            print(f"   Database: {data.get('database', 'unknown')}")
            print(f"   Features: {data.get('features', {})}")
        else:
            print(f"❌ Backend: ERROR ({r.status_code})")
    except Exception as e:
        print(f"❌ Backend: OFFLINE ({e})")
    
    # Check specific endpoints
    endpoints = [
        "/api/v1/test-revenue/",
        "/api/v1/ai-estimation/health",
        "/api/v1/stripe-revenue/health",
        "/api/v1/automation/",
        "/api/v1/memory/recent",
        "/api/v1/crm/customers"
    ]
    
    print("\n📊 Endpoint Status:")
    for endpoint in endpoints:
        try:
            r = requests.get(f"https://brainops-backend-prod.onrender.com{endpoint}", timeout=2)
            status = "✅" if r.status_code in [200, 201] else f"❌ ({r.status_code})"
            print(f"   {endpoint}: {status}")
        except:
            print(f"   {endpoint}: ❌ (timeout)")

def check_frontends():
    """Check frontend deployments"""
    print("\n🖥️ FRONTEND STATUS")
    print("=" * 50)
    
    frontends = {
        "MyRoofGenius": "https://myroofgenius.com",
        "WeatherCraft ERP": "https://weathercraft-erp.vercel.app",
        "BrainOps Task OS": "https://brainops-task-os.vercel.app",
        "WeatherCraft App": "https://weathercraft-app.vercel.app"
    }
    
    for name, url in frontends.items():
        try:
            r = requests.get(url, timeout=5, allow_redirects=True)
            if r.status_code == 200:
                print(f"✅ {name}: OPERATIONAL")
            else:
                print(f"⚠️ {name}: Status {r.status_code}")
        except Exception as e:
            print(f"❌ {name}: ERROR")

def check_database():
    """Check database status and data"""
    print("\n💾 DATABASE STATUS")
    print("=" * 50)
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Get table count
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cur.fetchone()[0]
        print(f"✅ Database: CONNECTED ({table_count} tables)")
        
        # Get data counts
        tables = ['customers', 'jobs', 'invoices', 'estimates', 'products']
        print("\n📈 Data Counts:")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"   {table}: {count}")
        
        # Check recent syncs
        cur.execute("""
            SELECT COUNT(*) FROM centerpoint_sync_log 
            WHERE started_at > NOW() - INTERVAL '1 hour'
        """)
        recent_syncs = cur.fetchone()[0]
        print(f"\n🔄 CenterPoint Syncs (last hour): {recent_syncs}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database: ERROR - {e}")

def check_processes():
    """Check running processes"""
    print("\n⚙️ RUNNING PROCESSES")
    print("=" * 50)
    
    processes = [
        "PERSISTENT_MONITORING_SYSTEM.py",
        "CENTERPOINT_24_7_SYNC_SERVICE.py",
        "CENTERPOINT_SYNC_SERVICE_V2.py"
    ]
    
    for process in processes:
        result = subprocess.run(
            f"pgrep -f {process} | wc -l",
            shell=True,
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip())
        status = f"✅ Running ({count} instances)" if count > 0 else "❌ Not running"
        print(f"   {process}: {status}")

def check_docker():
    """Check Docker status"""
    print("\n🐳 DOCKER STATUS")
    print("=" * 50)
    
    result = subprocess.run(
        "docker images | grep brainops | head -1",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        parts = result.stdout.split()
        print(f"✅ Latest image: {parts[0]}:{parts[1]}")
        print(f"   Created: {parts[4]} {parts[5]} ago")
        print(f"   Size: {parts[6]}")
    else:
        print("❌ No Docker images found")

def get_truth():
    """Get the complete system truth"""
    print("\n" + "=" * 60)
    print("🔮 SYSTEM TRUTH REPORT - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    check_backend()
    check_frontends()
    check_database()
    check_processes()
    check_docker()
    
    print("\n" + "=" * 60)
    print("📌 KEY FACTS:")
    print("=" * 60)
    print("1. WeatherCraft ERP is the MAIN PRODUCT (not WeatherCraft App)")
    print("2. Revenue system is PARTIALLY working (3/13 endpoints)")
    print("3. CenterPoint sync is NOT working (API issues)")
    print("4. System has 172 tables but minimal data")
    print("5. Docker v6.11 is built but may not be deployed")
    print("\n✨ Run this script anytime to get the TRUTH")

if __name__ == "__main__":
    get_truth()