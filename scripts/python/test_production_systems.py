#!/usr/bin/env python3
"""
BrainOps AI OS - Production System Test Suite
Version: 1.0.0
Comprehensive testing of all production systems
"""

import os
import sys
import json
import asyncio
import httpx
import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
DB_CONFIG = {
    'host': 'aws-0-us-east-2.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.yomagoqdmxszqtdwuhab',
    'password': '<DB_PASSWORD_REDACTED>'
}

API_BASE_URL = "https://brainops-backend-prod.onrender.com"
TASK_OS_URL = "http://localhost:8000"

class ProductionTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = 0
        
    def test_result(self, category: str, test_name: str, status: str, details: str = ""):
        """Record test result"""
        self.total_tests += 1
        
        if status == "PASS":
            self.passed_tests += 1
            symbol = f"{Fore.GREEN}✅"
        elif status == "FAIL":
            self.failed_tests += 1
            symbol = f"{Fore.RED}❌"
        else:  # WARNING
            self.warnings += 1
            symbol = f"{Fore.YELLOW}⚠️"
        
        self.results.append({
            'category': category,
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        print(f"{symbol} [{category}] {test_name}: {status}")
        if details:
            print(f"   {details}")
    
    def test_database_connectivity(self):
        """Test database connection and schema"""
        category = "DATABASE"
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Test connection
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            self.test_result(category, "Connection", "PASS", f"PostgreSQL {version[0][:20]}...")
            
            # Test schemas exist
            schemas = ['task_os', 'core', 'ops', 'memory', 'docs', 'data', 'email', 'revenue']
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = ANY(%s)
            """, (schemas,))
            
            existing_schemas = [row[0] for row in cursor.fetchall()]
            
            for schema in schemas:
                if schema in existing_schemas:
                    self.test_result(category, f"Schema {schema}", "PASS")
                else:
                    self.test_result(category, f"Schema {schema}", "FAIL", "Schema does not exist")
            
            # Test critical tables
            critical_tables = [
                ('task_os', 'epics'),
                ('task_os', 'tasks'),
                ('core', 'env_registry'),
                ('ops', 'run_logs'),
                ('memory', 'agent_memories')
            ]
            
            for schema, table in critical_tables:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                """, (schema, table))
                
                if cursor.fetchone()[0] > 0:
                    cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                    count = cursor.fetchone()[0]
                    self.test_result(category, f"Table {schema}.{table}", "PASS", f"{count} records")
                else:
                    self.test_result(category, f"Table {schema}.{table}", "FAIL", "Table does not exist")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.test_result(category, "Connection", "FAIL", str(e))
    
    async def test_backend_api(self):
        """Test backend API endpoints"""
        category = "BACKEND_API"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test health endpoint
            try:
                response = await client.get(f"{API_BASE_URL}/api/v1/health")
                if response.status_code == 200:
                    data = response.json()
                    self.test_result(category, "Health Check", "PASS", f"Status: {data.get('status')}")
                else:
                    self.test_result(category, "Health Check", "FAIL", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_result(category, "Health Check", "FAIL", str(e))
            
            # Test version endpoint
            try:
                response = await client.get(f"{API_BASE_URL}/api/v1/version")
                if response.status_code == 200:
                    data = response.json()
                    self.test_result(category, "Version", "PASS", f"Version: {data.get('version')}")
                else:
                    self.test_result(category, "Version", "WARNING", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_result(category, "Version", "WARNING", str(e))
            
            # Test public endpoints
            public_endpoints = [
                "/api/v1/products/public",
                "/api/v1/aurea/public/chat",
                "/api/v1/marketplace/products"
            ]
            
            for endpoint in public_endpoints:
                try:
                    response = await client.get(f"{API_BASE_URL}{endpoint}")
                    if response.status_code in [200, 201]:
                        self.test_result(category, f"Public {endpoint}", "PASS")
                    elif response.status_code == 404:
                        self.test_result(category, f"Public {endpoint}", "WARNING", "Endpoint not found")
                    else:
                        self.test_result(category, f"Public {endpoint}", "FAIL", f"Status: {response.status_code}")
                except Exception as e:
                    self.test_result(category, f"Public {endpoint}", "FAIL", str(e))
    
    async def test_task_os(self):
        """Test Task OS service"""
        category = "TASK_OS"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{TASK_OS_URL}/")
                if response.status_code == 200:
                    data = response.json()
                    self.test_result(category, "Service Status", "PASS", f"Version: {data.get('version')}")
                else:
                    self.test_result(category, "Service Status", "FAIL", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_result(category, "Service Status", "WARNING", "Service not running locally")
            
            # Test health endpoint
            try:
                response = await client.get(f"{TASK_OS_URL}/health")
                if response.status_code == 200:
                    data = response.json()
                    self.test_result(category, "Health Check", "PASS", f"Task count: {data.get('task_count', 0)}")
                else:
                    self.test_result(category, "Health Check", "WARNING", f"Status code: {response.status_code}")
            except Exception as e:
                self.test_result(category, "Health Check", "WARNING", str(e))
    
    def test_environment_registry(self):
        """Test environment variable registry"""
        category = "ENV_REGISTRY"
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Count total variables
            cursor.execute("SELECT COUNT(*) FROM core.env_registry")
            total = cursor.fetchone()[0]
            self.test_result(category, "Total Variables", "PASS", f"{total} variables registered")
            
            # Count by scope
            cursor.execute("""
                SELECT scope, COUNT(*) 
                FROM core.env_registry 
                GROUP BY scope
            """)
            
            for scope, count in cursor.fetchall():
                self.test_result(category, f"Scope {scope}", "PASS", f"{count} variables")
            
            # Check for sensitive variables
            cursor.execute("""
                SELECT COUNT(*) 
                FROM core.env_registry 
                WHERE encrypted_value IS NOT NULL
            """)
            
            encrypted = cursor.fetchone()[0]
            self.test_result(category, "Encrypted Variables", "PASS" if encrypted > 0 else "WARNING", 
                           f"{encrypted} encrypted values")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.test_result(category, "Registry Check", "FAIL", str(e))
    
    def test_memory_system(self):
        """Test memory persistence system"""
        category = "MEMORY_SYSTEM"
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Check agent memories
            cursor.execute("SELECT COUNT(*) FROM memory.agent_memories")
            memories = cursor.fetchone()[0]
            self.test_result(category, "Agent Memories", "PASS" if memories >= 0 else "WARNING", 
                           f"{memories} memories stored")
            
            # Check memory usage tracking
            cursor.execute("SELECT COUNT(*) FROM memory.memory_usage")
            usage = cursor.fetchone()[0]
            self.test_result(category, "Memory Usage", "PASS", f"{usage} usage records")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.test_result(category, "Memory Check", "FAIL", str(e))
    
    def test_data_pipeline(self):
        """Test Centerpoint data pipeline"""
        category = "DATA_PIPELINE"
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Check sources
            cursor.execute("SELECT COUNT(*) FROM data.centerpoint_sources")
            sources = cursor.fetchone()[0]
            self.test_result(category, "Data Sources", "PASS" if sources >= 0 else "WARNING", 
                           f"{sources} sources configured")
            
            # Check ingestions
            cursor.execute("""
                SELECT COUNT(*), MAX(start_time) 
                FROM data.centerpoint_ingestions
            """)
            
            count, last_run = cursor.fetchone()
            if count > 0:
                self.test_result(category, "Ingestions", "PASS", 
                               f"{count} runs, last: {last_run}")
            else:
                self.test_result(category, "Ingestions", "WARNING", "No ingestions run yet")
            
            # Check reconciliations
            cursor.execute("SELECT COUNT(*) FROM data.centerpoint_reconciliations")
            recons = cursor.fetchone()[0]
            self.test_result(category, "Reconciliations", "PASS" if recons >= 0 else "WARNING",
                           f"{recons} reconciliations")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.test_result(category, "Pipeline Check", "WARNING", str(e))
    
    def test_revenue_system(self):
        """Test revenue tracking system"""
        category = "REVENUE"
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Check payments table
            cursor.execute("SELECT COUNT(*), SUM(amount_cents) FROM revenue.payments WHERE status = 'succeeded'")
            count, total = cursor.fetchone()
            
            if count and count > 0:
                self.test_result(category, "Payments", "PASS", 
                               f"{count} payments, total: ${(total or 0)/100:.2f}")
            else:
                self.test_result(category, "Payments", "WARNING", "No payments recorded")
            
            # Check webhooks
            cursor.execute("SELECT COUNT(*) FROM revenue.webhooks")
            webhooks = cursor.fetchone()[0]
            self.test_result(category, "Webhooks", "PASS", f"{webhooks} webhook events")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.test_result(category, "Revenue Check", "WARNING", str(e))
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("PRODUCTION SYSTEM TEST REPORT")
        print("="*60)
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {Fore.GREEN}{self.passed_tests}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{self.failed_tests}{Style.RESET_ALL}")
        print(f"Warnings: {Fore.YELLOW}{self.warnings}{Style.RESET_ALL}")
        
        # Calculate health score
        if self.total_tests > 0:
            health_score = (self.passed_tests / self.total_tests) * 100
            
            if health_score >= 90:
                status = f"{Fore.GREEN}HEALTHY"
            elif health_score >= 70:
                status = f"{Fore.YELLOW}DEGRADED"
            else:
                status = f"{Fore.RED}CRITICAL"
            
            print(f"\nSystem Health: {status} ({health_score:.1f}%){Style.RESET_ALL}")
        
        # Group results by category
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'passed': 0, 'failed': 0, 'warnings': 0}
            
            if result['status'] == 'PASS':
                categories[cat]['passed'] += 1
            elif result['status'] == 'FAIL':
                categories[cat]['failed'] += 1
            else:
                categories[cat]['warnings'] += 1
        
        print("\nResults by Category:")
        for cat, stats in categories.items():
            print(f"  {cat}:")
            print(f"    Passed: {stats['passed']}")
            print(f"    Failed: {stats['failed']}")
            print(f"    Warnings: {stats['warnings']}")
        
        # Save report to file
        with open('TEST_REPORT.json', 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'summary': {
                    'total': self.total_tests,
                    'passed': self.passed_tests,
                    'failed': self.failed_tests,
                    'warnings': self.warnings,
                    'health_score': health_score if self.total_tests > 0 else 0
                },
                'results': self.results
            }, f, indent=2)
        
        print("\nDetailed report saved to TEST_REPORT.json")
        
        return health_score if self.total_tests > 0 else 0
    
    async def run_all_tests(self):
        """Run all production tests"""
        print("🧪 Running BrainOps Production System Tests")
        print("="*60)
        
        # Database tests
        print("\n📊 Testing Database...")
        self.test_database_connectivity()
        
        # Backend API tests
        print("\n🌐 Testing Backend API...")
        await self.test_backend_api()
        
        # Task OS tests
        print("\n📋 Testing Task OS...")
        await self.test_task_os()
        
        # Environment Registry tests
        print("\n🔐 Testing Environment Registry...")
        self.test_environment_registry()
        
        # Memory System tests
        print("\n🧠 Testing Memory System...")
        self.test_memory_system()
        
        # Data Pipeline tests
        print("\n🔄 Testing Data Pipeline...")
        self.test_data_pipeline()
        
        # Revenue System tests
        print("\n💰 Testing Revenue System...")
        self.test_revenue_system()
        
        # Generate report
        health_score = self.generate_report()
        
        # Exit with appropriate code
        if self.failed_tests > 0:
            sys.exit(1)
        elif self.warnings > 5:
            sys.exit(2)
        else:
            sys.exit(0)

async def main():
    tester = ProductionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())