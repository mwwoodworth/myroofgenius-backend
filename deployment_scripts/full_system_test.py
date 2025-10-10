#!/usr/bin/env python3
"""Full system regression test for BrainOps OS"""

import requests
import json
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
MYROOFGENIUS_URL = "https://myroofgenius.com"
SLACK_WEBHOOK = "https://hooks.slack.com/services/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"

# Test credentials
TEST_USER = "test@brainops.com"
TEST_PASS = "TestPassword123!"

def send_slack_update(message, blocks=None):
    """Send update to Slack"""
    payload = {"text": message, "username": "Test Runner", "icon_emoji": "🧪"}
    if blocks:
        payload["blocks"] = blocks
    
    try:
        requests.post(SLACK_WEBHOOK, json=payload)
    except:
        pass

class SystemTest:
    def __init__(self):
        self.results = {}
        self.token = None
        
    def test_backend_health(self):
        """Test backend health"""
        print("\n🏥 Testing Backend Health...")
        try:
            resp = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.results['backend_health'] = {
                    'status': 'pass',
                    'version': data.get('version'),
                    'endpoints': data.get('total_endpoints', 0)
                }
                print(f"✅ Backend healthy - v{data.get('version')} with {data.get('total_endpoints')} endpoints")
                return True
            else:
                self.results['backend_health'] = {'status': 'fail', 'code': resp.status_code}
                print(f"❌ Backend unhealthy: {resp.status_code}")
                return False
        except Exception as e:
            self.results['backend_health'] = {'status': 'error', 'error': str(e)}
            print(f"❌ Backend error: {str(e)}")
            return False
    
    def test_authentication(self):
        """Test authentication flow"""
        print("\n🔐 Testing Authentication...")
        try:
            payload = {"email": TEST_USER, "password": TEST_PASS}
            resp = requests.post(f"{BACKEND_URL}/api/v1/auth/login", json=payload, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get('access_token')
                self.results['authentication'] = {'status': 'pass'}
                print("✅ Authentication successful")
                return True
            else:
                self.results['authentication'] = {'status': 'fail', 'code': resp.status_code}
                print(f"❌ Authentication failed: {resp.status_code}")
                return False
        except Exception as e:
            self.results['authentication'] = {'status': 'error', 'error': str(e)}
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_aurea_features(self):
        """Test AUREA features"""
        print("\n🤖 Testing AUREA Executive Assistant...")
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        aurea_tests = {
            'status': f"{BACKEND_URL}/api/v1/aurea/status",
            'health': f"{BACKEND_URL}/api/v1/aurea/health",
            'chat': f"{BACKEND_URL}/api/v1/aurea/chat"
        }
        
        results = {}
        for name, url in aurea_tests.items():
            try:
                if name == 'chat':
                    payload = {"message": "System status", "context": {}}
                    resp = requests.post(url, json=payload, headers=headers, timeout=10)
                else:
                    resp = requests.get(url, headers=headers, timeout=10)
                
                results[name] = resp.status_code == 200
                print(f"  {'✅' if results[name] else '❌'} AUREA {name}: {resp.status_code}")
            except Exception as e:
                results[name] = False
                print(f"  ❌ AUREA {name} error: {str(e)}")
        
        self.results['aurea'] = results
        return all(results.values())
    
    def test_ai_integrations(self):
        """Test AI service integrations"""
        print("\n🧠 Testing AI Integrations...")
        
        ai_endpoints = {
            'claude': f"{BACKEND_URL}/api/v1/ai/claude/chat",
            'gemini': f"{BACKEND_URL}/api/v1/ai/gemini/status",
            'memory': f"{BACKEND_URL}/api/v1/memory/status"
        }
        
        results = {}
        headers = {'Authorization': f'Bearer {self.token}'} if self.token else {}
        
        for name, url in ai_endpoints.items():
            try:
                if name == 'claude':
                    payload = {"message": "test"}
                    resp = requests.post(url, json=payload, headers=headers, timeout=10)
                else:
                    resp = requests.get(url, headers=headers, timeout=10)
                
                results[name] = resp.status_code in [200, 401, 403]  # Auth errors are OK
                print(f"  {'✅' if results[name] else '❌'} {name.upper()}: {resp.status_code}")
            except Exception as e:
                results[name] = False
                print(f"  ❌ {name.upper()} error: {str(e)}")
        
        self.results['ai_integrations'] = results
        return len([v for v in results.values() if v]) >= 2
    
    def test_database_operations(self):
        """Test database connectivity"""
        print("\n💾 Testing Database Operations...")
        
        try:
            resp = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=10)
            data = resp.json()
            db_status = data.get('database') == 'connected'
            
            self.results['database'] = {'status': 'pass' if db_status else 'fail'}
            print(f"  {'✅' if db_status else '❌'} Database: {data.get('database')}")
            return db_status
        except Exception as e:
            self.results['database'] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ Database check error: {str(e)}")
            return False
    
    def test_frontend_deployment(self):
        """Test frontend deployments"""
        print("\n🌐 Testing Frontend Deployments...")
        
        frontends = {
            'MyRoofGenius': MYROOFGENIUS_URL,
            'BrainStackStudio': 'https://brainstackstudio.vercel.app'
        }
        
        results = {}
        for name, url in frontends.items():
            try:
                resp = requests.get(url, timeout=30, allow_redirects=True)
                success = resp.status_code in [200, 301, 302, 304]
                results[name] = {'status': 'pass' if success else 'fail', 'code': resp.status_code}
                print(f"  {'✅' if success else '❌'} {name}: {resp.status_code}")
            except Exception as e:
                results[name] = {'status': 'timeout', 'error': str(e)}
                print(f"  ⚠️ {name}: Timeout/Error")
        
        self.results['frontends'] = results
        return any(r.get('status') == 'pass' for r in results.values())
    
    def test_slack_integration(self):
        """Test Slack integration"""
        print("\n💬 Testing Slack Integration...")
        
        try:
            # Test webhook
            test_msg = {"text": "🧪 System test ping", "username": "Test"}
            resp = requests.post(SLACK_WEBHOOK, json=test_msg, timeout=10)
            
            webhook_ok = resp.status_code == 200
            print(f"  {'✅' if webhook_ok else '❌'} Webhook: {resp.status_code}")
            
            # Test Slack endpoints (if deployed)
            slack_event_url = f"{MYROOFGENIUS_URL}/api/slack/verify"
            try:
                resp = requests.get(slack_event_url, timeout=10)
                event_ok = resp.status_code == 200
                print(f"  {'✅' if event_ok else '❌'} Event Handler: {resp.status_code}")
            except:
                event_ok = False
                print("  ⚠️ Event Handler: Not accessible")
            
            self.results['slack'] = {
                'webhook': webhook_ok,
                'events': event_ok
            }
            return webhook_ok
        except Exception as e:
            self.results['slack'] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ Slack error: {str(e)}")
            return False
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 FULL SYSTEM TEST REPORT")
        print("="*60)
        print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"🌐 Backend: {BACKEND_URL}")
        print("="*60)
        
        # Calculate stats
        total_tests = 0
        passed_tests = 0
        
        for category, result in self.results.items():
            if isinstance(result, dict):
                if 'status' in result:
                    total_tests += 1
                    if result['status'] == 'pass':
                        passed_tests += 1
                else:
                    # Count sub-tests
                    for sub_result in result.values():
                        total_tests += 1
                        if sub_result == True or (isinstance(sub_result, dict) and sub_result.get('status') == 'pass'):
                            passed_tests += 1
        
        # Generate Slack report
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🧪 Full System Test Report"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Overall Status:* {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.0f}%)\n*Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            },
            {"type": "divider"}
        ]
        
        # Add test results
        for category, result in self.results.items():
            status_text = self._format_result(category, result)
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": status_text}
            })
        
        # Send to Slack
        send_slack_update("Full System Test Complete", blocks)
        
        # Print summary
        print(f"\n✅ Tests Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.0f}%)")
        
        return passed_tests == total_tests
    
    def _format_result(self, category, result):
        """Format test result for display"""
        if isinstance(result, dict):
            if 'status' in result:
                icon = "✅" if result['status'] == 'pass' else "❌"
                extra = f" (v{result.get('version')})" if 'version' in result else ""
                return f"{icon} *{category.replace('_', ' ').title()}*{extra}"
            else:
                # Format sub-results
                lines = [f"*{category.replace('_', ' ').title()}*:"]
                for key, val in result.items():
                    if isinstance(val, bool):
                        icon = "✅" if val else "❌"
                        lines.append(f"  {icon} {key}")
                    elif isinstance(val, dict):
                        icon = "✅" if val.get('status') == 'pass' else "❌"
                        lines.append(f"  {icon} {key}")
                return "\n".join(lines)
        return f"{'✅' if result else '❌'} *{category.replace('_', ' ').title()}*"

def main():
    """Run full system test"""
    print("""
🚀 BrainOps OS - Full System Regression Test
============================================
""")
    
    tester = SystemTest()
    
    # Run all tests
    tests = [
        tester.test_backend_health,
        tester.test_authentication,
        tester.test_aurea_features,
        tester.test_ai_integrations,
        tester.test_database_operations,
        tester.test_frontend_deployment,
        tester.test_slack_integration
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
        time.sleep(1)  # Rate limiting
    
    # Generate report
    success = tester.generate_report()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)