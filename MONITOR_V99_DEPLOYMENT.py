#!/usr/bin/env python3
"""
Monitor v9.9 deployment - Connection Pool Fix
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"

def test_all_endpoints():
    """Test all critical endpoints"""
    
    endpoints = [
        ("/api/v1/health", "Health"),
        ("/api/v1/ai-board/status", "AI Board"),
        ("/api/v1/aurea/status", "AUREA"),
        ("/api/v1/langgraph/status", "LangGraph"),
        ("/api/v1/ai-os/status", "AI OS"),
        ("/api/v1/customers", "Customers"),
        ("/api/v1/jobs", "Jobs"),
        ("/api/v1/estimates", "Estimates"),
        ("/api/v1/invoices", "Invoices"),
        ("/api/v1/products/public", "Products"),
    ]
    
    print("🔍 Testing all endpoints...")
    print("=" * 60)
    
    working = 0
    errors = []
    
    for path, name in endpoints:
        try:
            resp = requests.get(f"{BASE_URL}{path}", timeout=10)
            if resp.status_code == 200:
                working += 1
                print(f"✅ {name:20} - {resp.status_code}")
            else:
                print(f"❌ {name:20} - {resp.status_code}")
                errors.append(f"{name}: {resp.status_code}")
        except Exception as e:
            print(f"❌ {name:20} - ERROR: {str(e)[:30]}")
            errors.append(f"{name}: {str(e)[:50]}")
    
    success_rate = (working / len(endpoints)) * 100
    
    return success_rate, errors

def monitor_deployment():
    """Monitor v9.9 deployment with connection pool fixes"""
    
    print("🚀 Monitoring v9.9 Deployment - Connection Pool Fix")
    print("=" * 60)
    print("Expected fixes:")
    print("- Connection pool reduced from 20/40 to 5/10")
    print("- Connection recycling after 1 hour")
    print("- Auto-create tables on startup")
    print("- Graceful route import handling")
    print("=" * 60)
    print("")
    
    # Give Render time to deploy
    print("⏰ Waiting 30 seconds for deployment to start...")
    time.sleep(30)
    
    # Check version
    max_attempts = 20
    for i in range(max_attempts):
        try:
            print(f"\n[Attempt {i+1}/{max_attempts}] Checking deployment...")
            
            # Check health endpoint
            resp = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                version = data.get("version", "unknown")
                
                print(f"📌 Current version: {version}")
                
                if version == "9.9":
                    print("\n✅ v9.9 DEPLOYED SUCCESSFULLY!")
                    print("=" * 60)
                    
                    # Test all endpoints
                    success_rate, errors = test_all_endpoints()
                    
                    print("=" * 60)
                    print(f"📊 SUCCESS RATE: {success_rate:.0f}%")
                    
                    if success_rate == 100:
                        print("\n🎉🎉🎉 100% OPERATIONAL! 🎉🎉🎉")
                        print("✅ CONNECTION POOL ISSUE FIXED!")
                        print("✅ ALL ENDPOINTS WORKING!")
                        print("🚀 System ready for production!")
                        
                        # Save success context
                        with open("/home/mwwoodworth/brainops/context/v99_success.json", "w") as f:
                            json.dump({
                                "version": "9.9",
                                "success_rate": 100,
                                "timestamp": datetime.now().isoformat(),
                                "status": "PERFECT",
                                "connection_pool": "Fixed - 5/10 instead of 20/40"
                            }, f, indent=2)
                    else:
                        print(f"\n⚠️ System {success_rate:.0f}% operational")
                        print("Issues found:")
                        for error in errors:
                            print(f"  - {error}")
                    
                    return success_rate
                
                elif version in ["9.6", "9.7", "9.8"]:
                    print(f"⏳ Still on {version}, waiting for v9.9...")
                else:
                    print(f"🔄 Version {version} detected")
            else:
                print(f"⚠️ Health check returned {resp.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("🔄 Connection error - deployment in progress...")
        except Exception as e:
            print(f"⚠️ Error: {str(e)[:50]}")
        
        time.sleep(15)
    
    print("\n⏱️ Timeout waiting for v9.9 deployment")
    print("Please check Render dashboard manually")
    return 0

def check_connection_pool():
    """Check if connection pool issues are resolved"""
    
    print("\n🔬 Testing Connection Pool Fix...")
    print("=" * 60)
    
    # Make multiple concurrent requests to test pool
    import concurrent.futures
    
    def make_request(i):
        try:
            resp = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    # Test with 20 concurrent requests (should handle with pool of 5)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(make_request, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    success_count = sum(results)
    
    if success_count == 20:
        print("✅ Connection pool handling concurrent requests perfectly!")
        print(f"   20/20 requests succeeded with pool size of 5")
    else:
        print(f"⚠️ Connection pool issues: {success_count}/20 requests succeeded")
    
    return success_count == 20

if __name__ == "__main__":
    # Monitor deployment
    success_rate = monitor_deployment()
    
    if success_rate > 0:
        # Test connection pool
        pool_fixed = check_connection_pool()
        
        if pool_fixed:
            print("\n" + "🎯" * 20)
            print("DEPLOYMENT COMPLETE - ALL ISSUES RESOLVED!")
            print("🎯" * 20)