#!/usr/bin/env python3
"""
Deployment Monitor for MyRoofGenius v3.1.159
Monitors the deployment progress and verifies all systems are operational
"""

import asyncio
import json
import time
from datetime import datetime
import httpx

API_URL = "https://brainops-backend-prod.onrender.com"

async def check_deployment_status():
    """Monitor deployment status until v3.1.159 is live"""
    
    print("🚀 MyRoofGenius v3.1.159 Deployment Monitor")
    print("=" * 60)
    print(f"Monitoring: {API_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        previous_version = None
        check_count = 0
        
        while True:
            check_count += 1
            try:
                # Check health endpoint
                response = await client.get(f"{API_URL}/api/v1/health")
                if response.status_code == 200:
                    data = response.json()
                    current_version = data.get("version", "unknown")
                    routes_loaded = data.get("routes_loaded", 0)
                    total_endpoints = data.get("total_endpoints", 0)
                    
                    # Print status update
                    print(f"\n[Check #{check_count}] {datetime.now().strftime('%H:%M:%S')}")
                    print(f"  Version: {current_version}")
                    print(f"  Routes Loaded: {routes_loaded}")
                    print(f"  Total Endpoints: {total_endpoints}")
                    print(f"  Status: {data.get('status', 'unknown')}")
                    
                    # Check for version change
                    if previous_version and previous_version != current_version:
                        print(f"\n🎉 VERSION CHANGED: {previous_version} → {current_version}")
                    
                    previous_version = current_version
                    
                    # Check if v3.1.159 is deployed
                    if current_version == "3.1.159":
                        print("\n✅ v3.1.159 SUCCESSFULLY DEPLOYED!")
                        
                        # Run quick verification
                        print("\nRunning verification checks...")
                        
                        # Check key endpoints
                        endpoints_to_check = [
                            "/api/v1/automations",
                            "/api/v1/marketplace/products",
                            "/api/v1/blog/posts",
                            "/api/v1/crm/dashboard",
                            "/api/v1/aurea/health",
                            "/api/v1/llm/status",
                            "/api/v1/agents/dashboard"
                        ]
                        
                        success_count = 0
                        for endpoint in endpoints_to_check:
                            try:
                                resp = await client.get(f"{API_URL}{endpoint}")
                                if resp.status_code in [200, 401, 403]:  # OK or needs auth
                                    print(f"  ✓ {endpoint}: {resp.status_code}")
                                    success_count += 1
                                else:
                                    print(f"  ✗ {endpoint}: {resp.status_code}")
                            except Exception as e:
                                print(f"  ✗ {endpoint}: {str(e)}")
                        
                        success_rate = (success_count / len(endpoints_to_check)) * 100
                        print(f"\nEndpoint Success Rate: {success_rate:.1f}%")
                        
                        if success_rate >= 80:
                            print("\n🎉 DEPLOYMENT VERIFIED - SYSTEM OPERATIONAL!")
                        else:
                            print("\n⚠️  Some endpoints not responding - check configuration")
                        
                        # Generate deployment summary
                        summary = {
                            "deployment_time": datetime.now().isoformat(),
                            "version": current_version,
                            "routes_loaded": routes_loaded,
                            "total_endpoints": total_endpoints,
                            "verification_success_rate": success_rate,
                            "status": "operational" if success_rate >= 80 else "partial"
                        }
                        
                        with open("deployment_summary_v3159.json", "w") as f:
                            json.dump(summary, f, indent=2)
                        
                        print(f"\n📄 Deployment summary saved to deployment_summary_v3159.json")
                        break
                    
                else:
                    print(f"\n[Check #{check_count}] Health check failed: {response.status_code}")
                    
            except Exception as e:
                print(f"\n[Check #{check_count}] Error: {str(e)}")
            
            # Wait before next check
            await asyncio.sleep(10)
            
            # Timeout after 30 minutes
            if check_count > 180:
                print("\n⏱️  Timeout: Deployment monitoring stopped after 30 minutes")
                break

if __name__ == "__main__":
    asyncio.run(check_deployment_status())
