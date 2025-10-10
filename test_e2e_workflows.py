#!/usr/bin/env python3
"""
WeatherCraft ERP - End-to-End Workflow Testing
Complete validation of all business processes
"""

import requests
import json
import time
from datetime import datetime, timedelta
import uuid
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
LOCAL_URL = "http://localhost:8000"
USE_LOCAL = True  # Set to True for local testing

BASE_URL = LOCAL_URL if USE_LOCAL else BACKEND_URL

# Test data
TEST_LEAD = {
    "contact_name": "Test Customer",
    "contact_email": f"test_{uuid.uuid4().hex[:8]}@example.com",
    "contact_phone": "(303) 555-0100",
    "company_name": "Test Roofing Co",
    "property_address": "123 Test St, Denver, CO 80202",
    "roof_type": "shingle",
    "roof_size": 2500,
    "urgency": "high",
    "budget_range": "high",
    "source": "website",
    "notes": "E2E test lead"
}

class WorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_entities = {
            'leads': [],
            'customers': [],
            'estimates': [],
            'jobs': [],
            'invoices': [],
            'tickets': []
        }
    
    def log_result(self, test_name: str, success: bool, details: str = ""):
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            logger.info(f"✅ {test_name}: {details}")
        else:
            logger.error(f"❌ {test_name}: {details}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make HTTP request to backend"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code >= 400:
                logger.warning(f"Request failed: {method} {endpoint} - {response.status_code}")
                return {"error": response.text, "status_code": response.status_code}
            
            return response.json()
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # TEST WORKFLOWS
    # ============================================================================
    
    def test_lead_to_customer_flow(self) -> bool:
        """Test complete lead to customer conversion flow"""
        test_name = "Lead to Customer Flow"
        
        try:
            # Step 1: Create lead
            lead_response = self.make_request("POST", "/api/v1/erp/leads", TEST_LEAD)
            
            if "error" in lead_response:
                self.log_result(test_name, False, f"Failed to create lead: {lead_response['error']}")
                return False
            
            lead_id = lead_response.get('lead', {}).get('id')
            if not lead_id:
                self.log_result(test_name, False, "No lead ID returned")
                return False
            
            self.created_entities['leads'].append(lead_id)
            
            # Step 2: Score lead
            score_response = self.make_request("POST", f"/api/v1/erp/leads/{lead_id}/score", {})
            
            if "error" in score_response:
                self.log_result(test_name, False, f"Failed to score lead: {score_response['error']}")
                return False
            
            score = score_response.get('score', 0)
            
            # Step 3: Convert lead to customer
            convert_response = self.make_request("POST", f"/api/v1/erp/leads/{lead_id}/convert", {})
            
            if "error" in convert_response:
                self.log_result(test_name, False, f"Failed to convert lead: {convert_response['error']}")
                return False
            
            customer_id = convert_response.get('customer', {}).get('id')
            if customer_id:
                self.created_entities['customers'].append(customer_id)
            
            self.log_result(test_name, True, f"Lead {lead_id} converted to customer {customer_id} with score {score}")
            return True
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_estimate_to_job_flow(self) -> bool:
        """Test complete estimate to job conversion flow"""
        test_name = "Estimate to Job Flow"
        
        try:
            # First ensure we have a customer
            if not self.created_entities['customers']:
                if not self.test_lead_to_customer_flow():
                    self.log_result(test_name, False, "Failed to create customer for testing")
                    return False
            
            customer_id = self.created_entities['customers'][0]
            
            # Step 1: Create estimate
            estimate_data = {
                "customer_id": customer_id,
                "project_name": "Test Roof Replacement",
                "roof_size_sqft": 2500,
                "items": [
                    {
                        "description": "Remove existing shingles",
                        "quantity": 25,
                        "unit": "square",
                        "unit_price": 50
                    },
                    {
                        "description": "Install new shingles",
                        "quantity": 25,
                        "unit": "square",
                        "unit_price": 450
                    }
                ]
            }
            
            estimate_response = self.make_request("POST", "/api/v1/erp/estimates", estimate_data)
            
            if "error" in estimate_response:
                self.log_result(test_name, False, f"Failed to create estimate: {estimate_response['error']}")
                return False
            
            estimate_id = estimate_response.get('estimate', {}).get('id')
            if not estimate_id:
                self.log_result(test_name, False, "No estimate ID returned")
                return False
            
            self.created_entities['estimates'].append(estimate_id)
            
            # Step 2: Approve estimate
            approve_response = self.make_request("POST", f"/api/v1/erp/estimates/{estimate_id}/approve", {})
            
            if "error" in approve_response:
                self.log_result(test_name, False, f"Failed to approve estimate: {approve_response['error']}")
                return False
            
            # Step 3: Convert to job
            job_response = self.make_request("POST", f"/api/v1/erp/estimates/{estimate_id}/convert-to-job", {})
            
            if "error" in job_response:
                self.log_result(test_name, False, f"Failed to convert to job: {job_response['error']}")
                return False
            
            job_id = job_response.get('job', {}).get('id')
            if job_id:
                self.created_entities['jobs'].append(job_id)
            
            self.log_result(test_name, True, f"Estimate {estimate_id} converted to job {job_id}")
            return True
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_job_completion_flow(self) -> bool:
        """Test complete job completion flow"""
        test_name = "Job Completion Flow"
        
        try:
            # Ensure we have a job
            if not self.created_entities['jobs']:
                if not self.test_estimate_to_job_flow():
                    self.log_result(test_name, False, "Failed to create job for testing")
                    return False
            
            job_id = self.created_entities['jobs'][0]
            
            # Step 1: Update job status to in_progress
            progress_response = self.make_request("PUT", f"/api/v1/erp/jobs/{job_id}/status", {"status": "in_progress"})
            
            if "error" in progress_response:
                self.log_result(test_name, False, f"Failed to update job status: {progress_response['error']}")
                return False
            
            # Step 2: Complete job
            complete_response = self.make_request("POST", f"/api/v1/erp/jobs/{job_id}/complete", {})
            
            if "error" in complete_response:
                self.log_result(test_name, False, f"Failed to complete job: {complete_response['error']}")
                return False
            
            invoice_id = complete_response.get('invoice', {}).get('id')
            warranty_id = complete_response.get('warranty', {}).get('id')
            
            if invoice_id:
                self.created_entities['invoices'].append(invoice_id)
            
            self.log_result(test_name, True, f"Job {job_id} completed with invoice {invoice_id} and warranty {warranty_id}")
            return True
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_invoice_payment_flow(self) -> bool:
        """Test invoice generation and payment flow"""
        test_name = "Invoice Payment Flow"
        
        try:
            # Ensure we have an invoice
            if not self.created_entities['invoices']:
                if not self.test_job_completion_flow():
                    self.log_result(test_name, False, "Failed to create invoice for testing")
                    return False
            
            invoice_id = self.created_entities['invoices'][0]
            
            # Get invoice details
            invoice_response = self.make_request("GET", f"/api/v1/erp/invoices/{invoice_id}", {})
            
            if "error" in invoice_response:
                self.log_result(test_name, False, f"Failed to get invoice: {invoice_response['error']}")
                return False
            
            invoice = invoice_response.get('invoice', {})
            
            # Process payment
            payment_data = {
                "invoice_id": invoice_id,
                "amount": invoice.get('total', 0),
                "payment_method": "check",
                "reference_number": f"CHK-{uuid.uuid4().hex[:8]}"
            }
            
            payment_response = self.make_request("POST", "/api/v1/erp/payments", payment_data)
            
            if "error" in payment_response:
                self.log_result(test_name, False, f"Failed to process payment: {payment_response['error']}")
                return False
            
            payment_id = payment_response.get('payment', {}).get('id')
            
            self.log_result(test_name, True, f"Payment {payment_id} processed for invoice {invoice_id}")
            return True
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_service_ticket_flow(self) -> bool:
        """Test service ticket creation and resolution flow"""
        test_name = "Service Ticket Flow"
        
        try:
            # Ensure we have a customer and job
            if not self.created_entities['customers']:
                self.test_lead_to_customer_flow()
            
            if not self.created_entities['jobs']:
                self.test_estimate_to_job_flow()
            
            customer_id = self.created_entities['customers'][0] if self.created_entities['customers'] else None
            job_id = self.created_entities['jobs'][0] if self.created_entities['jobs'] else None
            
            # Create service ticket
            ticket_data = {
                "customer_id": customer_id,
                "job_id": job_id,
                "title": "Leak detected after installation",
                "description": "Customer reports minor leak near chimney flashing",
                "priority": "high",
                "type": "warranty"
            }
            
            ticket_response = self.make_request("POST", "/api/v1/erp/service-tickets", ticket_data)
            
            if "error" in ticket_response:
                self.log_result(test_name, False, f"Failed to create ticket: {ticket_response['error']}")
                return False
            
            ticket_id = ticket_response.get('ticket', {}).get('id')
            if ticket_id:
                self.created_entities['tickets'].append(ticket_id)
            
            self.log_result(test_name, True, f"Service ticket {ticket_id} created and dispatched")
            return True
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_workflow_automation(self) -> bool:
        """Test workflow automation system"""
        test_name = "Workflow Automation"
        
        try:
            # Create a test workflow
            workflow_data = {
                "name": "Test Lead Scoring Workflow",
                "description": "Automatically score and qualify leads",
                "category": "sales",
                "trigger_type": "lead_created",
                "conditions": {
                    "has_email": True,
                    "has_phone": True
                },
                "actions": [
                    {"type": "score_lead"},
                    {"type": "assign_to_sales"},
                    {"type": "send_welcome_email"}
                ],
                "is_active": True
            }
            
            workflow_response = self.make_request("POST", "/api/v1/workflows", workflow_data)
            
            if "error" in workflow_response:
                self.log_result(test_name, False, f"Failed to create workflow: {workflow_response['error']}")
                return False
            
            workflow_id = workflow_response.get('workflow', {}).get('id')
            
            # Test workflow execution
            if workflow_id:
                exec_response = self.make_request("POST", f"/api/v1/workflows/{workflow_id}/execute", {
                    "context": {"test": True}
                })
                
                if "error" not in exec_response:
                    self.log_result(test_name, True, f"Workflow {workflow_id} created and tested")
                    return True
            
            self.log_result(test_name, False, "Workflow execution failed")
            return False
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_inventory_management(self) -> bool:
        """Test inventory management and reorder flow"""
        test_name = "Inventory Management"
        
        try:
            # Get inventory levels
            inventory_response = self.make_request("GET", "/api/v1/erp/inventory/levels", {})
            
            if "error" in inventory_response:
                self.log_result(test_name, False, f"Failed to get inventory: {inventory_response['error']}")
                return False
            
            # Check reorder items
            reorder_response = self.make_request("GET", "/api/v1/erp/inventory/reorder", {})
            
            if "error" in reorder_response:
                self.log_result(test_name, False, f"Failed to get reorder items: {reorder_response['error']}")
                return False
            
            items_to_reorder = reorder_response.get('items_to_reorder', [])
            
            # Create purchase order if needed
            if items_to_reorder:
                po_data = {
                    "vendor_id": "test_vendor",
                    "items": [
                        {
                            "item_id": item['id'],
                            "quantity": item.get('reorder_quantity', 100),
                            "unit_price": item.get('unit_price', 10)
                        }
                        for item in items_to_reorder[:3]  # Test with first 3 items
                    ]
                }
                
                po_response = self.make_request("POST", "/api/v1/erp/purchase-orders", po_data)
                
                if "error" not in po_response:
                    self.log_result(test_name, True, f"Inventory checked, {len(items_to_reorder)} items need reorder")
                    return True
            else:
                self.log_result(test_name, True, "Inventory levels adequate, no reorders needed")
                return True
            
            return False
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_scheduling_system(self) -> bool:
        """Test crew scheduling and calendar management"""
        test_name = "Scheduling System"
        
        try:
            # Get available crews
            start_date = datetime.now().isoformat()
            crew_response = self.make_request("POST", "/api/v1/erp/crews/available", {
                "start_date": start_date,
                "duration_days": 2
            })
            
            if "error" in crew_response:
                self.log_result(test_name, False, f"Failed to get crews: {crew_response['error']}")
                return False
            
            # Create a schedule
            schedule_data = {
                "schedulable_type": "job",
                "schedulable_id": self.created_entities['jobs'][0] if self.created_entities['jobs'] else str(uuid.uuid4()),
                "scheduled_date": start_date,
                "duration_hours": 8,
                "crew_id": crew_response.get('best_crew', {}).get('id'),
                "notes": "E2E test schedule"
            }
            
            schedule_response = self.make_request("POST", "/api/v1/erp/schedules", schedule_data)
            
            if "error" in schedule_response:
                self.log_result(test_name, False, f"Failed to create schedule: {schedule_response['error']}")
                return False
            
            # Get calendar
            calendar_response = self.make_request("GET", f"/api/v1/erp/schedules/calendar?date={start_date}", {})
            
            if "error" not in calendar_response:
                self.log_result(test_name, True, "Schedule created and calendar retrieved")
                return True
            
            return False
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    def test_analytics_reporting(self) -> bool:
        """Test analytics and reporting endpoints"""
        test_name = "Analytics & Reporting"
        
        try:
            # Test various analytics endpoints
            endpoints = [
                "/api/v1/erp/leads/analytics",
                "/api/v1/erp/jobs/profitability",
                "/api/v1/erp/ar-aging",
                "/api/v1/erp/service-dashboard"
            ]
            
            all_success = True
            for endpoint in endpoints:
                response = self.make_request("GET", endpoint, {})
                if "error" in response:
                    logger.warning(f"Analytics endpoint failed: {endpoint}")
                    all_success = False
            
            if all_success:
                self.log_result(test_name, True, "All analytics endpoints functional")
            else:
                self.log_result(test_name, False, "Some analytics endpoints failed")
            
            return all_success
            
        except Exception as e:
            self.log_result(test_name, False, str(e))
            return False
    
    # ============================================================================
    # RUN ALL TESTS
    # ============================================================================
    
    def run_all_tests(self):
        """Run all E2E workflow tests"""
        logger.info("="*60)
        logger.info("STARTING END-TO-END WORKFLOW TESTS")
        logger.info(f"Backend URL: {BASE_URL}")
        logger.info("="*60)
        
        tests = [
            self.test_lead_to_customer_flow,
            self.test_estimate_to_job_flow,
            self.test_job_completion_flow,
            self.test_invoice_payment_flow,
            self.test_service_ticket_flow,
            self.test_workflow_automation,
            self.test_inventory_management,
            self.test_scheduling_system,
            self.test_analytics_reporting
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(1)  # Small delay between tests
            except Exception as e:
                logger.error(f"Test failed with exception: {e}")
        
        # Generate summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        logger.info("\n" + "="*60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        logger.info("\nCreated Entities:")
        for entity_type, ids in self.created_entities.items():
            if ids:
                logger.info(f"  {entity_type}: {len(ids)} created")
        
        if failed_tests > 0:
            logger.info("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    logger.info(f"  ❌ {result['test']}: {result['details']}")
        
        # Save results to file
        with open('e2e_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': passed_tests/total_tests if total_tests > 0 else 0
                },
                'results': self.test_results,
                'created_entities': self.created_entities,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info("\nResults saved to e2e_test_results.json")
        logger.info("="*60)

if __name__ == "__main__":
    tester = WorkflowTester()
    tester.run_all_tests()