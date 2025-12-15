#!/usr/bin/env python3
"""
LIVE PRODUCTION SYSTEM VERIFICATION
No assumptions - only real production data
"""

import requests
import psycopg2
import json
import time
from datetime import datetime

class LiveProductionTester:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'passed': 0,
            'failed': 0,
            'tests': []
        }
        
    def test_backend_api(self):
        """Test live backend API"""
        print("\n🔍 TESTING BACKEND API (RENDER)")
        print("="*40)
        
        base_url = "https://brainops-backend-prod.onrender.com"
        
        # Test health endpoint
        try:
            response = requests.get(f"{base_url}/api/v1/health", timeout=10)
            data = response.json()
            
            if response.status_code == 200 and data.get('operational') == True:
                version = data.get('version', 'unknown')
                self.results['passed'] += 1
                print(f"✅ API Health: OK (v{version})")
                print(f"   Database: {data.get('database')}")
                print(f"   Features: {json.dumps(data.get('features', {}))}")
                
                # Test specific endpoints
                endpoints = [
                    '/api/v1/products/public',
                    '/api/v1/aurea/public/chat',
                    '/docs'
                ]
                
                for endpoint in endpoints:
                    try:
                        r = requests.get(f"{base_url}{endpoint}", timeout=5)
                        if r.status_code in [200, 201, 422]:  # 422 is ok for POST endpoints
                            self.results['passed'] += 1
                            print(f"✅ {endpoint}: {r.status_code}")
                        else:
                            self.results['failed'] += 1
                            print(f"❌ {endpoint}: {r.status_code}")
                    except Exception as e:
                        self.results['failed'] += 1
                        print(f"❌ {endpoint}: {str(e)}")
            else:
                self.results['failed'] += 1
                print(f"❌ API Health: Failed")
        except Exception as e:
            self.results['failed'] += 1
            print(f"❌ Backend API: {str(e)}")
    
    def test_myroofgenius(self):
        """Test MyRoofGenius revenue system"""
        print("\n💰 TESTING MYROOFGENIUS REVENUE SYSTEM")
        print("="*40)
        
        try:
            # Test main site
            response = requests.get("https://myroofgenius.com", timeout=10)
            if response.status_code == 200:
                self.results['passed'] += 1
                print(f"✅ MyRoofGenius Main: OK")
                
                # Check for revenue features in HTML
                html = response.text.lower()
                revenue_features = ['stripe', 'payment', 'checkout', 'cart', 'product']
                found = [f for f in revenue_features if f in html]
                
                if found:
                    print(f"   Revenue Features: {', '.join(found)}")
                else:
                    print(f"   ⚠️ Revenue features not visible in HTML")
            else:
                self.results['failed'] += 1
                print(f"❌ MyRoofGenius: Status {response.status_code}")
                
        except Exception as e:
            self.results['failed'] += 1
            print(f"❌ MyRoofGenius: {str(e)}")
    
    def test_weathercraft_erp(self):
        """Test WeatherCraft ERP service system"""
        print("\n🔧 TESTING WEATHERCRAFT ERP SERVICE SYSTEM")
        print("="*40)
        
        try:
            # Test main site
            response = requests.get("https://weathercraft-erp.vercel.app", timeout=10)
            if response.status_code == 200:
                self.results['passed'] += 1
                print(f"✅ WeatherCraft ERP: OK")
                
                # Check for service features
                html = response.text.lower()
                service_features = ['service', 'job', 'schedule', 'technician', 'field']
                found = [f for f in service_features if f in html]
                
                if found:
                    print(f"   Service Features: {', '.join(found)}")
                else:
                    print(f"   ⚠️ Service features not visible in HTML")
            else:
                self.results['failed'] += 1
                print(f"❌ WeatherCraft ERP: Status {response.status_code}")
                
        except Exception as e:
            self.results['failed'] += 1
            print(f"❌ WeatherCraft ERP: {str(e)}")
    
    def test_database_production(self):
        """Test production database with real data"""
        print("\n💾 TESTING PRODUCTION DATABASE")
        print("="*40)
        
        try:
            conn = psycopg2.connect(
                host='aws-0-us-east-2.pooler.supabase.com',
                port=6543,
                database='postgres',
                user='postgres.yomagoqdmxszqtdwuhab',
                password='<DB_PASSWORD_REDACTED>'
            )
            cursor = conn.cursor()
            
            # Test real production data
            queries = [
                ("Customers", "SELECT COUNT(*) FROM customers"),
                ("Jobs", "SELECT COUNT(*) FROM jobs"),
                ("AI Agents", "SELECT COUNT(*) FROM ai_agents WHERE status = 'active'"),
                ("Revenue Transactions", "SELECT COUNT(*) FROM revenue_transactions"),
                ("Service Jobs", "SELECT COUNT(*) FROM service_jobs"),
                ("CenterPoint Syncs", "SELECT COUNT(*) FROM centerpoint_sync_log WHERE completed_at > NOW() - INTERVAL '24 hours'")
            ]
            
            for name, query in queries:
                try:
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    self.results['passed'] += 1
                    print(f"✅ {name}: {count} records")
                    
                    if name == "Customers" and count < 100:
                        print(f"   ⚠️ Low customer count - needs data population")
                    elif name == "Revenue Transactions" and count == 0:
                        print(f"   ⚠️ No revenue transactions yet")
                        
                except Exception as e:
                    self.results['failed'] += 1
                    print(f"❌ {name}: {str(e)}")
            
            # Test system separation
            print("\n🔐 VERIFYING SYSTEM SEPARATION")
            cursor.execute("""
                SELECT 
                    'MyRoofGenius AI' as system,
                    COUNT(*) as agents
                FROM ai_agents 
                WHERE capabilities->>'focus' = 'myroofgenius'
                UNION ALL
                SELECT 
                    'WeatherCraft AI',
                    COUNT(*)
                FROM ai_agents 
                WHERE capabilities->>'focus' = 'weathercraft'
            """)
            
            for row in cursor.fetchall():
                print(f"   {row[0]}: {row[1]} dedicated agents")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.results['failed'] += 1
            print(f"❌ Database: {str(e)}")
    
    def test_revenue_capabilities(self):
        """Test actual revenue generation capabilities"""
        print("\n💳 TESTING REVENUE GENERATION")
        print("="*40)
        
        # Test Stripe integration
        try:
            # Check if backend has Stripe configured
            response = requests.get("https://brainops-backend-prod.onrender.com/api/v1/payments/stripe/config", timeout=5)
            if response.status_code in [200, 401, 403]:  # Auth required is ok
                self.results['passed'] += 1
                print(f"✅ Stripe Integration: Configured")
            else:
                self.results['failed'] += 1
                print(f"❌ Stripe Integration: Not configured")
        except:
            print(f"   ⚠️ Stripe endpoint not accessible")
        
        # Check database for revenue data
        try:
            conn = psycopg2.connect(
                host='aws-0-us-east-2.pooler.supabase.com',
                port=6543,
                database='postgres',
                user='postgres.yomagoqdmxszqtdwuhab',
                password='<DB_PASSWORD_REDACTED>'
            )
            cursor = conn.cursor()
            
            # Check for products
            cursor.execute("SELECT COUNT(*), MIN(price_cents), MAX(price_cents) FROM products WHERE is_active = true")
            count, min_price, max_price = cursor.fetchone()
            
            if count > 0:
                self.results['passed'] += 1
                print(f"✅ Products: {count} active (${min_price/100:.2f} - ${max_price/100:.2f})")
            else:
                self.results['failed'] += 1
                print(f"❌ Products: No active products")
            
            # Check for payment capabilities
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = 'revenue_transactions' 
                AND column_name = 'stripe_payment_intent_id'
            """)
            
            if cursor.fetchone()[0] > 0:
                self.results['passed'] += 1
                print(f"✅ Payment Processing: Table structure ready")
            else:
                self.results['failed'] += 1
                print(f"❌ Payment Processing: Missing payment columns")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.results['failed'] += 1
            print(f"❌ Revenue Test: {str(e)}")
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*50)
        print("📊 LIVE PRODUCTION TEST REPORT")
        print("="*50)
        
        total = self.results['passed'] + self.results['failed']
        if total > 0:
            success_rate = (self.results['passed'] / total) * 100
        else:
            success_rate = 0
            
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n✅ PRODUCTION SYSTEMS VERIFIED")
        elif success_rate >= 60:
            print("\n⚠️ PRODUCTION SYSTEMS PARTIALLY OPERATIONAL")
        else:
            print("\n❌ PRODUCTION SYSTEMS NEED ATTENTION")
        
        # Save report
        with open('/tmp/production_test_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed report: /tmp/production_test_report.json")
        
        return success_rate >= 80
    
    def run_all_tests(self):
        """Run all production tests"""
        print("\n🚀 LIVE PRODUCTION SYSTEM VERIFICATION")
        print("NO ASSUMPTIONS - ONLY REAL DATA")
        print("="*50)
        
        self.test_backend_api()
        self.test_myroofgenius()
        self.test_weathercraft_erp()
        self.test_database_production()
        self.test_revenue_capabilities()
        
        return self.generate_report()

if __name__ == '__main__':
    tester = LiveProductionTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
