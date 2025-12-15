#!/usr/bin/env python3
"""
Complete System Test - No Assumptions, Production Only
Tests every component of the BrainOps ecosystem
"""

import requests
import json
import subprocess
from datetime import datetime
import time

class SystemTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "backend": {},
            "frontend": {},
            "database": {},
            "ai_system": {},
            "automations": {},
            "deployments": {}
        }
        
    def test_backend(self):
        """Test backend API thoroughly"""
        print("\n🔍 TESTING BACKEND API...")
        
        # Health check
        try:
            r = requests.get("https://brainops-backend-prod.onrender.com/api/v1/health", timeout=5)
            health = r.json()
            self.results["backend"]["health"] = {
                "status": health.get("status"),
                "version": health.get("version"),
                "loaded_routers": health.get("loaded_routers"),
                "operational": health.get("operational")
            }
            print(f"  Version: {health.get('version')} - {health.get('status')}")
        except Exception as e:
            self.results["backend"]["health"] = {"error": str(e)}
            print(f"  ❌ Health check failed: {e}")
        
        # Test key endpoints
        endpoints = [
            ("/api/v1/ai/status", "AI Status"),
            ("/api/v1/aurea/status", "AUREA Status"),
            ("/api/v1/products", "Products"),
            ("/api/v1/auth/test", "Auth Test"),
            ("/api/v1/revenue/status", "Revenue Status"),
            ("/api/v1/task-os/status", "Task OS Status"),
            ("/api/v1/crm/customers", "CRM Customers"),
            ("/docs", "API Documentation")
        ]
        
        for endpoint, name in endpoints:
            try:
                r = requests.get(f"https://brainops-backend-prod.onrender.com{endpoint}", timeout=3)
                self.results["backend"][endpoint] = {
                    "name": name,
                    "status_code": r.status_code,
                    "available": r.status_code in [200, 401, 422]  # 401/422 means endpoint exists
                }
                status = "✅" if r.status_code in [200, 401, 422] else "❌"
                print(f"  {status} {name}: {r.status_code}")
            except Exception as e:
                self.results["backend"][endpoint] = {"name": name, "error": str(e)}
                print(f"  ❌ {name}: Failed")
    
    def test_frontend(self):
        """Test all frontend applications"""
        print("\n🌐 TESTING FRONTEND APPS...")
        
        apps = [
            ("https://myroofgenius.com", "MyRoofGenius"),
            ("https://brainops-task-os.vercel.app", "BrainOps Task OS"),
            ("https://weathercraft-app.vercel.app", "WeatherCraft App"),
            ("https://weathercraft-erp.vercel.app", "WeatherCraft ERP"),
            ("https://brainops-aios-ops.vercel.app", "BrainOps AIOS")
        ]
        
        for url, name in apps:
            try:
                r = requests.get(url, timeout=5, allow_redirects=True)
                self.results["frontend"][name] = {
                    "url": url,
                    "status_code": r.status_code,
                    "live": r.status_code == 200,
                    "final_url": r.url
                }
                status = "✅" if r.status_code == 200 else "⚠️"
                print(f"  {status} {name}: {r.status_code} -> {r.url}")
            except Exception as e:
                self.results["frontend"][name] = {"url": url, "error": str(e)}
                print(f"  ❌ {name}: Failed")
    
    def test_database(self):
        """Test database connectivity and data"""
        print("\n💾 TESTING DATABASE...")
        
        # Use psql to check data
        cmd = """export PGPASSWORD='<DB_PASSWORD_REDACTED>' && psql -h aws-0-us-east-2.pooler.supabase.com -p 6543 -U postgres.yomagoqdmxszqtdwuhab -d postgres -t -c "
        SELECT 
            'customers' as table_name, COUNT(*) as count FROM customers
        UNION ALL
        SELECT 'jobs', COUNT(*) FROM jobs
        UNION ALL
        SELECT 'products', COUNT(*) FROM products
        UNION ALL
        SELECT 'invoices', COUNT(*) FROM invoices
        UNION ALL
        SELECT 'users', COUNT(*) FROM users;" 2>/dev/null"""
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if '|' in line:
                        parts = line.split('|')
                        table = parts[0].strip()
                        count = int(parts[1].strip())
                        self.results["database"][table] = count
                        status = "✅" if count > 0 else "⚠️"
                        print(f"  {status} {table}: {count} records")
            else:
                self.results["database"]["error"] = "Connection failed"
                print(f"  ❌ Database connection failed")
        except Exception as e:
            self.results["database"]["error"] = str(e)
            print(f"  ❌ Database test failed: {e}")
    
    def test_ai_system(self):
        """Test AI and automation systems"""
        print("\n🤖 TESTING AI SYSTEMS...")
        
        # Test AI endpoints
        base_url = "https://brainops-backend-prod.onrender.com"
        
        # Check AI status
        try:
            r = requests.get(f"{base_url}/api/v1/ai/status", timeout=5)
            if r.status_code == 200:
                ai_data = r.json()
                self.results["ai_system"]["status"] = ai_data
                print(f"  ✅ AI Status: {ai_data.get('status')}")
                print(f"     Capabilities: {len(ai_data.get('capabilities', []))}")
                print(f"     Agents: {len(ai_data.get('agents', []))}")
            else:
                self.results["ai_system"]["status"] = {"error": f"Status {r.status_code}"}
                print(f"  ❌ AI Status: {r.status_code}")
        except Exception as e:
            self.results["ai_system"]["status"] = {"error": str(e)}
            print(f"  ❌ AI Status check failed: {e}")
        
        # Test new LangGraph endpoints (v4.33)
        langgraph_endpoints = [
            "/api/v1/ai/agents",
            "/api/v1/ai/workflows",
            "/api/v1/ai/test"
        ]
        
        for endpoint in langgraph_endpoints:
            try:
                r = requests.get(f"{base_url}{endpoint}", timeout=3)
                available = r.status_code in [200, 404]  # 404 means not deployed yet
                self.results["ai_system"][endpoint] = {
                    "status_code": r.status_code,
                    "available": r.status_code == 200
                }
                status = "✅" if r.status_code == 200 else "⚠️"
                print(f"  {status} {endpoint}: {r.status_code}")
            except:
                self.results["ai_system"][endpoint] = {"available": False}
                print(f"  ❌ {endpoint}: Not available")
    
    def test_deployments(self):
        """Check deployment status"""
        print("\n🚀 CHECKING DEPLOYMENTS...")
        
        # Check Render deployment
        try:
            headers = {"Authorization": "Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"}
            r = requests.get(
                "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys?limit=1",
                headers=headers,
                timeout=5
            )
            if r.status_code == 200:
                deploy = r.json()[0]["deploy"]
                self.results["deployments"]["render"] = {
                    "status": deploy.get("status"),
                    "image": deploy.get("image", {}).get("ref"),
                    "trigger": deploy.get("trigger"),
                    "created": deploy.get("createdAt")
                }
                print(f"  Render: {deploy.get('status')} - {deploy.get('image', {}).get('ref', 'unknown')}")
            else:
                print(f"  ❌ Render API: {r.status_code}")
        except Exception as e:
            print(f"  ❌ Render check failed: {e}")
        
        # Check Docker Hub
        try:
            r = requests.get("https://hub.docker.com/v2/repositories/mwwoodworth/brainops-backend/tags/v4.33", timeout=5)
            if r.status_code == 200:
                self.results["deployments"]["docker_v433"] = True
                print(f"  ✅ Docker v4.33: Available on Docker Hub")
            else:
                self.results["deployments"]["docker_v433"] = False
                print(f"  ❌ Docker v4.33: Not found")
        except:
            print(f"  ⚠️ Docker Hub check failed")
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "="*60)
        print("📊 COMPLETE SYSTEM STATUS REPORT")
        print("="*60)
        
        # Backend Summary
        backend_version = self.results["backend"].get("health", {}).get("version", "Unknown")
        backend_status = self.results["backend"].get("health", {}).get("status", "Unknown")
        print(f"\n🔧 BACKEND:")
        print(f"  Version: {backend_version}")
        print(f"  Status: {backend_status}")
        print(f"  Routers Loaded: {self.results['backend'].get('health', {}).get('loaded_routers', 0)}")
        
        # Count working endpoints
        working_endpoints = sum(1 for k, v in self.results["backend"].items() 
                               if isinstance(v, dict) and v.get("available", False))
        total_endpoints = len([k for k in self.results["backend"] if k != "health"])
        print(f"  Working Endpoints: {working_endpoints}/{total_endpoints}")
        
        # Frontend Summary
        print(f"\n🌐 FRONTEND APPS:")
        for app, data in self.results["frontend"].items():
            if isinstance(data, dict):
                status = "✅ LIVE" if data.get("live") else "❌ DOWN"
                print(f"  {app}: {status}")
        
        # Database Summary
        print(f"\n💾 DATABASE:")
        total_records = 0
        for table, count in self.results["database"].items():
            if isinstance(count, int):
                total_records += count
                print(f"  {table}: {count} records")
        print(f"  Total Records: {total_records}")
        
        # AI System Summary
        print(f"\n🤖 AI SYSTEM:")
        ai_status = self.results["ai_system"].get("status", {})
        if isinstance(ai_status, dict) and "status" in ai_status:
            print(f"  Status: {ai_status.get('status')}")
            print(f"  Capabilities: {len(ai_status.get('capabilities', []))}")
            print(f"  Agents: {len(ai_status.get('agents', []))}")
        
        # Check v4.33 features
        v433_available = any(
            self.results["ai_system"].get(ep, {}).get("available", False)
            for ep in ["/api/v1/ai/agents", "/api/v1/ai/workflows", "/api/v1/ai/test"]
        )
        print(f"  v4.33 Features: {'✅ Available' if v433_available else '⚠️ Not deployed yet'}")
        
        # Deployment Status
        print(f"\n🚀 DEPLOYMENTS:")
        render_status = self.results["deployments"].get("render", {}).get("status", "Unknown")
        print(f"  Render: {render_status}")
        print(f"  Docker v4.33: {'✅ Published' if self.results['deployments'].get('docker_v433') else '❌ Not found'}")
        
        # Overall System Health
        print("\n" + "="*60)
        print("🎯 OVERALL SYSTEM STATUS")
        print("="*60)
        
        # Calculate health score
        health_score = 0
        max_score = 100
        
        # Backend (30 points)
        if backend_status == "healthy":
            health_score += 20
        if working_endpoints > 5:
            health_score += 10
        
        # Frontend (20 points)
        live_apps = sum(1 for v in self.results["frontend"].values() 
                       if isinstance(v, dict) and v.get("live"))
        health_score += (live_apps / len(self.results["frontend"])) * 20
        
        # Database (20 points)
        if total_records > 0:
            health_score += 10
        if total_records > 100:
            health_score += 10
        
        # AI System (20 points)
        if ai_status.get("status") == "operational":
            health_score += 10
        if v433_available:
            health_score += 10
        
        # Deployment (10 points)
        if render_status in ["live", "update_in_progress"]:
            health_score += 10
        
        print(f"\n🏆 SYSTEM HEALTH SCORE: {health_score:.0f}/100")
        
        if health_score >= 90:
            print("✅ System is FULLY OPERATIONAL")
        elif health_score >= 70:
            print("⚠️ System is PARTIALLY OPERATIONAL")
        elif health_score >= 50:
            print("⚠️ System has SIGNIFICANT ISSUES")
        else:
            print("❌ System is CRITICALLY IMPAIRED")
        
        # Critical Issues
        print("\n⚠️ CRITICAL ISSUES FOUND:")
        issues = []
        
        if backend_version != "4.33":
            issues.append(f"Backend running v{backend_version}, not v4.33")
        
        if total_records == 0:
            issues.append("Database is completely empty - no customer data")
        
        if not v433_available:
            issues.append("v4.33 AI features not deployed yet")
        
        weathercraft_down = not self.results["frontend"].get("WeatherCraft App", {}).get("live")
        if weathercraft_down:
            issues.append("WeatherCraft App is down (404)")
        
        if issues:
            for issue in issues:
                print(f"  • {issue}")
        else:
            print("  None - all systems operational")
        
        # Save detailed report
        report_file = f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return health_score

def main():
    print("🔍 COMPLETE SYSTEM TEST - NO ASSUMPTIONS")
    print("Testing all production systems...")
    print("="*60)
    
    tester = SystemTester()
    
    # Run all tests
    tester.test_backend()
    tester.test_frontend()
    tester.test_database()
    tester.test_ai_system()
    tester.test_deployments()
    
    # Generate report
    health_score = tester.generate_report()
    
    # Return status
    return 0 if health_score >= 70 else 1

if __name__ == "__main__":
    exit(main())