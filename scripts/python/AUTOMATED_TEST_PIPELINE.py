#!/usr/bin/env python3
"""
Automated Testing Pipeline for BrainOps
Runs comprehensive tests on all systems
"""

import requests
import psycopg2
import json
import time
from datetime import datetime
import subprocess

class AutomatedTestPipeline:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def test_api_health(self):
        """Test API health endpoints"""
        print("\n🧪 Testing API Health...")
        
        endpoints = [
            'https://brainops-backend-prod.onrender.com/api/v1/health',
            'https://myroofgenius.com',
            'https://weathercraft-erp.vercel.app'
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    self.passed_tests += 1
                    print(f"  ✅ {endpoint}: OK")
                    self.test_results.append({
                        'test': f'API Health: {endpoint}',
                        'status': 'PASSED',
                        'response_time': response.elapsed.total_seconds()
                    })
                else:
                    self.failed_tests += 1
                    print(f"  ❌ {endpoint}: Status {response.status_code}")
                    self.test_results.append({
                        'test': f'API Health: {endpoint}',
                        'status': 'FAILED',
                        'error': f'Status {response.status_code}'
                    })
            except Exception as e:
                self.failed_tests += 1
                print(f"  ❌ {endpoint}: {str(e)}")
                self.test_results.append({
                    'test': f'API Health: {endpoint}',
                    'status': 'FAILED',
                    'error': str(e)
                })
            
            self.total_tests += 1
    
    def test_database_connectivity(self):
        """Test database connectivity and queries"""
        print("\n🧪 Testing Database...")
        
        try:
            conn = psycopg2.connect(
                host='aws-0-us-east-2.pooler.supabase.com',
                port=6543,
                database='postgres',
                user='postgres.yomagoqdmxszqtdwuhab',
                password='<DB_PASSWORD_REDACTED>'
            )
            cursor = conn.cursor()
            
            # Test basic queries
            tests = [
                ("SELECT COUNT(*) FROM customers", "Customer count"),
                ("SELECT COUNT(*) FROM jobs", "Job count"),
                ("SELECT COUNT(*) FROM ai_agents", "AI Agents count"),
                ("SELECT COUNT(*) FROM centerpoint_sync_log WHERE started_at > NOW() - INTERVAL '1 hour'", "Recent syncs")
            ]
            
            for query, test_name in tests:
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()[0]
                    self.passed_tests += 1
                    print(f"  ✅ {test_name}: {result}")
                    self.test_results.append({
                        'test': f'Database: {test_name}',
                        'status': 'PASSED',
                        'result': result
                    })
                except Exception as e:
                    self.failed_tests += 1
                    print(f"  ❌ {test_name}: {str(e)}")
                    self.test_results.append({
                        'test': f'Database: {test_name}',
                        'status': 'FAILED',
                        'error': str(e)
                    })
                
                self.total_tests += 1
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.failed_tests += 1
            print(f"  ❌ Database connection failed: {str(e)}")
            self.test_results.append({
                'test': 'Database Connection',
                'status': 'FAILED',
                'error': str(e)
            })
            self.total_tests += 1
    
    def test_docker_services(self):
        """Test Docker services"""
        print("\n🧪 Testing Docker Services...")
        
        try:
            result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            container = json.loads(line)
                            containers.append(container.get('Names', 'unknown'))
                        except:
                            pass
                
                if containers:
                    self.passed_tests += 1
                    print(f"  ✅ Docker running with {len(containers)} containers")
                    self.test_results.append({
                        'test': 'Docker Services',
                        'status': 'PASSED',
                        'containers': containers
                    })
                else:
                    print("  ⚠️ Docker running but no containers active")
                    self.test_results.append({
                        'test': 'Docker Services',
                        'status': 'WARNING',
                        'message': 'No active containers'
                    })
            else:
                self.failed_tests += 1
                print(f"  ❌ Docker command failed")
                self.test_results.append({
                    'test': 'Docker Services',
                    'status': 'FAILED',
                    'error': 'Docker command failed'
                })
                
        except Exception as e:
            self.failed_tests += 1
            print(f"  ❌ Docker test failed: {str(e)}")
            self.test_results.append({
                'test': 'Docker Services',
                'status': 'FAILED',
                'error': str(e)
            })
        
        self.total_tests += 1
    
    def test_monitoring_systems(self):
        """Test monitoring systems"""
        print("\n🧪 Testing Monitoring Systems...")
        
        # Check for running monitoring processes
        monitoring_processes = [
            'PERSISTENT_MONITORING_SYSTEM.py',
            'LOG_AGGREGATOR.py',
            'METRICS_DASHBOARD.py',
            'CENTERPOINT_24_7_SYNC_SERVICE.py'
        ]
        
        for process in monitoring_processes:
            try:
                result = subprocess.run(['pgrep', '-f', process], 
                                      capture_output=True)
                
                if result.returncode == 0:
                    self.passed_tests += 1
                    print(f"  ✅ {process}: Running")
                    self.test_results.append({
                        'test': f'Monitoring: {process}',
                        'status': 'PASSED'
                    })
                else:
                    self.failed_tests += 1
                    print(f"  ❌ {process}: Not running")
                    self.test_results.append({
                        'test': f'Monitoring: {process}',
                        'status': 'FAILED',
                        'error': 'Process not running'
                    })
            except Exception as e:
                self.failed_tests += 1
                print(f"  ❌ {process}: Check failed - {str(e)}")
                self.test_results.append({
                    'test': f'Monitoring: {process}',
                    'status': 'FAILED',
                    'error': str(e)
                })
            
            self.total_tests += 1
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*50)
        print("📊 TEST REPORT")
        print("="*50)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ({(self.passed_tests/self.total_tests*100):.1f}%)")
        print(f"Failed: {self.failed_tests} ({(self.failed_tests/self.total_tests*100):.1f}%)")
        
        # Save to file
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': self.total_tests,
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'success_rate': f"{(self.passed_tests/self.total_tests*100):.1f}%"
            },
            'results': self.test_results
        }
        
        with open('/tmp/test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: /tmp/test_report.json")
        
        # Return exit code based on results
        return 0 if self.failed_tests == 0 else 1
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n🚀 AUTOMATED TEST PIPELINE")
        print("="*50)
        
        self.test_api_health()
        self.test_database_connectivity()
        self.test_docker_services()
        self.test_monitoring_systems()
        
        return self.generate_report()

if __name__ == '__main__':
    pipeline = AutomatedTestPipeline()
    exit_code = pipeline.run_all_tests()
    exit(exit_code)
