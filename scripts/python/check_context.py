#!/usr/bin/env python3
"""
MANDATORY CONTEXT CHECKER
Run this at the start of EVERY session to verify system state
"""

import os
import psycopg2
import requests
import json
from datetime import datetime

# Database connection
DB_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

def check_database_context():
    """Verify actual database state"""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    print("\n=== DATABASE CONTEXT CHECK ===")
    
    # Check critical tables
    queries = [
        ("App Users", "SELECT COUNT(*) FROM app_users"),
        ("Customers", "SELECT COUNT(*) FROM customers"),
        ("Jobs", "SELECT COUNT(*) FROM jobs"),
        ("Invoices", "SELECT COUNT(*) FROM invoices"),
        ("Estimates", "SELECT COUNT(*) FROM estimates"),
        ("Automations", "SELECT COUNT(*) FROM automations"),
        ("AI Agents", "SELECT COUNT(*) FROM ai_agents"),
        ("System SOPs", "SELECT COUNT(*) FROM system_sops"),
    ]
    
    results = {}
    for name, query in queries:
        cur.execute(query)
        count = cur.fetchone()[0]
        results[name] = count
        print(f"{name}: {count}")
    
    # Check for discrepancies
    if results["App Users"] == 0:
        print("⚠️ WARNING: No app users! Authentication will fail!")
    if results["Customers"] > 100:
        print("⚠️ WARNING: More than expected customers. Did CenterPoint sync run?")
    if results["Invoices"] == 0:
        print("⚠️ WARNING: No invoices in database!")
    
    cur.close()
    conn.close()
    return results

def check_backend_status():
    """Verify backend API status"""
    print("\n=== BACKEND STATUS CHECK ===")
    
    try:
        response = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health")
        data = response.json()
        print(f"Version: {data.get('version', 'Unknown')}")
        print(f"Status: {data.get('status', 'Unknown')}")
        print(f"Operational: {data.get('operational', False)}")
        print(f"Loaded Routers: {data.get('loaded_routers', 0)}")
        
        if data.get('version') != 'v5.00':
            print(f"⚠️ WARNING: Backend is {data.get('version')}, not v5.00!")
        
        return data
    except Exception as e:
        print(f"❌ ERROR: Backend health check failed: {e}")
        return None

def check_critical_files():
    """Verify critical files exist"""
    print("\n=== CRITICAL FILES CHECK ===")
    
    files = [
        "/home/mwwoodworth/code/MasterDBBrainOps81725.md",
        "/home/mwwoodworth/code/OPERATIONAL_CONTEXT_REQUIREMENTS.md",
        "/home/mwwoodworth/code/fastapi-operator-env/Dockerfile",
        "/home/mwwoodworth/code/CLAUDE.md",
    ]
    
    for filepath in files:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {filepath} ({size:,} bytes)")
        else:
            print(f"❌ MISSING: {filepath}")

def update_context_sop(results):
    """Update the context SOP with current findings"""
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    context_data = {
        "timestamp": timestamp,
        "database": results,
        "checked_by": "check_context.py"
    }
    
    query = """
    UPDATE system_sops 
    SET steps = steps || %s::jsonb,
        updated_at = NOW()
    WHERE sop_id = 'operational-context-20250817'
    """
    
    cur.execute(query, [json.dumps([{"action": "Context verified", "data": context_data}])])
    conn.commit()
    
    print(f"\n✅ Context SOP updated at {timestamp}")
    
    cur.close()
    conn.close()

def main():
    print("=" * 60)
    print("MANDATORY OPERATIONAL CONTEXT CHECK")
    print("=" * 60)
    
    # Check database
    db_results = check_database_context()
    
    # Check backend
    backend_status = check_backend_status()
    
    # Check files
    check_critical_files()
    
    # Update SOP
    update_context_sop(db_results)
    
    print("\n" + "=" * 60)
    print("CONTEXT CHECK COMPLETE")
    print("Remember: NEVER trust assumptions, ALWAYS verify!")
    print("=" * 60)

if __name__ == "__main__":
    main()