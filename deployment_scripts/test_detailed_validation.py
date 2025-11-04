#!/usr/bin/env python3
"""
Detailed validation script based on external audit findings
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Tuple

BASE_URL = "https://myroofgenius.com"
API_URL = "https://brainops-backend-prod.onrender.com"

def test_signup_flow() -> Tuple[bool, str]:
    """Test the actual signup flow"""
    try:
        # Get signup page
        resp = requests.get(f"{BASE_URL}/signup", allow_redirects=True)
        if resp.status_code != 200:
            return False, f"Signup page returned {resp.status_code}"
        
        # Try to create a test account via API
        test_data = {
            "email": "test_validation@example.com",
            "password": "TestPassword123!",
            "full_name": "Test Validation"
        }
        
        resp = requests.post(
            f"{API_URL}/api/v1/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status_code == 201:
            return True, "Signup working correctly"
        elif resp.status_code == 409:
            return True, "Signup working (user already exists)"
        elif resp.status_code == 500:
            return False, "Server error during registration (500)"
        else:
            return False, f"Signup returned {resp.status_code}: {resp.text[:100]}"
            
    except Exception as e:
        return False, f"Signup test error: {str(e)}"

def test_estimator_features() -> Tuple[bool, str]:
    """Test if estimator features are enabled"""
    try:
        # Check material calculator
        resp = requests.get(f"{BASE_URL}/material-calculator", allow_redirects=True)
        if resp.status_code != 200:
            return False, f"Material calculator returned {resp.status_code}"
            
        # Check for disabled message
        if "disabled" in resp.text.lower() and "estimator" in resp.text.lower():
            return False, "Estimator features showing as disabled"
            
        # Check labor estimator
        resp = requests.get(f"{BASE_URL}/labor-estimator", allow_redirects=True)
        if resp.status_code != 200:
            return False, f"Labor estimator returned {resp.status_code}"
            
        if "disabled" in resp.text.lower() and "estimator" in resp.text.lower():
            return False, "Labor estimator showing as disabled"
            
        return True, "Estimator features appear enabled"
    except Exception as e:
        return False, f"Estimator test error: {str(e)}"

def test_dashboard_existence() -> Tuple[bool, str]:
    """Test if user dashboard exists"""
    try:
        # Check common dashboard URLs
        dashboard_urls = ["/dashboard", "/user/dashboard", "/profile", "/account"]
        
        found = []
        for url in dashboard_urls:
            resp = requests.get(f"{BASE_URL}{url}", allow_redirects=False)
            if resp.status_code in [200, 302, 301]:
                found.append(url)
        
        if not found:
            return False, "No user dashboard found at common URLs"
            
        return True, f"Dashboard found at: {', '.join(found)}"
    except Exception as e:
        return False, f"Dashboard test error: {str(e)}"

def test_admin_panel() -> Tuple[bool, str]:
    """Test if admin panel exists"""
    try:
        admin_urls = ["/admin", "/admin/dashboard", "/admin-panel"]
        
        found = []
        for url in admin_urls:
            resp = requests.get(f"{BASE_URL}{url}", allow_redirects=False)
            if resp.status_code in [200, 302, 301, 401]:  # 401 is ok, means it exists but needs auth
                found.append(f"{url} ({resp.status_code})")
        
        if not found:
            return False, "No admin panel found"
            
        return True, f"Admin panel found: {', '.join(found)}"
    except Exception as e:
        return False, f"Admin test error: {str(e)}"

def test_ui_elements() -> Tuple[bool, str]:
    """Test for specific UI issues mentioned in audit"""
    try:
        resp = requests.get(BASE_URL)
        if resp.status_code != 200:
            return False, f"Homepage returned {resp.status_code}"
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        issues = []
        
        # Check for gear icon
        gear_elements = soup.find_all(text=lambda t: 'gear' in t.lower() if t else False)
        if gear_elements:
            issues.append("Gear icon references found")
        
        # Check for overlapping elements (harder to detect without rendering)
        headers = soup.find_all(['header', 'nav'])
        if len(headers) > 1:
            issues.append(f"Multiple header/nav elements ({len(headers)}) might cause overlaps")
        
        # Check for calculator functionality
        calc_buttons = soup.find_all('button', text=lambda t: 'calculat' in t.lower() if t else False)
        if calc_buttons:
            # Check if they have onclick or proper links
            non_functional = [btn for btn in calc_buttons if not btn.get('onclick') and not btn.parent.name == 'a']
            if non_functional:
                issues.append(f"{len(non_functional)} calculator buttons might be non-functional")
        
        if issues:
            return False, "UI issues: " + "; ".join(issues)
        return True, "No specific UI issues detected"
        
    except Exception as e:
        return False, f"UI test error: {str(e)}"

def test_blog_content() -> Tuple[bool, str]:
    """Test if blog has actual content"""
    try:
        resp = requests.get(f"{BASE_URL}/blog")
        if resp.status_code != 200:
            return False, f"Blog returned {resp.status_code}"
        
        # Check if there's actual blog content
        if "no blog posts" in resp.text.lower() or "coming soon" in resp.text.lower():
            return False, "Blog has no content"
            
        # Try to access a specific blog post
        resp = requests.get(f"{BASE_URL}/blog/ai-revolutionizing-roofing", allow_redirects=True)
        if resp.status_code == 404:
            return False, "Blog posts return 404"
            
        return True, "Blog appears to have content"
    except Exception as e:
        return False, f"Blog test error: {str(e)}"

def run_detailed_validation():
    """Run detailed validation tests"""
    print("\n🔬 DETAILED MYROOFGENIUS VALIDATION")
    print("=" * 60)
    print(f"Based on external audit findings")
    print("=" * 60)
    
    tests = [
        ("Signup Flow", test_signup_flow),
        ("Estimator Features", test_estimator_features),
        ("User Dashboard", test_dashboard_existence),
        ("Admin Panel", test_admin_panel),
        ("UI Elements", test_ui_elements),
        ("Blog Content", test_blog_content)
    ]
    
    results = []
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        success, message = test_func()
        results.append((test_name, success, message))
        
        if success:
            print(f"✅ PASSED: {message}")
            passed += 1
        else:
            print(f"❌ FAILED: {message}")
    
    print("\n" + "=" * 60)
    print(f"📊 DETAILED RESULTS: {passed}/{len(tests)} tests passed")
    print(f"🎯 Success Rate: {(passed/len(tests)*100):.1f}%")
    
    print("\n📋 SUMMARY OF FINDINGS:")
    for test_name, success, message in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
    
    critical_issues = [r for r in results if not r[1] and r[0] in ["Signup Flow", "Estimator Features"]]
    if critical_issues:
        print("\n⚠️  CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
        for test_name, _, message in critical_issues:
            print(f"  - {test_name}: {message}")
    
    print("=" * 60)

if __name__ == "__main__":
    run_detailed_validation()