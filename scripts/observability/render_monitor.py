#!/usr/bin/env python3
"""
Render Deployment Monitor - Real-time visibility into deployments
Provides transparency for debugging deployment issues
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# Render API configuration
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx")
RENDER_SERVICE_ID = "srv-d1tfs4idbo4c73di6k00"
RENDER_API_BASE = "https://api.render.com/v1"

# API endpoint for our backend
BACKEND_URL = "https://brainops-backend-prod.onrender.com"

class RenderMonitor:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {RENDER_API_KEY}",
            "Accept": "application/json"
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service details"""
        url = f"{RENDER_API_BASE}/services/{RENDER_SERVICE_ID}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None
    
    def get_latest_deploy(self) -> Dict[str, Any]:
        """Get latest deployment info"""
        url = f"{RENDER_API_BASE}/services/{RENDER_SERVICE_ID}/deploys?limit=1"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            deploys = response.json()
            if deploys:
                return deploys[0]["deploy"]
        return None
    
    def get_deploy_logs(self, deploy_id: str, tail: int = 100) -> str:
        """Get deployment logs"""
        # Note: Render API doesn't provide direct log access via REST
        # We'd need to use WebSocket for real-time logs
        # For now, we'll check deployment status
        url = f"{RENDER_API_BASE}/services/{RENDER_SERVICE_ID}/deploys/{deploy_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return json.dumps(response.json(), indent=2)
        return "Unable to fetch logs"
    
    def check_backend_health(self) -> Dict[str, Any]:
        """Check if backend is responding"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            return {"error": str(e)}
        return {"error": "Backend not responding"}
    
    def check_revenue_routes(self) -> Dict[str, Any]:
        """Test if revenue routes are accessible"""
        routes_to_test = [
            "/api/v1/test-revenue/",
            "/api/v1/ai-estimation/competitor-analysis",
            "/api/v1/stripe-revenue/dashboard-metrics",
            "/api/v1/customer-pipeline/lead-analytics",
            "/api/v1/landing-pages/estimate-now",
            "/api/v1/google-ads/campaigns",
            "/api/v1/revenue-dashboard/dashboard-metrics"
        ]
        
        results = {}
        for route in routes_to_test:
            try:
                if "competitor-analysis" in route:
                    # POST endpoint
                    response = requests.post(
                        f"{BACKEND_URL}{route}",
                        json={"zip_code": "80202", "service_type": "test"},
                        timeout=3
                    )
                else:
                    # GET endpoint
                    response = requests.get(f"{BACKEND_URL}{route}", timeout=3)
                
                results[route] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code != 404
                }
            except Exception as e:
                results[route] = {
                    "status_code": 0,
                    "accessible": False,
                    "error": str(e)
                }
        
        return results
    
    def monitor_deployment(self):
        """Main monitoring function"""
        print("=" * 60)
        print("RENDER DEPLOYMENT MONITOR")
        print("=" * 60)
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print()
        
        # Check service info
        print("📦 SERVICE STATUS:")
        service = self.get_service_info()
        if service:
            print(f"  Name: {service.get('name')}")
            print(f"  Status: {service.get('status', 'unknown')}")
            print(f"  URL: {service.get('serviceDetails', {}).get('url')}")
            print(f"  SSH: {service.get('serviceDetails', {}).get('sshAddress')}")
        else:
            print("  ❌ Unable to fetch service info")
        print()
        
        # Check latest deployment
        print("🚀 LATEST DEPLOYMENT:")
        deploy = self.get_latest_deploy()
        if deploy:
            print(f"  ID: {deploy.get('id')}")
            print(f"  Status: {deploy.get('status')}")
            print(f"  Trigger: {deploy.get('trigger')}")
            print(f"  Started: {deploy.get('startedAt')}")
            print(f"  Finished: {deploy.get('finishedAt')}")
            if deploy.get('image'):
                print(f"  Image: {deploy['image'].get('ref')}")
                print(f"  SHA: {deploy['image'].get('sha', '')[:12]}...")
        else:
            print("  ❌ Unable to fetch deployment info")
        print()
        
        # Check backend health
        print("❤️ BACKEND HEALTH:")
        health = self.check_backend_health()
        if "error" not in health:
            print(f"  Status: {health.get('status')}")
            print(f"  Version: {health.get('version')}")
            print(f"  Database: {health.get('database')}")
            features = health.get('features', {})
            if features:
                print("  Features:")
                for feature, enabled in features.items():
                    status = "✅" if enabled else "❌"
                    print(f"    {status} {feature}")
        else:
            print(f"  ❌ Error: {health['error']}")
        print()
        
        # Check revenue routes
        print("💰 REVENUE ROUTES STATUS:")
        routes = self.check_revenue_routes()
        working_count = 0
        for route, result in routes.items():
            if result['accessible']:
                working_count += 1
                status = "✅"
            else:
                status = "❌"
            print(f"  {status} {route}: {result['status_code']}")
        
        print()
        print(f"Summary: {working_count}/{len(routes)} revenue routes accessible")
        print()
        
        # Recommendations
        print("📋 RECOMMENDATIONS:")
        if working_count == 0:
            print("  1. Routes not loading - check main.py imports")
            print("  2. SSH into container: ssh srv-d1tfs4idbo4c73di6k00@ssh.oregon.render.com")
            print("  3. Check logs: render logs srv-d1tfs4idbo4c73di6k00 --tail")
            print("  4. Verify Docker image contains revenue routes")
            print("  5. Check for import errors in production environment")
        elif working_count < len(routes):
            print("  1. Some routes working - partial deployment issue")
            print("  2. Check specific route registration in main.py")
            print("  3. Verify all dependencies installed in Docker image")
        else:
            print("  ✅ All revenue routes operational!")
        
        print("=" * 60)

if __name__ == "__main__":
    monitor = RenderMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        # Continuous monitoring mode
        while True:
            os.system('clear')
            monitor.monitor_deployment()
            print("\nRefreshing in 30 seconds... (Ctrl+C to stop)")
            time.sleep(30)
    else:
        # Single run
        monitor.monitor_deployment()