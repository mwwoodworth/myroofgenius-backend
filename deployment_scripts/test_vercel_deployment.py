#!/usr/bin/env python3
"""
Test Vercel Deployment and UI Issues
"""

import requests
import json
from datetime import datetime
import re

VERCEL_URL = "https://myroofgenius-live-git-main-matts-projects-fe7d7976.vercel.app"
PRODUCTION_URL = "https://www.myroofgenius.com"

class VercelDeploymentTester:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "deployment_status": {},
            "ui_issues": [],
            "api_tests": {},
            "recommendations": []
        }
    
    def test_deployment_health(self):
        """Test if Vercel deployment is healthy"""
        print("🔍 Testing Vercel Deployment Health...")
        
        urls_to_test = {
            "vercel_home": VERCEL_URL,
            "vercel_login": f"{VERCEL_URL}/login",
            "vercel_register": f"{VERCEL_URL}/register",
            "vercel_dashboard": f"{VERCEL_URL}/dashboard",
            "production_home": PRODUCTION_URL,
            "production_login": f"{PRODUCTION_URL}/login"
        }
        
        for name, url in urls_to_test.items():
            try:
                resp = self.session.get(url, allow_redirects=True, timeout=10)
                status = resp.status_code
                
                # Check for common issues
                issues = []
                
                # Check if page has content
                if len(resp.text) < 1000:
                    issues.append("Page content too small - possible error")
                
                # Check for error indicators
                error_patterns = [
                    r"error",
                    r"Error",
                    r"failed to fetch",
                    r"Failed to fetch",
                    r"cannot find module",
                    r"Cannot find module",
                    r"undefined is not",
                    r"TypeError:",
                    r"ReferenceError:"
                ]
                
                for pattern in error_patterns:
                    if re.search(pattern, resp.text[:5000]):  # Check first 5KB
                        issues.append(f"Found error pattern: {pattern}")
                
                # Check for React hydration errors
                if "Hydration failed" in resp.text or "hydration mismatch" in resp.text.lower():
                    issues.append("React hydration error detected")
                
                # Check for proper HTML structure
                if "<html" not in resp.text or "<body" not in resp.text:
                    issues.append("Invalid HTML structure")
                
                self.results["deployment_status"][name] = {
                    "url": url,
                    "status_code": status,
                    "healthy": status == 200 and len(issues) == 0,
                    "issues": issues,
                    "content_length": len(resp.text)
                }
                
                print(f"  - {name}: {'✅' if status == 200 else '❌'} (Status: {status})")
                if issues:
                    for issue in issues:
                        print(f"    ⚠️  {issue}")
                        self.results["ui_issues"].append({
                            "page": name,
                            "issue": issue,
                            "severity": "high"
                        })
                
            except Exception as e:
                print(f"  - {name}: ❌ ERROR: {str(e)}")
                self.results["deployment_status"][name] = {
                    "url": url,
                    "healthy": False,
                    "error": str(e)
                }
                self.results["ui_issues"].append({
                    "page": name,
                    "issue": f"Failed to load: {str(e)}",
                    "severity": "critical"
                })
    
    def test_api_endpoints(self):
        """Test if API endpoints are accessible"""
        print("\n🔧 Testing API Endpoints...")
        
        # Test backend API
        backend_url = "https://brainops-backend-prod.onrender.com"
        api_tests = {
            "health": f"{backend_url}/api/v1/health",
            "aurea_status": f"{backend_url}/api/v1/aurea/status"
        }
        
        for name, url in api_tests.items():
            try:
                resp = requests.get(url, timeout=10)
                self.results["api_tests"][name] = {
                    "url": url,
                    "status": resp.status_code,
                    "success": resp.status_code == 200
                }
                print(f"  - {name}: {'✅' if resp.status_code == 200 else '❌'} (Status: {resp.status_code})")
            except Exception as e:
                print(f"  - {name}: ❌ ERROR: {str(e)}")
                self.results["api_tests"][name] = {
                    "url": url,
                    "success": False,
                    "error": str(e)
                }
    
    def check_console_errors(self):
        """Check for JavaScript console errors in page source"""
        print("\n🐛 Checking for JavaScript Errors...")
        
        try:
            resp = self.session.get(VERCEL_URL)
            
            # Look for common JS error patterns
            js_error_patterns = [
                r"console\.error",
                r"throw new Error",
                r"uncaught",
                r"Uncaught",
                r"SyntaxError",
                r"ReferenceError",
                r"TypeError",
                r"Cannot read properties",
                r"is not defined",
                r"is not a function"
            ]
            
            js_errors_found = []
            for pattern in js_error_patterns:
                matches = re.findall(pattern, resp.text)
                if matches:
                    js_errors_found.append({
                        "pattern": pattern,
                        "count": len(matches)
                    })
            
            if js_errors_found:
                print("  ❌ JavaScript error patterns found:")
                for error in js_errors_found:
                    print(f"    - {error['pattern']}: {error['count']} occurrences")
                    self.results["ui_issues"].append({
                        "page": "homepage",
                        "issue": f"JS error pattern '{error['pattern']}' found {error['count']} times",
                        "severity": "high"
                    })
            else:
                print("  ✅ No obvious JavaScript errors detected")
            
        except Exception as e:
            print(f"  ❌ ERROR checking for JS errors: {str(e)}")
    
    def generate_recommendations(self):
        """Generate fix recommendations based on findings"""
        if self.results["ui_issues"]:
            critical_issues = [i for i in self.results["ui_issues"] if i["severity"] == "critical"]
            high_issues = [i for i in self.results["ui_issues"] if i["severity"] == "high"]
            
            if critical_issues:
                self.results["recommendations"].append({
                    "priority": "URGENT",
                    "action": "Fix critical deployment issues immediately",
                    "details": [i["issue"] for i in critical_issues]
                })
            
            if high_issues:
                self.results["recommendations"].append({
                    "priority": "HIGH",
                    "action": "Address JavaScript and UI errors",
                    "details": [i["issue"] for i in high_issues]
                })
            
            # Specific recommendations
            for issue in self.results["ui_issues"]:
                if "hydration" in issue["issue"].lower():
                    self.results["recommendations"].append({
                        "priority": "HIGH",
                        "action": "Fix React hydration mismatch",
                        "details": ["Ensure server and client render the same content", "Check for dynamic content without proper hydration boundaries"]
                    })
                elif "cannot find module" in issue["issue"].lower():
                    self.results["recommendations"].append({
                        "priority": "URGENT",
                        "action": "Fix missing module imports",
                        "details": ["Run 'npm install' to ensure all dependencies are installed", "Check import paths are correct"]
                    })
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "=" * 60)
        print("📊 VERCEL DEPLOYMENT TEST REPORT")
        print("=" * 60)
        
        print(f"\n📅 Test Date: {self.results['timestamp']}")
        print(f"🔗 Vercel URL: {VERCEL_URL}")
        
        # Deployment Status
        healthy_count = sum(1 for d in self.results["deployment_status"].values() if d.get("healthy", False))
        total_count = len(self.results["deployment_status"])
        
        print(f"\n🚀 Deployment Health: {healthy_count}/{total_count} pages healthy")
        
        # Issues Summary
        critical_issues = [i for i in self.results["ui_issues"] if i["severity"] == "critical"]
        high_issues = [i for i in self.results["ui_issues"] if i["severity"] == "high"]
        
        print(f"\n⚠️  Issues Found:")
        print(f"  - Critical: {len(critical_issues)}")
        print(f"  - High: {len(high_issues)}")
        
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"  - {issue['page']}: {issue['issue']}")
        
        if high_issues:
            print("\n⚠️  HIGH PRIORITY ISSUES:")
            for issue in high_issues[:5]:  # Show first 5
                print(f"  - {issue['page']}: {issue['issue']}")
        
        # Recommendations
        if self.results["recommendations"]:
            print("\n🔧 RECOMMENDATIONS:")
            for rec in self.results["recommendations"]:
                print(f"\n[{rec['priority']}] {rec['action']}")
                for detail in rec["details"][:3]:  # Show first 3 details
                    print(f"  - {detail}")
        
        # Save report
        with open("/home/mwwoodworth/code/VERCEL_DEPLOYMENT_REPORT.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: VERCEL_DEPLOYMENT_REPORT.json")
        
        # Final verdict
        print("\n" + "=" * 60)
        if len(critical_issues) == 0 and healthy_count == total_count:
            print("✅ DEPLOYMENT TEST PASSED - Site is healthy")
        else:
            print("❌ DEPLOYMENT TEST FAILED - Issues need immediate attention")
        print("=" * 60)
        
        return len(critical_issues) == 0
    
    def run_all_tests(self):
        """Run all deployment tests"""
        print("🚀 Vercel Deployment Test Suite")
        print("=" * 60)
        
        # Test deployment health
        self.test_deployment_health()
        
        # Test API endpoints
        self.test_api_endpoints()
        
        # Check for JS errors
        self.check_console_errors()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Generate report
        return self.generate_report()

if __name__ == "__main__":
    tester = VercelDeploymentTester()
    success = tester.run_all_tests()
    
    if not success:
        print("\n⚠️  IMMEDIATE ACTION REQUIRED:")
        print("1. Check Vercel build logs for errors")
        print("2. Fix any missing imports or modules")
        print("3. Test locally before deploying")
        print("4. Re-run this test after fixes")