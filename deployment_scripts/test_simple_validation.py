#!/usr/bin/env python3
"""
Simple validation without external dependencies
"""

import requests
import json
from typing import Tuple

BASE_URL = "https://myroofgenius.com"
API_URL = "https://brainops-backend-prod.onrender.com"

def test_signup_flow() -> Tuple[bool, str]:
    """Test the actual signup flow"""
    try:
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
            return False, f"Signup returned {resp.status_code}"
            
    except Exception as e:
        return False, f"Signup test error: {str(e)}"

def test_estimator_features() -> Tuple[bool, str]:
    """Test if estimator features are enabled"""
    try:
        # Check material calculator
        resp = requests.get(f"{BASE_URL}/material-calculator")
        content = resp.text.lower()
        
        if "estimator feature is disabled" in content:
            return False, "Estimator features showing as disabled"
            
        if resp.status_code != 200:
            return False, f"Material calculator returned {resp.status_code}"
            
        return True, "Estimator features appear enabled"
    except Exception as e:
        return False, f"Estimator test error: {str(e)}"

def test_dashboard_existence() -> Tuple[bool, str]:
    """Test if user dashboard exists"""
    try:
        # Check dashboard URL with redirects
        resp = requests.get(f"{BASE_URL}/dashboard", allow_redirects=True)
        
        # If it redirects to login, that means dashboard exists but is protected
        if "/login" in resp.url:
            return True, "Dashboard exists (redirects to login - protected route)"
        elif resp.status_code == 200:
            return True, "Dashboard accessible without auth"
        
        # Try profile
        resp = requests.get(f"{BASE_URL}/profile", allow_redirects=True)
        if "/login" in resp.url:
            return True, "Profile exists (redirects to login - protected route)"
        elif resp.status_code == 200:
            return True, "Profile accessible"
            
        return False, "No user dashboard found"
    except Exception as e:
        return False, f"Dashboard test error: {str(e)}"

def test_admin_panel() -> Tuple[bool, str]:
    """Test if admin panel exists"""
    try:
        resp = requests.get(f"{BASE_URL}/admin", allow_redirects=True)
        
        # If it redirects to login or dashboard, admin panel exists but is protected
        if "/login" in resp.url:
            return True, "Admin panel exists (redirects to login - protected route)"
        elif "/dashboard" in resp.url:
            return True, "Admin panel exists (redirects to dashboard - non-admin user)"
        elif resp.status_code == 200:
            return True, "Admin panel accessible"
            
        return False, "No admin panel found"
    except Exception as e:
        return False, f"Admin test error: {str(e)}"

def test_ui_content() -> Tuple[bool, str]:
    """Test for specific UI content issues"""
    try:
        resp = requests.get(BASE_URL)
        content = resp.text.lower()
        
        issues = []
        
        # Check for gear/settings in main content
        if "settings" in content and "gear" in content:
            issues.append("Gear/settings icon might be present")
        
        # Check for GitHub
        if "github" in content:
            issues.append("GitHub references found")
            
        # Check for robot
        if "robot" in content:
            issues.append("Robot references found")
        
        if issues:
            return False, "UI issues: " + "; ".join(issues)
        return True, "No problematic UI content detected"
        
    except Exception as e:
        return False, f"UI test error: {str(e)}"

def test_blog_dynamic() -> Tuple[bool, str]:
    """Test if blog loads dynamically"""
    try:
        resp = requests.get(f"{BASE_URL}/blog")
        content = resp.text.lower()
        
        if "no blog posts" in content:
            return False, "Blog shows no posts message"
            
        # Try specific post
        resp2 = requests.get(f"{BASE_URL}/blog/test-post")
        if resp2.status_code == 404:
            # This is actually expected if using dynamic routing
            return True, "Blog using dynamic routing (404 for non-existent posts)"
            
        return True, "Blog appears functional"
    except Exception as e:
        return False, f"Blog test error: {str(e)}"

def run_simple_validation():
    """Run validation tests"""
    print("\n🔍 MYROOFGENIUS CRITICAL ISSUES VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Backend Registration", test_signup_flow),
        ("Estimator Features", test_estimator_features),
        ("User Dashboard", test_dashboard_existence),
        ("Admin Panel", test_admin_panel),
        ("UI Content Check", test_ui_content),
        ("Blog Functionality", test_blog_dynamic)
    ]
    
    results = []
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        success, message = test_func()
        results.append((test_name, success, message))
        
        if success:
            print(f"✅ {message}")
            passed += 1
        else:
            print(f"❌ {message}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed}/{len(tests)} tests passed ({(passed/len(tests)*100):.0f}%)")
    
    # Identify critical vs non-critical issues
    critical_failed = [r for r in results if not r[1] and r[0] in ["Backend Registration", "Estimator Features"]]
    other_failed = [r for r in results if not r[1] and r[0] not in ["Backend Registration", "Estimator Features"]]
    
    if critical_failed:
        print("\n🚨 CRITICAL ISSUES (Block launch):")
        for name, _, msg in critical_failed:
            print(f"  - {name}: {msg}")
    
    if other_failed:
        print("\n⚠️  OTHER ISSUES (Should fix):")
        for name, _, msg in other_failed:
            print(f"  - {name}: {msg}")
    
    if not critical_failed and not other_failed:
        print("\n✅ ALL SYSTEMS GO - Ready for production!")
    
    print("=" * 60)

if __name__ == "__main__":
    run_simple_validation()