#!/usr/bin/env python3
"""
Production Deployment Verification Script
Tests all systems to ensure they are ACTUALLY operational
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Tuple

BACKEND_URL = "https://brainops-backend-prod.onrender.com"
MYROOFGENIUS_URL = "https://myroofgenius.com"
WEATHERCRAFT_URL = "https://weathercraft-erp.vercel.app"

class ProductionVerifier:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
        self.failures = []
        
    async def test_endpoint(self, name: str, url: str, expected_status: int = 200) -> bool:
        """Test a single endpoint"""
        try:
            response = await self.client.get(url)
            success = response.status_code == expected_status
            
            if success:
                self.results.append(f"✅ {name}: {response.status_code}")
            else:
                self.failures.append(f"❌ {name}: Expected {expected_status}, got {response.status_code}")
                
            return success
        except Exception as e:
            self.failures.append(f"❌ {name}: {str(e)}")
            return False
    
    async def test_post_endpoint(self, name: str, url: str, data: Dict, expected_status: int = 200) -> bool:
        """Test a POST endpoint"""
        try:
            response = await self.client.post(url, json=data)
            success = response.status_code == expected_status
            
            if success:
                self.results.append(f"✅ {name}: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
            else:
                self.failures.append(f"❌ {name}: Expected {expected_status}, got {response.status_code}")
                
            return success
        except Exception as e:
            self.failures.append(f"❌ {name}: {str(e)}")
            return False
    
    async def verify_backend(self):
        """Verify backend API is fully operational"""
        print("\n🔍 VERIFYING BACKEND API...")
        
        # Core endpoints
        await self.test_endpoint("Health Check", f"{BACKEND_URL}/api/v1/health")
        await self.test_endpoint("Root", f"{BACKEND_URL}/")
        
        # AI Agents
        await self.test_endpoint("AI Agents Status", f"{BACKEND_URL}/api/v1/ai-agents/status")
        await self.test_endpoint("AI Consciousness", f"{BACKEND_URL}/api/v1/ai-agents/consciousness")
        
        # Test agent actions
        marketing_result = await self.test_post_endpoint(
            "Marketing Campaign", 
            f"{BACKEND_URL}/api/v1/ai-agents/marketing/campaign",
            {"target": "storm_damage", "budget": 5000}
        )
        
        sales_result = await self.test_post_endpoint(
            "Sales Engagement",
            f"{BACKEND_URL}/api/v1/ai-agents/sales/engage",
            {"lead": {"name": "Test Lead", "requested_quote": True}}
        )
        
        # Persistent Memory
        await self.test_endpoint("Memory Status", f"{BACKEND_URL}/api/v1/persistent-memory/status")
        
        memory_store = await self.test_post_endpoint(
            "Store Memory",
            f"{BACKEND_URL}/api/v1/persistent-memory/store",
            {
                "category": "test",
                "content": {"test": "Production verification", "timestamp": datetime.utcnow().isoformat()},
                "importance": 0.8
            }
        )
        
        # AUREA
        await self.test_endpoint("AUREA Status", f"{BACKEND_URL}/api/v1/aurea/status")
        
        # LangGraph
        await self.test_endpoint("LangGraph Status", f"{BACKEND_URL}/api/v1/langgraph/status")
        
        # Products (public endpoint)
        await self.test_endpoint("Products List", f"{BACKEND_URL}/api/v1/products")
        
    async def verify_myroofgenius(self):
        """Verify MyRoofGenius frontend"""
        print("\n🔍 VERIFYING MYROOFGENIUS...")
        
        await self.test_endpoint("Homepage", MYROOFGENIUS_URL)
        await self.test_endpoint("API Health", f"{MYROOFGENIUS_URL}/api/health")
        
    async def verify_weathercraft(self):
        """Verify WeatherCraft ERP"""
        print("\n🔍 VERIFYING WEATHERCRAFT ERP...")
        
        await self.test_endpoint("ERP Homepage", WEATHERCRAFT_URL)
        
    async def verify_database_operations(self):
        """Test actual database operations"""
        print("\n🔍 VERIFYING DATABASE OPERATIONS...")
        
        # Test memory recall
        response = await self.client.get(
            f"{BACKEND_URL}/api/v1/persistent-memory/recall",
            params={"limit": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.results.append(f"✅ Memory Recall: {data.get('count', 0)} memories retrieved")
        else:
            self.failures.append(f"❌ Memory Recall: {response.status_code}")
            
        # Test knowledge retrieval
        response = await self.client.get(f"{BACKEND_URL}/api/v1/persistent-memory/knowledge")
        
        if response.status_code == 200:
            data = response.json()
            self.results.append(f"✅ Knowledge Base: {data.get('count', 0)} entries")
        else:
            self.failures.append(f"❌ Knowledge Base: {response.status_code}")
    
    async def run_full_verification(self):
        """Run complete production verification"""
        print("=" * 60)
        print("🚀 PRODUCTION DEPLOYMENT VERIFICATION")
        print(f"📅 {datetime.utcnow().isoformat()}")
        print("=" * 60)
        
        await self.verify_backend()
        await self.verify_myroofgenius()
        await self.verify_weathercraft()
        await self.verify_database_operations()
        
        await self.client.aclose()
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 VERIFICATION RESULTS")
        print("=" * 60)
        
        print("\n✅ SUCCESSFUL TESTS:")
        for result in self.results:
            print(f"  {result}")
            
        if self.failures:
            print("\n❌ FAILED TESTS:")
            for failure in self.failures:
                print(f"  {failure}")
        
        # Calculate success rate
        total_tests = len(self.results) + len(self.failures)
        success_rate = (len(self.results) / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        print(f"✅ Passed: {len(self.results)}")
        print(f"❌ Failed: {len(self.failures)}")
        
        if success_rate >= 90:
            print("\n🎉 DEPLOYMENT VERIFIED - SYSTEM OPERATIONAL")
        elif success_rate >= 70:
            print("\n⚠️ DEPLOYMENT PARTIALLY SUCCESSFUL - NEEDS ATTENTION")
        else:
            print("\n🚨 DEPLOYMENT FAILED - CRITICAL ISSUES DETECTED")
        
        print("=" * 60)
        
        return success_rate

async def main():
    verifier = ProductionVerifier()
    success_rate = await verifier.run_full_verification()
    
    # Exit with appropriate code
    exit(0 if success_rate >= 90 else 1)

if __name__ == "__main__":
    asyncio.run(main())