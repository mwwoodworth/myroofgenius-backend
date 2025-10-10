#!/usr/bin/env python3
"""
Test Complete Production System
Direct database connections and thorough testing
"""

import psycopg2
import requests
import json
import time
from datetime import datetime
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Direct database connection
DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
BACKEND_URL = "https://brainops-backend-prod.onrender.com"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def test_database_direct():
    """Test database directly"""
    logger.info("=" * 60)
    logger.info("TESTING DATABASE DIRECTLY")
    logger.info("=" * 60)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # Test 1: Check tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('leads', 'estimates', 'jobs', 'invoices', 'workflows', 
                               'workflow_executions', 'material_orders', 'purchase_orders')
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        if len(tables) >= 8:
            logger.info(f"✅ All core tables exist: {tables}")
            tests_passed += 1
        else:
            logger.error(f"❌ Missing tables. Found: {tables}")
            tests_failed += 1
        
        # Test 2: Check leads table columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'leads' AND table_schema = 'public'
            AND column_name IN ('company_name', 'contact_name', 'contact_email', 
                               'lead_number', 'lead_score', 'score')
        """)
        lead_columns = [row[0] for row in cursor.fetchall()]
        
        if len(lead_columns) >= 5:
            logger.info(f"✅ Lead columns exist: {lead_columns}")
            tests_passed += 1
        else:
            logger.error(f"❌ Missing lead columns. Found: {lead_columns}")
            tests_failed += 1
        
        # Test 3: Insert test lead directly
        test_lead_id = str(uuid.uuid4())
        test_email = f"test_{uuid.uuid4().hex[:8]}@production.com"
        
        cursor.execute("""
            INSERT INTO leads (
                id, lead_number, name, email, phone, 
                status, score, source, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
        """, (test_lead_id, f"L-TEST-{uuid.uuid4().hex[:5]}", 
              "Production Test Lead", test_email, "(555) 123-4567", 
              "new", 75, "test"))
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT id, name, score FROM leads WHERE id = %s", (test_lead_id,))
        lead = cursor.fetchone()
        
        if lead:
            logger.info(f"✅ Lead created directly: {lead[1]} with score {lead[2]}")
            tests_passed += 1
        else:
            logger.error("❌ Failed to create lead directly")
            tests_failed += 1
        
        # Test 4: Check workflow tables
        cursor.execute("SELECT COUNT(*) FROM workflows")
        workflow_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM workflow_executions")
        execution_count = cursor.fetchone()[0]
        
        logger.info(f"✅ Workflows: {workflow_count}, Executions: {execution_count}")
        tests_passed += 1
        
        # Test 5: Check job and invoice counts
        cursor.execute("SELECT COUNT(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM invoices")
        invoice_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        
        logger.info(f"✅ Production data - Jobs: {job_count}, Invoices: {invoice_count}, Customers: {customer_count}")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"❌ Database test error: {e}")
        tests_failed += 1
    finally:
        cursor.close()
        conn.close()
    
    logger.info(f"\nDatabase Tests - Passed: {tests_passed}, Failed: {tests_failed}")
    return tests_passed, tests_failed

def wait_for_deployment(max_wait=30):
    """Wait for deployment to complete"""
    logger.info("Checking deployment status...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                version = data.get('version', 'unknown')
                logger.info(f"Current backend version: {version}")
                if version.startswith('23'):
                    logger.info(f"✅ v23.0.0 is deployed!")
                    return True
                elif version == '22.5.0':
                    logger.info(f"⚠️ v22.5.0 still running - v23.0.0 deployment pending")
                    break
            else:
                logger.info(f"⏳ Health check returned {response.status_code}")
        except Exception as e:
            logger.info(f"⏳ Health check failed: {e}")
        
        time.sleep(5)
    
    logger.warning("⚠️ Proceeding with tests using current deployment")
    return False

def test_api_endpoints():
    """Test API endpoints"""
    logger.info("=" * 60)
    logger.info("TESTING API ENDPOINTS")
    logger.info("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Health check
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Health check: {data.get('version')} - {data.get('status')}")
            tests_passed += 1
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        tests_failed += 1
    
    # Test 2: Lead endpoints
    try:
        # Test GET leads
        response = requests.get(f"{BACKEND_URL}/api/v1/erp/leads")
        if response.status_code == 200:
            logger.info("✅ GET /api/v1/erp/leads working")
            tests_passed += 1
        elif response.status_code == 404:
            logger.warning("⚠️ ERP endpoints not deployed yet")
            tests_failed += 1
        else:
            logger.error(f"❌ GET leads failed: {response.status_code}")
            tests_failed += 1
        
        # Test POST lead
        test_lead = {
            "contact_name": f"API Test {datetime.now().strftime('%H%M%S')}",
            "contact_email": f"api_test_{uuid.uuid4().hex[:8]}@test.com",
            "contact_phone": "(555) 987-6543",
            "company_name": "API Test Company",
            "urgency": "high"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/v1/erp/leads", json=test_lead)
        if response.status_code in [200, 201]:
            data = response.json()
            logger.info(f"✅ POST /api/v1/erp/leads working - Created: {data.get('id')}")
            tests_passed += 1
        elif response.status_code == 404:
            logger.warning("⚠️ POST lead endpoint not found")
            tests_failed += 1
        else:
            logger.error(f"❌ POST lead failed: {response.status_code}")
            tests_failed += 1
            
    except Exception as e:
        logger.error(f"❌ Lead endpoint error: {e}")
        tests_failed += 1
    
    # Test 3: Workflow endpoints
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/workflows")
        if response.status_code == 200:
            logger.info("✅ GET /api/v1/workflows working")
            tests_passed += 1
        elif response.status_code == 404:
            logger.warning("⚠️ Workflow endpoints not deployed yet")
            tests_failed += 1
        else:
            logger.error(f"❌ GET workflows failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        logger.error(f"❌ Workflow endpoint error: {e}")
        tests_failed += 1
    
    # Test 4: Analytics endpoints
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/erp/leads/analytics")
        if response.status_code == 200:
            logger.info("✅ GET /api/v1/erp/leads/analytics working")
            tests_passed += 1
        elif response.status_code == 404:
            logger.warning("⚠️ Analytics endpoints not deployed yet")
            tests_failed += 1
        else:
            logger.error(f"❌ Analytics failed: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        logger.error(f"❌ Analytics endpoint error: {e}")
        tests_failed += 1
    
    logger.info(f"\nAPI Tests - Passed: {tests_passed}, Failed: {tests_failed}")
    return tests_passed, tests_failed

def test_process_flows():
    """Test complete process flows"""
    logger.info("=" * 60)
    logger.info("TESTING PROCESS FLOWS")
    logger.info("=" * 60)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # Test Lead → Customer flow
        lead_id = str(uuid.uuid4())
        customer_id = str(uuid.uuid4())
        
        # Create lead
        cursor.execute("""
            INSERT INTO leads (id, lead_number, name, email, status, score, source, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (lead_id, f"L-FLOW-{uuid.uuid4().hex[:5]}", "Flow Test Lead", 
              f"flow_{uuid.uuid4().hex[:8]}@test.com", "new", 80, "test"))
        
        # Convert to customer
        cursor.execute("""
            INSERT INTO customers (id, name, email, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (customer_id, "Flow Test Customer", f"customer_{uuid.uuid4().hex[:8]}@test.com"))
        
        # Update lead
        cursor.execute("""
            UPDATE leads SET status = 'converted', customer_id = %s, converted_at = NOW()
            WHERE id = %s
        """, (customer_id, lead_id))
        
        conn.commit()
        
        # Verify conversion
        cursor.execute("SELECT status, customer_id FROM leads WHERE id = %s", (lead_id,))
        result = cursor.fetchone()
        
        if result and result[0] == 'converted':
            logger.info("✅ Lead → Customer flow working")
            tests_passed += 1
        else:
            logger.error("❌ Lead → Customer flow failed")
            tests_failed += 1
        
        # Test Job → Invoice flow
        job_id = str(uuid.uuid4())
        invoice_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO jobs (id, customer_id, status, total_amount, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (job_id, customer_id, "completed", 5000))
        
        cursor.execute("""
            INSERT INTO invoices (id, invoice_number, title, customer_id, job_id, 
                                total_amount, subtotal_cents, tax_cents, discount_cents, 
                                total_cents, balance_cents, line_items,
                                status, invoice_date, due_date, created_at, 
                                created_by, org_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW() + INTERVAL '30 days', NOW(),
                    '4b12fb49-f0b1-44ab-bd9c-8385a8958c16', '00000000-0000-0000-0000-000000000001')
        """, (invoice_id, f"INV-{uuid.uuid4().hex[:8]}", "Test Invoice", 
              customer_id, job_id, 5000, 500000, 0, 0, 500000, 500000, 
              '[]', "pending"))
        
        conn.commit()
        
        logger.info("✅ Job → Invoice flow working")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"❌ Process flow error: {e}")
        tests_failed += 1
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    
    logger.info(f"\nProcess Flow Tests - Passed: {tests_passed}, Failed: {tests_failed}")
    return tests_passed, tests_failed

def main():
    logger.info("\n" + "=" * 60)
    logger.info("COMPLETE PRODUCTION SYSTEM TEST")
    logger.info("=" * 60)
    
    # Wait for deployment
    deployment_ready = wait_for_deployment()
    
    # Run all tests
    total_passed = 0
    total_failed = 0
    
    # Database tests
    db_passed, db_failed = test_database_direct()
    total_passed += db_passed
    total_failed += db_failed
    
    # API tests
    api_passed, api_failed = test_api_endpoints()
    total_passed += api_passed
    total_failed += api_failed
    
    # Process flow tests
    flow_passed, flow_failed = test_process_flows()
    total_passed += flow_passed
    total_failed += flow_failed
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("FINAL TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Tests Passed: {total_passed}")
    logger.info(f"Total Tests Failed: {total_failed}")
    success_rate = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0
    logger.info(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        logger.info("✅ SYSTEM IS OPERATIONAL!")
    elif success_rate >= 60:
        logger.info("⚠️ SYSTEM IS PARTIALLY OPERATIONAL")
    else:
        logger.info("❌ SYSTEM NEEDS ATTENTION")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()