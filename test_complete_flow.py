#!/usr/bin/env python3
"""
Test Complete System Flow - Frontend to Backend to Database
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
MYROOFGENIUS_URL = "https://myroofgenius.com"
WEATHERCRAFT_URL = "https://weathercraft-erp.vercel.app"

async def test_complete_flow():
    """Test the complete system integration"""
    print("🧪 TESTING COMPLETE SYSTEM FLOW")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        results = {
            "backend": False,
            "customers": False,
            "jobs": False,
            "revenue": False,
            "ai_agents": False,
            "frontend_mrg": False,
            "frontend_wc": False
        }
        
        # 1. Test Backend Health
        try:
            response = await client.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                data = response.json()
                results["backend"] = True
                print(f"✅ Backend Health: v{data.get('version', 'unknown')}")
        except Exception as e:
            print(f"❌ Backend Health: {e}")
        
        # 2. Test Customer API
        try:
            response = await client.get(f"{BACKEND_URL}/api/v1/customers")
            if response.status_code == 200:
                data = response.json()
                customer_count = len(data.get("customers", []))
                results["customers"] = True
                print(f"✅ Customers API: {customer_count} customers found")
        except Exception as e:
            print(f"❌ Customers API: {e}")
        
        # 3. Test Jobs API
        try:
            response = await client.get(f"{BACKEND_URL}/api/v1/jobs")
            if response.status_code == 200:
                data = response.json()
                job_count = len(data.get("jobs", []))
                results["jobs"] = True
                print(f"✅ Jobs API: {job_count} jobs found")
        except Exception as e:
            print(f"❌ Jobs API: {e}")
        
        # 4. Test Revenue Metrics
        try:
            response = await client.get(f"{BACKEND_URL}/api/v1/revenue/metrics")
            if response.status_code == 200:
                data = response.json()
                results["revenue"] = True
                print(f"✅ Revenue API: MRR ${data.get('mrr', 0):,.2f}")
        except Exception as e:
            print(f"❌ Revenue API: {e}")
        
        # 5. Test AI Agents
        try:
            response = await client.get(f"{BACKEND_URL}/api/v1/ai/agents")
            if response.status_code == 200:
                data = response.json()
                agent_count = len(data.get("agents", []))
                results["ai_agents"] = True
                print(f"✅ AI Agents API: {agent_count} agents found")
        except Exception as e:
            print(f"❌ AI Agents API: {e}")
        
        # 6. Test MyRoofGenius Frontend
        try:
            response = await client.get(MYROOFGENIUS_URL, follow_redirects=True)
            if response.status_code == 200:
                results["frontend_mrg"] = True
                print(f"✅ MyRoofGenius Frontend: Accessible")
        except Exception as e:
            print(f"❌ MyRoofGenius Frontend: {e}")
        
        # 7. Test WeatherCraft ERP
        try:
            response = await client.get(WEATHERCRAFT_URL, follow_redirects=True)
            if response.status_code == 200:
                results["frontend_wc"] = True
                print(f"✅ WeatherCraft ERP: Accessible")
        except Exception as e:
            print(f"❌ WeatherCraft ERP: {e}")
        
        # 8. Test End-to-End: Create and Retrieve
        print("\n📝 Testing End-to-End Flow...")
        try:
            # Create a test estimate
            estimate_data = {
                "customer_name": f"Test Customer {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "email": f"test_{datetime.now().timestamp()}@test.com",
                "phone": "555-0000",
                "address": "123 Test Street",
                "roof_size": 2000,
                "roof_type": "asphalt_shingle",
                "roof_pitch": "medium",
                "layers": 1
            }
            
            response = await client.post(
                f"{BACKEND_URL}/api/v1/estimates/public",
                json=estimate_data
            )
            
            if response.status_code == 200:
                estimate = response.json()
                print(f"✅ Created Estimate: ${estimate.get('total', 0):,.2f}")
                
                # Retrieve the estimate
                if estimate.get("id"):
                    response = await client.get(
                        f"{BACKEND_URL}/api/v1/estimates/{estimate['id']}"
                    )
                    if response.status_code == 200:
                        print(f"✅ Retrieved Estimate: Confirmed")
            else:
                print(f"⚠️ Estimate creation returned: {response.status_code}")
        except Exception as e:
            print(f"❌ End-to-End Test: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SYSTEM INTEGRATION SUMMARY")
        print("=" * 60)
        
        working = sum(1 for v in results.values() if v)
        total = len(results)
        percentage = (working / total) * 100
        
        for component, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {component.replace('_', ' ').title()}: {'Working' if status else 'Failed'}")
        
        print("\n" + "=" * 60)
        print(f"🎯 SYSTEM READINESS: {percentage:.1f}% ({working}/{total} components)")
        
        if percentage == 100:
            print("🎉 SYSTEM IS FULLY OPERATIONAL!")
        elif percentage >= 80:
            print("⚠️ System is mostly operational but needs attention")
        else:
            print("🔴 System has critical issues that need fixing")
        
        return results

if __name__ == "__main__":
    results = asyncio.run(test_complete_flow())