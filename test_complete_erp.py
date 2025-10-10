#!/usr/bin/env python3
"""
Comprehensive ERP System Test Suite
Tests all major workflows and functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"  # Change to production URL when testing live
API_PREFIX = "/api/v1/erp"

class ERPTestSuite:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.api_url = f"{base_url}{API_PREFIX}"
        self.test_data = {}
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> Dict:
        """Test a single endpoint"""
        url = f"{self.api_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "PUT":
                response = requests.put(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == expected_status:
                self.results['passed'] += 1
                logger.info(f"✅ {method} {endpoint}: Status {response.status_code}")
                return response.json() if response.text else {}
            else:
                self.results['failed'] += 1
                error = f"{method} {endpoint}: Expected {expected_status}, got {response.status_code}"
                self.results['errors'].append(error)
                logger.error(f"❌ {error}")
                return {}
                
        except Exception as e:
            self.results['failed'] += 1
            error = f"{method} {endpoint}: {str(e)}"
            self.results['errors'].append(error)
            logger.error(f"❌ {error}")
            return {}
    
    def test_lead_management(self):
        """Test lead management workflow"""
        logger.info("\n" + "="*60)
        logger.info("TESTING LEAD MANAGEMENT")
        logger.info("="*60)
        
        # Create a lead
        lead_data = {
            "source": "website",
            "estimated_value": 50000,
            "urgency": "high",
            "property_type": "residential",
            "notes": "Test lead from comprehensive test suite",
            "contact_name": "John Smith",
            "contact_email": "john@example.com",
            "contact_phone": "555-0100"
        }
        
        result = self.test_endpoint("POST", "/leads", lead_data)
        if result and 'lead' in result:
            self.test_data['lead_id'] = result['lead']['id']
            logger.info(f"Created lead: {result['lead']['id']}")
        
        # Get leads
        self.test_endpoint("GET", "/leads")
        
        # Get lead analytics
        self.test_endpoint("GET", "/leads/analytics")
    
    def test_estimation_system(self):
        """Test estimation workflow"""
        logger.info("\n" + "="*60)
        logger.info("TESTING ESTIMATION SYSTEM")
        logger.info("="*60)
        
        # Create an estimate  
        estimate_data = {
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_phone": "555-0100",
            "property_address": "123 Test St, Denver, CO 80202",
            "roof_type": "shingle",
            "roof_size_sqft": 2500,
            "items": [
                {
                    "description": "Remove existing shingles",
                    "quantity": 25,
                    "unit": "square",
                    "unit_price": 50,
                    "category": "labor"
                },
                {
                    "description": "Install new shingles",
                    "quantity": 25,
                    "unit": "square",
                    "unit_price": 150,
                    "category": "material"
                }
            ]
        }
        
        result = self.test_endpoint("POST", "/estimates", estimate_data)
        if result and 'estimate' in result:
            self.test_data['estimate_id'] = result['estimate']['id']
            logger.info(f"Created estimate: {result['estimate']['id']}")
        
        # Get estimates
        self.test_endpoint("GET", "/estimates")
    
    def test_job_management(self):
        """Test job management workflow"""
        logger.info("\n" + "="*60)
        logger.info("TESTING JOB MANAGEMENT")
        logger.info("="*60)
        
        # Create a job
        job_data = {
            "title": "Test Roofing Job",
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "estimate_id": self.test_data.get('estimate_id'),
            "job_type": "installation",
            "priority": "high",
            "start_date": str(datetime.now().date()),
            "estimated_duration_days": 3
        }
        
        result = self.test_endpoint("POST", "/jobs", job_data)
        if result and 'job' in result:
            self.test_data['job_id'] = result['job']['id']
            logger.info(f"Created job: {result['job']['id']}")
        
        # Get jobs
        self.test_endpoint("GET", "/jobs")
        
        # Get job profitability
        self.test_endpoint("GET", "/jobs/profitability")
    
    def test_scheduling_system(self):
        """Test scheduling and dispatch"""
        logger.info("\n" + "="*60)
        logger.info("TESTING SCHEDULING SYSTEM")
        logger.info("="*60)
        
        # Create a schedule
        schedule_data = {
            "job_id": self.test_data.get('job_id'),
            "crew_id": "test-crew",
            "scheduled_date": str((datetime.now() + timedelta(days=1)).date()),
            "start_time": "08:00",
            "end_time": "17:00",
            "notes": "Test schedule entry"
        }
        
        result = self.test_endpoint("POST", "/schedules", schedule_data)
        if result and 'schedule' in result:
            self.test_data['schedule_id'] = result['schedule']['id']
            logger.info(f"Created schedule: {result['schedule']['id']}")
        
        # Get schedules
        self.test_endpoint("GET", "/schedules")
        
        # Get schedule calendar
        self.test_endpoint("GET", f"/schedules/calendar?date={datetime.now().date()}")
    
    def test_inventory_management(self):
        """Test inventory management"""
        logger.info("\n" + "="*60)
        logger.info("TESTING INVENTORY MANAGEMENT")
        logger.info("="*60)
        
        # Check inventory levels
        self.test_endpoint("GET", "/inventory/levels")
        
        # Get low stock items
        self.test_endpoint("GET", "/inventory/reorder")
    
    def test_financial_operations(self):
        """Test financial operations"""
        logger.info("\n" + "="*60)
        logger.info("TESTING FINANCIAL OPERATIONS")
        logger.info("="*60)
        
        # Create an invoice
        invoice_data = {
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "job_id": self.test_data.get('job_id'),
            "items": [
                {
                    "description": "Roofing installation",
                    "quantity": 1,
                    "unit_price": 5000
                }
            ],
            "tax_rate": 8.75
        }
        
        result = self.test_endpoint("POST", "/invoices", invoice_data)
        if result and 'invoice' in result:
            self.test_data['invoice_id'] = result['invoice']['id']
            logger.info(f"Created invoice: {result['invoice']['id']}")
        
        # Get invoices
        self.test_endpoint("GET", "/invoices")
        
        # Get AR aging
        self.test_endpoint("GET", "/ar-aging")
        
        # Record a payment
        payment_data = {
            "customer_name": "Test Customer",
            "amount": 2500,
            "payment_method": "credit-card",
            "invoice_applications": [
                {
                    "invoice_id": self.test_data.get('invoice_id'),
                    "amount": 2500
                }
            ]
        }
        
        result = self.test_endpoint("POST", "/payments", payment_data)
        if result and 'payment' in result:
            logger.info(f"Recorded payment: {result['payment']['id']}")
    
    def test_service_operations(self):
        """Test service and warranty management"""
        logger.info("\n" + "="*60)
        logger.info("TESTING SERVICE OPERATIONS")
        logger.info("="*60)
        
        # Create a service ticket
        ticket_data = {
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "issue_type": "leak",
            "severity": "high",
            "description": "Roof leak in master bedroom",
            "location_description": "Northeast corner of roof"
        }
        
        result = self.test_endpoint("POST", "/service-tickets", ticket_data)
        if result and 'ticket' in result:
            self.test_data['ticket_id'] = result['ticket']['id']
            logger.info(f"Created service ticket: {result['ticket']['id']}")
        
        # Create a warranty
        warranty_data = {
            "job_id": self.test_data.get('job_id'),
            "customer_name": "Test Customer",
            "start_date": str(datetime.now().date()),
            "duration_years": 10,
            "warranty_type": "workmanship"
        }
        
        result = self.test_endpoint("POST", "/warranties", warranty_data)
        if result and 'warranty' in result:
            logger.info(f"Created warranty: {result['warranty']['id']}")
        
        # Get service dashboard
        self.test_endpoint("GET", "/service-dashboard")
    
    def run_all_tests(self):
        """Run all test suites"""
        logger.info("\n" + "#"*60)
        logger.info("# WEATHERCRAFT ERP - COMPREHENSIVE SYSTEM TEST")
        logger.info("#"*60)
        logger.info(f"Testing against: {self.base_url}")
        logger.info(f"Started at: {datetime.now()}")
        
        # Run test suites
        self.test_lead_management()
        self.test_estimation_system()
        self.test_job_management()
        self.test_scheduling_system()
        self.test_inventory_management()
        self.test_financial_operations()
        self.test_service_operations()
        
        # Print results
        logger.info("\n" + "="*60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ Passed: {self.results['passed']}")
        logger.info(f"❌ Failed: {self.results['failed']}")
        
        success_rate = (self.results['passed'] / (self.results['passed'] + self.results['failed']) * 100) if (self.results['passed'] + self.results['failed']) > 0 else 0
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        if self.results['errors']:
            logger.info("\nErrors:")
            for error in self.results['errors'][:10]:  # Show first 10 errors
                logger.error(f"  - {error}")
        
        # Determine overall status
        if success_rate >= 80:
            logger.info("\n🎉 SYSTEM TEST PASSED - ERP is operational!")
        elif success_rate >= 60:
            logger.info("\n⚠️ SYSTEM PARTIALLY OPERATIONAL - Some features need attention")
        else:
            logger.info("\n❌ SYSTEM TEST FAILED - Major issues detected")
        
        return self.results

def main():
    """Run the test suite"""
    tester = ERPTestSuite()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            logger.info("✅ Server is running")
        else:
            logger.error("❌ Server health check failed")
            return
    except Exception as e:
        logger.error(f"❌ Cannot connect to server at {BASE_URL}: {e}")
        logger.info("Please ensure the FastAPI server is running")
        return
    
    # Run tests
    results = tester.run_all_tests()
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nTest results saved to test_results.json")

if __name__ == "__main__":
    main()