#!/usr/bin/env python3
"""
Test AI System v4.33 - Complete LangGraph Orchestration
Tests all AI endpoints and automation features
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# API Configuration
API_URL = "https://brainops-backend-prod.onrender.com"
LOCAL_URL = "http://localhost:10000"

class AISystemTester:
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def test_endpoint(self, method: str, path: str, data: Dict = None, expected_status: int = 200, description: str = "") -> bool:
        """Test a single endpoint"""
        self.total_tests += 1
        url = f"{self.base_url}{path}"
        
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            else:
                response = self.session.request(method, url, json=data)
            
            success = response.status_code == expected_status
            
            if success:
                self.passed_tests += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            result = {
                "test": description or f"{method} {path}",
                "status": status,
                "expected": expected_status,
                "actual": response.status_code,
                "response": response.json() if response.text else None
            }
            
            self.results.append(result)
            print(f"{status}: {result['test']} ({response.status_code})")
            
            return success
            
        except Exception as e:
            status = "❌ ERROR"
            result = {
                "test": description or f"{method} {path}",
                "status": status,
                "error": str(e)
            }
            self.results.append(result)
            print(f"{status}: {result['test']} - {e}")
            return False
    
    def run_ai_tests(self):
        """Run all AI system tests"""
        print("\n🤖 TESTING AI SYSTEM v4.33")
        print("=" * 60)
        
        # 1. Core AI Status
        print("\n📊 Core AI Status:")
        self.test_endpoint("GET", "/api/v1/ai/status", description="AI System Status")
        self.test_endpoint("GET", "/api/v1/ai/agents", description="List AI Agents")
        self.test_endpoint("GET", "/api/v1/ai/workflows", description="List Workflows")
        self.test_endpoint("GET", "/api/v1/ai/test", description="Test AI System")
        
        # 2. Task Submission
        print("\n📝 Task Submission:")
        task_data = {
            "agent_type": "customer_service",
            "action": "send_welcome",
            "parameters": {"customer_id": "CUST-123"},
            "priority": 5,
            "timeout": 300
        }
        self.test_endpoint("POST", "/api/v1/ai/tasks/submit", data=task_data, description="Submit AI Task")
        
        # 3. Workflow Execution
        print("\n🔄 Workflow Execution:")
        workflow_data = {
            "workflow_id": "customer_onboarding",
            "context": {
                "customer_id": "CUST-456",
                "customer_data": {
                    "name": "Test Customer",
                    "email": "test@example.com"
                }
            }
        }
        self.test_endpoint("POST", "/api/v1/ai/workflows/execute", data=workflow_data, description="Execute Workflow")
        
        # 4. Automation Endpoints
        print("\n⚡ Automation Endpoints:")
        customer_data = {
            "id": "CUST-789",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-0123"
        }
        self.test_endpoint("POST", "/api/v1/ai/automations/customer-onboarding", data=customer_data, 
                          description="Customer Onboarding Automation")
        
        self.test_endpoint("POST", "/api/v1/ai/automations/job-completion", 
                          data={"job_id": "JOB-123", "job_data": {"status": "completed"}},
                          description="Job Completion Automation")
        
        requirements = {
            "roof_type": "shingle",
            "square_footage": 2500,
            "complexity": "medium"
        }
        self.test_endpoint("POST", "/api/v1/ai/automations/quote-generation", data=requirements,
                          description="AI Quote Generation")
        
        self.test_endpoint("POST", "/api/v1/ai/automations/schedule-optimization",
                          description="Schedule Optimization")
        
        # 5. Analytics and Insights
        print("\n📈 Analytics & Insights:")
        self.test_endpoint("GET", "/api/v1/ai/analytics/performance", description="AI Performance Metrics")
        self.test_endpoint("POST", "/api/v1/ai/analytics/generate-report", 
                          data={"report_type": "monthly"},
                          description="Generate AI Report")
        
        # 6. Monitoring and Health
        print("\n🏥 Monitoring & Health:")
        self.test_endpoint("GET", "/api/v1/ai/monitoring/health", description="System Health Check")
        self.test_endpoint("GET", "/api/v1/ai/monitoring/anomalies", description="Anomaly Detection")
        
        # 7. Decision Support
        print("\n🎯 Decision Support:")
        decision_data = {
            "type": "pricing",
            "context": {
                "square_footage": 3000,
                "material": "metal",
                "location": "Denver, CO"
            }
        }
        self.test_endpoint("POST", "/api/v1/ai/decisions/recommend", data=decision_data,
                          description="AI Recommendations")
        
        tasks = [
            {"id": "1", "name": "Emergency repair", "priority": 1},
            {"id": "2", "name": "Routine maintenance", "priority": 5},
            {"id": "3", "name": "New installation", "priority": 3}
        ]
        self.test_endpoint("POST", "/api/v1/ai/decisions/prioritize", data=tasks,
                          description="Task Prioritization")
        
        # 8. Compliance and Audit
        print("\n🔒 Compliance & Audit:")
        kyc_data = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "company": "Smith Roofing",
            "tax_id": "12-3456789"
        }
        self.test_endpoint("POST", "/api/v1/ai/compliance/kyc", data=kyc_data,
                          description="KYC Check")
        self.test_endpoint("GET", "/api/v1/ai/compliance/audit", description="Compliance Audit")
        
        # 9. Batch Operations
        print("\n🎭 Batch Operations:")
        batch_ops = [
            {
                "agent_type": "sales",
                "action": "generate_quote",
                "parameters": {"requirements": {"size": "small"}},
                "priority": 3,
                "timeout": 60
            },
            {
                "agent_type": "operations",
                "action": "verify_completion",
                "parameters": {"job_id": "JOB-456"},
                "priority": 2,
                "timeout": 30
            }
        ]
        self.test_endpoint("POST", "/api/v1/ai/batch/process", data=batch_ops,
                          description="Batch Processing")
        
        # 10. Configuration
        print("\n⚙️ Configuration:")
        config = {
            "enabled": True,
            "workflows": ["customer_onboarding", "job_completion"],
            "schedule": "0 9 * * MON-FRI"
        }
        self.test_endpoint("POST", "/api/v1/ai/config/automation", data=config,
                          description="Configure Automation")
        
        # 11. Check for specific agent types
        print("\n🤖 Agent Type Tests:")
        for agent_type in ["CUSTOMER_SERVICE", "SALES", "OPERATIONS", "FINANCE", "TECHNICAL", 
                          "MONITORING", "DECISION", "SCHEDULER", "DATA_ANALYST", "COMPLIANCE"]:
            task = {
                "agent_type": agent_type.lower(),
                "action": "test",
                "parameters": {},
                "priority": 1,
                "timeout": 10
            }
            # Just test if submission works, don't expect success on unknown action
            self.test_endpoint("POST", "/api/v1/ai/tasks/submit", data=task, 
                             expected_status=200,
                             description=f"Test {agent_type} Agent")
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 AI SYSTEM TEST REPORT")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"API URL: {self.base_url}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0:.1f}%")
        
        # Group results by category
        categories = {}
        for result in self.results:
            category = result['test'].split(':')[0] if ':' in result['test'] else 'General'
            if category not in categories:
                categories[category] = {'passed': 0, 'failed': 0}
            
            if result['status'] == '✅ PASS':
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
        
        print("\n📈 Results by Category:")
        for category, stats in categories.items():
            total = stats['passed'] + stats['failed']
            success_rate = (stats['passed'] / total * 100) if total > 0 else 0
            print(f"  {category}: {stats['passed']}/{total} ({success_rate:.1f}%)")
        
        # Show failed tests
        failed_tests = [r for r in self.results if r['status'] != '✅ PASS']
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['test']}")
                if 'actual' in test:
                    print(f"    Expected: {test['expected']}, Got: {test['actual']}")
                if 'error' in test:
                    print(f"    Error: {test['error']}")
        
        # Summary
        print("\n" + "=" * 60)
        if self.passed_tests == self.total_tests:
            print("🎉 ALL TESTS PASSED! AI System v4.33 is fully operational!")
        elif self.passed_tests / self.total_tests >= 0.9:
            print("✅ AI System v4.33 is mostly operational (90%+ success)")
        elif self.passed_tests / self.total_tests >= 0.7:
            print("⚠️ AI System v4.33 is partially operational (70%+ success)")
        else:
            print("❌ AI System v4.33 has significant issues (< 70% success)")
        
        # Save report
        report_file = f"ai_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'api_url': self.base_url,
                'summary': {
                    'total': self.total_tests,
                    'passed': self.passed_tests,
                    'failed': self.total_tests - self.passed_tests,
                    'success_rate': (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
                },
                'results': self.results
            }, f, indent=2, default=str)
        print(f"\n📄 Detailed report saved to: {report_file}")

def main():
    """Main test execution"""
    print("\n🚀 BrainOps AI System v4.33 Test Suite")
    print("Testing Complete LangGraph Orchestration")
    print("=" * 60)
    
    # Test production API
    tester = AISystemTester(API_URL)
    
    # Check if backend is running v4.33
    try:
        response = requests.get(f"{API_URL}/api/v1/health")
        version = response.json().get('version', 'unknown')
        print(f"Backend Version: {version}")
        
        if version != "4.33":
            print(f"⚠️ Warning: Backend is running v{version}, not v4.33")
            print("AI features may not be available until deployment completes")
            user_input = input("\nContinue testing anyway? (y/n): ")
            if user_input.lower() != 'y':
                print("Test aborted. Wait for v4.33 deployment.")
                return
    except Exception as e:
        print(f"❌ Error checking backend version: {e}")
        return
    
    # Run AI tests
    tester.run_ai_tests()
    
    # Generate report
    tester.generate_report()

if __name__ == "__main__":
    main()