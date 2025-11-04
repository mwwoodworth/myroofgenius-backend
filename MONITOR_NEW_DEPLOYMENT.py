#!/usr/bin/env python3
"""
Monitor New v9.16 Deployment
Deploy ID: dep-d2j6bhvdiees73brkimg
"""

import time
import requests
import json
from datetime import datetime

DEPLOY_ID = "dep-d2j6bhvdiees73brkimg"
HEALTH_URL = "https://brainops-backend-prod.onrender.com/api/v1/health"
TARGET_VERSION = "9.16"

def check_deployment():
    """Check if v9.16 is deployed"""
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current_version = data.get('version', 'unknown')
            return current_version, data
        else:
            return f"Error {response.status_code}", None
    except requests.RequestException as e:
        return f"Connection error: {e}", None
    except json.JSONDecodeError:
        return "Invalid JSON response", None

def main():
    print(f"""
    ╔════════════════════════════════════════════════════════╗
    ║          MONITORING v9.16 DEPLOYMENT                   ║
    ║          Deploy ID: {DEPLOY_ID}      ║
    ║          Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}           ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    max_checks = 20
    check_interval = 30  # seconds
    
    for i in range(1, max_checks + 1):
        print(f"\n🔍 Check {i}/{max_checks} at {datetime.now().strftime('%H:%M:%S')}...")
        
        version, data = check_deployment()
        
        if version == TARGET_VERSION:
            print(f"\n✅ SUCCESS! v{TARGET_VERSION} is LIVE!")
            print("="*60)
            print(json.dumps(data, indent=2))
            print("="*60)
            print("\n🎉 Deployment Complete!")
            
            # Store success in persistent memory
            import psycopg2
            DATABASE_URL = 'postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require'
            
            try:
                conn = psycopg2.connect(DATABASE_URL)
                cur = conn.cursor()
                
                deployment_data = {
                    'version': TARGET_VERSION,
                    'deploy_id': DEPLOY_ID,
                    'status': 'live',
                    'timestamp': datetime.now().isoformat(),
                    'health_response': data
                }
                
                cur.execute("""
                    INSERT INTO neural_os_knowledge 
                    (component_name, component_type, agent_name, knowledge_type, 
                     knowledge_data, confidence_score, review_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (component_name, knowledge_type, agent_name)
                    DO UPDATE SET 
                        knowledge_data = EXCLUDED.knowledge_data,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    f'Backend v{TARGET_VERSION} Live',
                    'deployment',
                    'DevOps Engineer',
                    'deployment_success',
                    json.dumps(deployment_data),
                    1.0,
                    f'v{TARGET_VERSION}_live'
                ))
                
                conn.commit()
                conn.close()
                print("✅ Deployment success stored in persistent memory!")
            except Exception as e:
                print(f"⚠️ Could not store in memory: {e}")
            
            return True
        else:
            print(f"   Current version: {version}")
            print(f"   Waiting for v{TARGET_VERSION}...")
        
        if i < max_checks:
            print(f"   Next check in {check_interval} seconds...")
            time.sleep(check_interval)
    
    print(f"\n⚠️ Deployment did not complete within {max_checks * check_interval // 60} minutes")
    print("Last status:")
    version, data = check_deployment()
    print(f"Version: {version}")
    if data:
        print(json.dumps(data, indent=2))
    
    return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)