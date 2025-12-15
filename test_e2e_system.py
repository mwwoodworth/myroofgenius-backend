#!/usr/bin/env python3
"""
WeatherCraft ERP - Comprehensive E2E System Test
Tests all AI-native operations, CRM, ERP, and ORM functionality
"""

import requests
import json
import psycopg2
from datetime import datetime
import sys

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
AI_SERVICE_URL = "https://brainops-ai-agents.onrender.com"
FRONTEND_URL = "https://weathercraft-erp.vercel.app"

# Database config
DB_CONFIG = {
    'host': 'aws-0-us-east-2.pooler.supabase.com',
    'database': 'postgres',
    'user': 'postgres.yomagoqdmxszqtdwuhab',
    'password': '<DB_PASSWORD_REDACTED>'
}

class SystemTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []

    def test(self, name, func):
        """Run a test and track results"""
        try:
            result = func()
            if result:
                self.tests_passed += 1
                self.results.append(f"✅ {name}: PASSED")
                return True
            else:
                self.tests_failed += 1
                self.results.append(f"❌ {name}: FAILED")
                return False
        except Exception as e:
            self.tests_failed += 1
            self.results.append(f"❌ {name}: ERROR - {str(e)}")
            return False

    def test_backend_health(self):
        """Test backend is operational"""
        r = requests.get(f"{BACKEND_URL}/api/v1/health")
        data = r.json()
        return data.get('operational') == True

    def test_ai_service_health(self):
        """Test AI service is operational"""
        r = requests.get(f"{AI_SERVICE_URL}/health")
        data = r.json()
        return data.get('status') == 'healthy' and data.get('ai_enabled') == True

    def test_real_ai_analysis(self):
        """Test real AI is working, not mock data"""
        payload = {
            "text": "New customer inquiry about commercial roof replacement. 10,000 sq ft building.",
            "analysis_type": "lead_scoring"
        }
        r = requests.post(f"{BACKEND_URL}/api/v1/ai/analyze", json=payload)
        data = r.json()

        # Check for real AI response indicators
        has_ai_provider = data.get('metadata', {}).get('ai_provider') in ['openai', 'anthropic', 'gemini']
        has_analysis = 'analysis' in data
        is_not_mock = 'mock' not in str(data).lower() and 'random' not in str(data).lower()

        return has_ai_provider and has_analysis and is_not_mock

    def test_crm_customers(self):
        """Test CRM customer operations"""
        # Test GET
        r = requests.get(f"{FRONTEND_URL}/api/customers")
        data = r.json()

        has_customers = 'customers' in data and len(data['customers']) > 0

        # Verify it's real data from database
        if has_customers:
            customer = data['customers'][0]
            has_real_fields = all(k in customer for k in ['id', 'name', 'email', 'created_at'])
            return has_real_fields
        return False

    def test_crm_jobs(self):
        """Test CRM job operations"""
        r = requests.get(f"{FRONTEND_URL}/api/jobs")
        data = r.json()

        has_jobs = 'jobs' in data and len(data['jobs']) > 0

        if has_jobs:
            job = data['jobs'][0]
            has_real_fields = all(k in job for k in ['id', 'customer_id', 'status'])
            return has_real_fields
        return False

    def test_erp_estimates(self):
        """Test ERP estimate operations"""
        r = requests.get(f"{FRONTEND_URL}/api/estimates")
        data = r.json()

        # Should have estimates or empty array, not error
        return 'estimates' in data or 'success' in data

    def test_erp_invoices(self):
        """Test ERP invoice operations"""
        r = requests.get(f"{FRONTEND_URL}/api/invoices")
        data = r.json()

        # Should have invoices or empty array
        return 'invoices' in data or 'success' in data

    def test_automations_status(self):
        """Test automations are enabled"""
        r = requests.get(f"{BACKEND_URL}/api/v1/automations/status")
        data = r.json()

        if data.get('success'):
            active = data.get('active_automations', 0)
            return active >= 9  # Should have at least 9 active
        return False

    def test_database_orm(self):
        """Test ORM and database operations"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Test we can query real data
            cur.execute("SELECT COUNT(*) FROM customers")
            customer_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM jobs")
            job_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM ai_agents WHERE status = 'active'")
            ai_agent_count = cur.fetchone()[0]

            cur.close()
            conn.close()

            # Should have real data
            return customer_count > 1000 and job_count > 10000 and ai_agent_count > 0
        except:
            return False

    def test_ai_decision_points(self):
        """Test AI decision points are configured"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM ai_decision_points WHERE enabled = true")
            count = cur.fetchone()[0]

            cur.close()
            conn.close()

            return count >= 10
        except:
            return False

    def test_monitoring_endpoint(self):
        """Test monitoring provides real metrics"""
        r = requests.get(f"{BACKEND_URL}/api/v1/monitoring")
        data = r.json()

        has_metrics = 'system' in data and 'database' in data
        has_real_data = data.get('database', {}).get('customers', 0) > 1000

        return has_metrics and has_real_data

    def test_analytics_dashboard(self):
        """Test analytics provides real insights"""
        r = requests.get(f"{BACKEND_URL}/api/v1/analytics/dashboard")
        data = r.json()

        has_metrics = 'metrics' in data
        has_revenue = data.get('metrics', {}).get('revenue', {}).get('total', 0) > 0

        return has_metrics and has_revenue

    def test_frontend_endpoints(self):
        """Test frontend API routes"""
        endpoints = [
            '/api/monitoring',
            '/api/appointments',
            '/api/calendar',
            '/api/reports'
        ]

        success_count = 0
        for endpoint in endpoints:
            try:
                r = requests.get(f"{FRONTEND_URL}{endpoint}", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    # Check for success or data
                    if 'success' in data or any(key in data for key in ['appointments', 'events', 'reports', 'status']):
                        success_count += 1
            except:
                pass

        return success_count >= 3  # At least 3 of 4 should work

    def test_ai_agents_registered(self):
        """Test AI agents are properly registered"""
        r = requests.get(f"{BACKEND_URL}/api/v1/ai/agents")
        data = r.json()

        agent_count = data.get('count', 0)
        return agent_count >= 50  # Should have 59 agents

    def test_workflows_configured(self):
        """Test workflows are configured"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM workflows")
            count = cur.fetchone()[0]

            cur.close()
            conn.close()

            return count >= 10
        except:
            return False

    def run_all_tests(self):
        """Run comprehensive E2E tests"""
        print("=" * 60)
        print("WEATHERCRAFT ERP - COMPREHENSIVE E2E SYSTEM TEST")
        print("=" * 60)
        print()

        print("🧪 Running tests...\n")

        # Core Infrastructure
        print("INFRASTRUCTURE TESTS:")
        self.test("Backend Health", self.test_backend_health)
        self.test("AI Service Health", self.test_ai_service_health)
        self.test("Monitoring Endpoint", self.test_monitoring_endpoint)
        print()

        # AI Native Operations
        print("AI NATIVE OPERATIONS:")
        self.test("Real AI Analysis", self.test_real_ai_analysis)
        self.test("AI Agents Registered", self.test_ai_agents_registered)
        self.test("AI Decision Points", self.test_ai_decision_points)
        print()

        # CRM Functionality
        print("CRM FUNCTIONALITY:")
        self.test("Customer Operations", self.test_crm_customers)
        self.test("Job Management", self.test_crm_jobs)
        print()

        # ERP Functionality
        print("ERP FUNCTIONALITY:")
        self.test("Estimate Management", self.test_erp_estimates)
        self.test("Invoice Management", self.test_erp_invoices)
        self.test("Analytics Dashboard", self.test_analytics_dashboard)
        print()

        # Automation & Workflows
        print("AUTOMATION SYSTEM:")
        self.test("Automations Status", self.test_automations_status)
        self.test("Workflows Configured", self.test_workflows_configured)
        print()

        # Database & ORM
        print("DATABASE & ORM:")
        self.test("Database ORM Operations", self.test_database_orm)
        print()

        # Frontend
        print("FRONTEND INTEGRATION:")
        self.test("Frontend API Endpoints", self.test_frontend_endpoints)
        print()

        # Summary
        print("=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)

        for result in self.results:
            print(result)

        print()
        print(f"TOTAL: {self.tests_passed} PASSED, {self.tests_failed} FAILED")

        success_rate = (self.tests_passed / (self.tests_passed + self.tests_failed)) * 100
        print(f"SUCCESS RATE: {success_rate:.1f}%")

        print()
        if success_rate >= 80:
            print("🎉 SYSTEM IS OPERATIONAL - AI-NATIVE ERP/CRM CONFIRMED")
        elif success_rate >= 60:
            print("⚠️  SYSTEM PARTIALLY OPERATIONAL - SOME ISSUES DETECTED")
        else:
            print("❌ SYSTEM HAS CRITICAL ISSUES - IMMEDIATE ATTENTION NEEDED")

        return success_rate

if __name__ == "__main__":
    tester = SystemTester()
    success_rate = tester.run_all_tests()

    # Exit with appropriate code
    if success_rate >= 80:
        sys.exit(0)
    else:
        sys.exit(1)