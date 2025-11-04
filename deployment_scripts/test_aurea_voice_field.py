#!/usr/bin/env python3
"""
AUREA Voice and Field Test Suite
Tests voice functionality, fallback, and UI integration
"""

import requests
import json
from datetime import datetime
import time

BACKEND_URL = "https://brainops-backend-prod.onrender.com"
FRONTEND_URL = "https://myroofgenius-live-git-main-matts-projects-fe7d7976.vercel.app"

# Test credentials
TEST_USER = {"email": "test@brainops.com", "password": "TestPassword123!"}

class AureaFieldTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "voice_tests": {},
            "ui_integration": {},
            "fallback_tests": {},
            "field_workflows": {},
            "issues": []
        }
    
    def authenticate(self):
        """Get auth token"""
        try:
            resp = self.session.post(f"{BACKEND_URL}/api/v1/auth/login", json=TEST_USER)
            if resp.status_code == 200:
                data = resp.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                return True
        except Exception as e:
            print(f"Auth failed: {e}")
        return False
    
    def test_voice_endpoints(self):
        """Test AUREA voice capabilities"""
        print("\n🎤 Testing AUREA Voice Endpoints...")
        
        voice_tests = {
            "voice_status": f"{BACKEND_URL}/api/v1/aurea/voice/status",
            "voice_session": f"{BACKEND_URL}/api/v1/aurea/voice/session",
            "voice_synthesis": f"{BACKEND_URL}/api/v1/aurea/voice/synthesize"
        }
        
        for name, url in voice_tests.items():
            try:
                if "session" in name:
                    resp = self.session.post(url, json={
                        "user_id": "test_user",
                        "device": "field_test"
                    })
                elif "synthesis" in name:
                    resp = self.session.post(url, json={
                        "text": "Testing AUREA voice synthesis",
                        "voice": "default"
                    })
                else:
                    resp = self.session.get(url)
                
                success = resp.status_code in [200, 201]
                self.results["voice_tests"][name] = {
                    "url": url,
                    "status": resp.status_code,
                    "success": success
                }
                
                print(f"  - {name}: {'✅' if success else '❌'} (Status: {resp.status_code})")
                
                if not success:
                    self.results["issues"].append({
                        "category": "voice",
                        "test": name,
                        "issue": f"Endpoint returned {resp.status_code}",
                        "severity": "high"
                    })
                    
            except Exception as e:
                print(f"  - {name}: ❌ ERROR: {str(e)}")
                self.results["voice_tests"][name] = {"error": str(e)}
    
    def test_ai_fallback(self):
        """Test AI provider fallback chain"""
        print("\n🔄 Testing AI Fallback Chain...")
        
        # Test primary (Claude/Sonnet)
        providers = [
            ("claude", "Primary (Sonnet)"),
            ("openai", "Fallback 1 (ChatGPT)"),
            ("gemini", "Fallback 2 (Gemini)")
        ]
        
        for provider, desc in providers:
            try:
                # Test via AUREA with specific provider
                resp = self.session.post(f"{BACKEND_URL}/api/v1/aurea/chat", json={
                    "message": f"Test fallback with {provider}",
                    "provider_hint": provider
                })
                
                success = resp.status_code == 200
                response_data = resp.json() if success else {}
                
                self.results["fallback_tests"][provider] = {
                    "description": desc,
                    "status": resp.status_code,
                    "success": success,
                    "provider_used": response_data.get("provider", "unknown")
                }
                
                print(f"  - {desc}: {'✅' if success else '❌'}")
                
            except Exception as e:
                print(f"  - {desc}: ❌ ERROR: {str(e)}")
                self.results["fallback_tests"][provider] = {"error": str(e)}
        
        # Test automatic fallback
        print("\n  Testing automatic fallback...")
        try:
            resp = self.session.post(f"{BACKEND_URL}/api/v1/aurea/chat", json={
                "message": "Test automatic fallback",
                "force_fallback": True
            })
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"  - Automatic fallback: ✅ (Used: {data.get('provider', 'unknown')})")
                self.results["fallback_tests"]["automatic"] = {
                    "success": True,
                    "provider": data.get("provider")
                }
            else:
                print(f"  - Automatic fallback: ❌ (Status: {resp.status_code})")
                self.results["issues"].append({
                    "category": "fallback",
                    "test": "automatic",
                    "issue": f"Fallback failed with status {resp.status_code}",
                    "severity": "critical"
                })
                
        except Exception as e:
            print(f"  - Automatic fallback: ❌ ERROR: {str(e)}")
    
    def test_ui_integration(self):
        """Test AUREA UI integration on pages"""
        print("\n🖥️  Testing AUREA UI Integration...")
        
        pages_to_test = [
            ("", "Homepage"),
            ("/dashboard", "Dashboard"),
            ("/aurea-dashboard", "AUREA Dashboard"),
            ("/marketplace", "Marketplace")
        ]
        
        for path, name in pages_to_test:
            url = f"{FRONTEND_URL}{path}"
            try:
                resp = requests.get(url, timeout=10)
                
                # Check if AUREA components are present
                aurea_indicators = [
                    "AUREA" in resp.text,
                    "aurea" in resp.text.lower(),
                    "voice" in resp.text.lower(),
                    "Ask AUREA" in resp.text
                ]
                
                aurea_present = any(aurea_indicators)
                
                self.results["ui_integration"][name] = {
                    "url": url,
                    "status": resp.status_code,
                    "aurea_present": aurea_present,
                    "indicators_found": sum(aurea_indicators)
                }
                
                print(f"  - {name}: {'✅' if aurea_present else '⚠️'} (AUREA indicators: {sum(aurea_indicators)}/4)")
                
                if not aurea_present:
                    self.results["issues"].append({
                        "category": "ui_integration",
                        "page": name,
                        "issue": "AUREA components not found on page",
                        "severity": "medium"
                    })
                    
            except Exception as e:
                print(f"  - {name}: ❌ ERROR: {str(e)}")
                self.results["ui_integration"][name] = {"error": str(e)}
    
    def test_field_workflows(self):
        """Test field-specific workflows"""
        print("\n🏗️  Testing Field Workflows...")
        
        workflows = [
            {
                "name": "Job Creation via Voice",
                "endpoint": f"{BACKEND_URL}/api/v1/aurea/command",
                "data": {
                    "command": "create new roofing job for 123 Main Street",
                    "type": "voice"
                }
            },
            {
                "name": "Estimate Generation",
                "endpoint": f"{BACKEND_URL}/api/v1/aurea/command",
                "data": {
                    "command": "generate estimate for 2500 sq ft shingle roof",
                    "type": "voice"
                }
            },
            {
                "name": "Photo Analysis",
                "endpoint": f"{BACKEND_URL}/api/v1/aurea/analyze",
                "data": {
                    "type": "roof_inspection",
                    "description": "Analyze roof condition from field photo"
                }
            }
        ]
        
        for workflow in workflows:
            try:
                resp = self.session.post(workflow["endpoint"], json=workflow["data"])
                success = resp.status_code in [200, 201]
                
                self.results["field_workflows"][workflow["name"]] = {
                    "endpoint": workflow["endpoint"],
                    "status": resp.status_code,
                    "success": success
                }
                
                print(f"  - {workflow['name']}: {'✅' if success else '❌'}")
                
                if not success:
                    self.results["issues"].append({
                        "category": "field_workflow",
                        "workflow": workflow["name"],
                        "issue": f"Workflow failed with status {resp.status_code}",
                        "severity": "high"
                    })
                    
            except Exception as e:
                print(f"  - {workflow['name']}: ❌ ERROR: {str(e)}")
                self.results["field_workflows"][workflow["name"]] = {"error": str(e)}
    
    def test_persistent_memory(self):
        """Test memory persistence for field work"""
        print("\n💾 Testing Persistent Memory...")
        
        test_id = f"field_test_{int(time.time())}"
        
        # Store field data
        try:
            resp = self.session.post(f"{BACKEND_URL}/api/v1/memory/create", json={
                "content": f"Field test job at 123 Main St - {test_id}",
                "memory_type": "field_job",
                "metadata": {
                    "job_id": test_id,
                    "location": "123 Main St",
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            if resp.status_code in [200, 201]:
                print("  - Memory storage: ✅")
                
                # Wait and retrieve
                time.sleep(1)
                
                resp2 = self.session.post(f"{BACKEND_URL}/api/v1/memory/search", json={
                    "query": test_id
                })
                
                if resp2.status_code == 200:
                    memories = resp2.json().get("results", [])
                    if memories:
                        print("  - Memory retrieval: ✅")
                        self.results["field_workflows"]["memory_persistence"] = {
                            "success": True,
                            "test_id": test_id
                        }
                    else:
                        print("  - Memory retrieval: ❌ (No results)")
                        self.results["issues"].append({
                            "category": "memory",
                            "issue": "Memory created but not retrievable",
                            "severity": "high"
                        })
            else:
                print("  - Memory storage: ❌")
                
        except Exception as e:
            print(f"  - Memory test: ❌ ERROR: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive field test report"""
        print("\n" + "=" * 60)
        print("📊 AUREA FIELD TEST REPORT")
        print("=" * 60)
        
        print(f"\n📅 Test Date: {self.results['timestamp']}")
        
        # Summary
        total_issues = len(self.results["issues"])
        critical_issues = len([i for i in self.results["issues"] if i.get("severity") == "critical"])
        high_issues = len([i for i in self.results["issues"] if i.get("severity") == "high"])
        
        print(f"\n⚠️  Issues Found: {total_issues}")
        print(f"  - Critical: {critical_issues}")
        print(f"  - High: {high_issues}")
        print(f"  - Medium: {total_issues - critical_issues - high_issues}")
        
        # Voice readiness
        voice_ready = all(t.get("success", False) for t in self.results["voice_tests"].values())
        print(f"\n🎤 Voice Ready: {'YES' if voice_ready else 'NO'}")
        
        # Fallback readiness
        fallback_ready = len([t for t in self.results["fallback_tests"].values() if t.get("success", False)]) >= 2
        print(f"🔄 Fallback Ready: {'YES' if fallback_ready else 'PARTIAL'}")
        
        # Field readiness
        field_ready = len([w for w in self.results["field_workflows"].values() if w.get("success", False)]) >= 2
        print(f"🏗️  Field Ready: {'YES' if field_ready else 'NO'}")
        
        # Critical issues
        if critical_issues > 0:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in self.results["issues"]:
                if issue.get("severity") == "critical":
                    print(f"  - {issue['category']}: {issue['issue']}")
        
        # Save report
        with open("/home/mwwoodworth/code/AUREA_FIELD_TEST_REPORT.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: AUREA_FIELD_TEST_REPORT.json")
        
        # Final verdict
        print("\n" + "=" * 60)
        if critical_issues == 0 and voice_ready and fallback_ready and field_ready:
            print("✅ AUREA IS FIELD-READY!")
        else:
            print("❌ AUREA NEEDS FIXES BEFORE FIELD USE")
        print("=" * 60)
        
        # Action items
        if self.results["issues"]:
            print("\n🔧 ACTION ITEMS:")
            for i, issue in enumerate(self.results["issues"][:5], 1):
                print(f"{i}. Fix {issue['category']}: {issue['issue']}")
    
    def run_all_tests(self):
        """Run all AUREA field tests"""
        print("🤖 AUREA Voice and Field Test Suite")
        print("=" * 60)
        
        # Authenticate first
        print("🔐 Authenticating...", end=" ")
        if not self.authenticate():
            print("❌ FAILED - Cannot continue")
            return
        print("✅ SUCCESS")
        
        # Run tests
        self.test_voice_endpoints()
        self.test_ai_fallback()
        self.test_ui_integration()
        self.test_field_workflows()
        self.test_persistent_memory()
        
        # Generate report
        self.generate_report()

if __name__ == "__main__":
    tester = AureaFieldTest()
    tester.run_all_tests()