#!/usr/bin/env python3
"""
MyRoofGenius UI/UX Test Suite
Tests for layout issues, overlaps, broken components
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

VERCEL_URL = "https://myroofgenius-live-git-main-matts-projects-fe7d7976.vercel.app"
PRODUCTION_URL = "https://www.myroofgenius.com"

class UIUXTester:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "issues_found": [],
            "screenshots_needed": []
        }
    
    def test_page_load_and_structure(self, url, page_name):
        """Test if page loads and has proper structure"""
        try:
            resp = self.session.get(url)
            if resp.status_code != 200:
                self.results["issues_found"].append({
                    "page": page_name,
                    "issue": f"Page returned {resp.status_code}",
                    "severity": "critical"
                })
                return False
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Check for common UI issues
            issues = []
            
            # Check for viewport meta tag
            viewport = soup.find('meta', {'name': 'viewport'})
            if not viewport:
                issues.append("Missing viewport meta tag - mobile layout will break")
            
            # Check for overlapping elements (common class names)
            overlapping_classes = ['fixed', 'absolute', 'sticky']
            elements_with_positioning = []
            for cls in overlapping_classes:
                elements = soup.find_all(class_=lambda x: x and cls in x)
                elements_with_positioning.extend([(cls, len(elements))])
            
            if any(count > 5 for _, count in elements_with_positioning):
                issues.append("Many fixed/absolute positioned elements - check for overlaps")
            
            # Check for proper container structure
            main_container = soup.find('main') or soup.find('div', {'role': 'main'})
            if not main_container:
                issues.append("No main content container found")
            
            # Check for accessibility
            buttons_without_text = soup.find_all('button', string='')
            if buttons_without_text:
                issues.append(f"{len(buttons_without_text)} buttons without text labels")
            
            # Check for images without alt text
            images_without_alt = soup.find_all('img', alt='')
            if images_without_alt:
                issues.append(f"{len(images_without_alt)} images without alt text")
            
            self.results["tests"][page_name] = {
                "status": "passed" if not issues else "issues_found",
                "issues": issues,
                "elements_with_positioning": elements_with_positioning
            }
            
            if issues:
                self.results["screenshots_needed"].append({
                    "page": page_name,
                    "url": url,
                    "reason": "UI/UX issues detected"
                })
            
            return len(issues) == 0
            
        except Exception as e:
            self.results["tests"][page_name] = {
                "status": "error",
                "error": str(e)
            }
            return False
    
    def test_responsive_design(self, url, page_name):
        """Test mobile responsiveness"""
        mobile_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        }
        
        try:
            resp = self.session.get(url, headers=mobile_headers)
            if resp.status_code == 200:
                # Check if mobile styles are present
                has_responsive = 'max-width' in resp.text or 'media' in resp.text
                
                self.results["tests"][f"{page_name}_mobile"] = {
                    "status": "passed" if has_responsive else "warning",
                    "responsive_indicators": has_responsive
                }
                
                if not has_responsive:
                    self.results["issues_found"].append({
                        "page": page_name,
                        "issue": "No responsive design indicators found",
                        "severity": "high"
                    })
                
                return has_responsive
        except Exception as e:
            self.results["tests"][f"{page_name}_mobile"] = {
                "status": "error",
                "error": str(e)
            }
        return False
    
    def test_critical_pages(self):
        """Test all critical pages"""
        pages = [
            ("", "Homepage"),
            ("/login", "Login"),
            ("/register", "Register"),
            ("/dashboard", "Dashboard"),
            ("/marketplace", "Marketplace"),
            ("/about", "About"),
            ("/contact", "Contact")
        ]
        
        for path, name in pages:
            print(f"\n🔍 Testing {name}...", flush=True)
            
            # Test Vercel deployment
            vercel_url = f"{VERCEL_URL}{path}"
            print(f"  - Vercel: {vercel_url}", end=" ", flush=True)
            vercel_ok = self.test_page_load_and_structure(vercel_url, f"{name}_vercel")
            print("✅" if vercel_ok else "❌")
            
            # Test production
            prod_url = f"{PRODUCTION_URL}{path}"
            print(f"  - Production: {prod_url}", end=" ", flush=True)
            prod_ok = self.test_page_load_and_structure(prod_url, f"{name}_production")
            print("✅" if prod_ok else "❌")
            
            # Test mobile responsiveness
            print(f"  - Mobile test:", end=" ", flush=True)
            mobile_ok = self.test_responsive_design(vercel_url, f"{name}_vercel")
            print("✅" if mobile_ok else "⚠️")
    
    def check_javascript_errors(self):
        """Check for JavaScript console errors"""
        # This would require a headless browser like Selenium
        # For now, we'll check if critical JS files load
        try:
            resp = self.session.get(VERCEL_URL)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find all script tags
            scripts = soup.find_all('script', src=True)
            broken_scripts = []
            
            for script in scripts[:5]:  # Check first 5 scripts
                script_url = script['src']
                if not script_url.startswith('http'):
                    script_url = f"{VERCEL_URL}{script_url}"
                
                try:
                    script_resp = self.session.head(script_url, timeout=5)
                    if script_resp.status_code != 200:
                        broken_scripts.append(script_url)
                except:
                    broken_scripts.append(script_url)
            
            self.results["tests"]["javascript_loading"] = {
                "status": "passed" if not broken_scripts else "failed",
                "broken_scripts": broken_scripts
            }
            
            if broken_scripts:
                self.results["issues_found"].append({
                    "page": "Global",
                    "issue": f"{len(broken_scripts)} JavaScript files failed to load",
                    "severity": "critical"
                })
            
        except Exception as e:
            self.results["tests"]["javascript_loading"] = {
                "status": "error",
                "error": str(e)
            }
    
    def generate_report(self):
        """Generate comprehensive UI/UX test report"""
        print("\n" + "=" * 60)
        print("📊 MYROOFGENIUS UI/UX TEST REPORT")
        print("=" * 60)
        
        print(f"\n📅 Test Date: {self.results['timestamp']}")
        print(f"🔗 Vercel URL: {VERCEL_URL}")
        print(f"🔗 Production URL: {PRODUCTION_URL}")
        
        # Summary of issues
        critical_issues = [i for i in self.results["issues_found"] if i["severity"] == "critical"]
        high_issues = [i for i in self.results["issues_found"] if i["severity"] == "high"]
        
        print(f"\n⚠️  Issues Found:")
        print(f"  - Critical: {len(critical_issues)}")
        print(f"  - High: {len(high_issues)}")
        print(f"  - Total: {len(self.results['issues_found'])}")
        
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"  - {issue['page']}: {issue['issue']}")
        
        if high_issues:
            print("\n⚠️  HIGH PRIORITY ISSUES:")
            for issue in high_issues:
                print(f"  - {issue['page']}: {issue['issue']}")
        
        # Pages needing screenshots
        if self.results["screenshots_needed"]:
            print(f"\n📸 Screenshots Needed ({len(self.results['screenshots_needed'])}):")
            for screenshot in self.results["screenshots_needed"]:
                print(f"  - {screenshot['page']}: {screenshot['reason']}")
                print(f"    URL: {screenshot['url']}")
        
        # Save detailed report
        with open("/home/mwwoodworth/code/MYROOFGENIUS_UI_TEST_REPORT.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: MYROOFGENIUS_UI_TEST_REPORT.json")
        
        # Final verdict
        print("\n" + "=" * 60)
        if len(critical_issues) == 0 and len(high_issues) == 0:
            print("✅ UI/UX TEST PASSED - No critical issues found")
        else:
            print("❌ UI/UX TEST FAILED - Issues need to be fixed")
        print("=" * 60)
    
    def run_all_tests(self):
        """Run all UI/UX tests"""
        print("🎨 MyRoofGenius UI/UX Test Suite")
        print("=" * 60)
        
        # Test critical pages
        self.test_critical_pages()
        
        # Check JavaScript loading
        print("\n🔧 Testing JavaScript loading...", end=" ", flush=True)
        self.check_javascript_errors()
        print("Done")
        
        # Generate report
        self.generate_report()

if __name__ == "__main__":
    tester = UIUXTester()
    tester.run_all_tests()