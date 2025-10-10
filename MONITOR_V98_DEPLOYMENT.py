#!/usr/bin/env python3
"""
Monitor v9.8 deployment with DevOps context
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"
CONTEXT_FILE = "/home/mwwoodworth/brainops/context/deployment_v98.json"

def update_context(status, result=None):
    """Update deployment context"""
    try:
        with open(CONTEXT_FILE, 'r') as f:
            context = json.load(f)
        
        context["deployment"]["status"] = status
        context["deployment"]["last_check"] = datetime.now().isoformat()
        if result:
            context["deployment"]["result"] = result
        
        with open(CONTEXT_FILE, 'w') as f:
            json.dump(context, f, indent=2)
    except:
        pass

def monitor_deployment():
    """Monitor v9.8 deployment"""
    print("🚀 Monitoring v9.8 Deployment")
    print("=" * 60)
    print("Using local DevOps context for persistence")
    print("")
    
    # Monitor for 5 minutes
    start_time = time.time()
    timeout = 300
    
    while time.time() - start_time < timeout:
        try:
            # Check version
            resp = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
            data = resp.json()
            version = data.get("version", "unknown")
            status = data.get("status", "unknown")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Version: {version}, Status: {status}")
            
            if version == "9.8":
                print("\n✅ v9.8 DEPLOYED SUCCESSFULLY!\n")
                update_context("deployed", "success")
                
                # Test all endpoints
                print("Testing all endpoints...")
                endpoints = [
                    "/api/v1/health",
                    "/api/v1/ai-board/status",
                    "/api/v1/aurea/status",
                    "/api/v1/langgraph/status",
                    "/api/v1/ai-os/status",
                    "/api/v1/customers",
                    "/api/v1/jobs",
                    "/api/v1/estimates",
                    "/api/v1/invoices",
                    "/api/v1/products/public",
                ]
                
                working = 0
                for path in endpoints:
                    try:
                        r = requests.get(f"{BASE_URL}{path}", timeout=5)
                        if r.status_code == 200:
                            working += 1
                            print(f"✅ {path}")
                        else:
                            print(f"❌ {path}: {r.status_code}")
                    except:
                        print(f"❌ {path}: Error")
                
                success_rate = (working/len(endpoints))*100
                print(f"\n{'='*60}")
                print(f"SUCCESS RATE: {success_rate:.0f}%")
                print(f"{'='*60}")
                
                if success_rate == 100:
                    print("\n🎉🎉🎉 100% OPERATIONAL! 🎉🎉🎉")
                    print("✅ BACKEND IS NOW LOCKED IN!")
                    print("🚀 Ready to use DevOps AI agents!")
                    update_context("deployed", {"success_rate": 100, "status": "perfect"})
                else:
                    update_context("deployed", {"success_rate": success_rate, "status": "partial"})
                
                return success_rate
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking... {str(e)[:30]}")
        
        time.sleep(15)
    
    print("\n⏱️ Timeout waiting for v9.8")
    update_context("timeout")
    return 0

if __name__ == "__main__":
    rate = monitor_deployment()
    
    # Save final status
    print(f"\nFinal deployment status saved to: {CONTEXT_FILE}")
    print("This context persists across Claude sessions via local DevOps server")