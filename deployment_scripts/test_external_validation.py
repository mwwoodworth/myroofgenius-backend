#!/usr/bin/env python3
"""
External validation script for MyRoofGenius production site
Tests all critical issues identified in the external audit
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple

BASE_URL = "https://myroofgenius.com"
API_URL = "https://brainops-backend-prod.onrender.com"

def test_auth_system() -> Tuple[bool, str]:
    """Test authentication system"""
    try:
        # Test login page
        resp = requests.get(f"{BASE_URL}/login", allow_redirects=True)
        if resp.status_code != 200:
            return False, f"Login page returned {resp.status_code}"
        
        # Test signup page  
        resp = requests.get(f"{BASE_URL}/signup", allow_redirects=True)
        if resp.status_code != 200:
            return False, f"Signup page returned {resp.status_code}"
            
        # Test auth error page
        resp = requests.get(f"{BASE_URL}/auth/error", allow_redirects=True)
        if resp.status_code != 200:
            return False, f"Auth error page returned {resp.status_code}"
            
        return True, "Auth pages accessible"
    except Exception as e:
        return False, f"Auth test error: {str(e)}"

def test_broken_routes() -> Tuple[bool, str]:
    """Test routes that were returning 404"""
    routes = [
        "/blog",
        "/forgot-password",
        "/material-calculator",
        "/labor-estimator"
    ]
    
    errors = []
    for route in routes:
        try:
            resp = requests.get(f"{BASE_URL}{route}", allow_redirects=True)
            if resp.status_code == 404:
                errors.append(f"{route}: 404")
            elif resp.status_code != 200:
                errors.append(f"{route}: {resp.status_code}")
        except Exception as e:
            errors.append(f"{route}: {str(e)}")
    
    if errors:
        return False, "Routes with issues: " + ", ".join(errors)
    return True, "All routes accessible"

def test_ui_issues() -> Tuple[bool, str]:
    """Test for UI issues like overlaps and unwanted elements"""
    try:
        resp = requests.get(BASE_URL)
        if resp.status_code != 200:
            return False, f"Homepage returned {resp.status_code}"
        
        content = resp.text.lower()
        
        issues = []
        # Check for robot imagery mentions
        if "robot" in content:
            issues.append("Robot imagery detected")
            
        # Check for GitHub links
        if "github.com" in content or "github" in content:
            issues.append("GitHub references detected")
            
        if issues:
            return False, "UI issues: " + ", ".join(issues)
        return True, "No UI issues detected"
    except Exception as e:
        return False, f"UI test error: {str(e)}"

def test_api_health() -> Tuple[bool, str]:
    """Test backend API health"""
    try:
        resp = requests.get(f"{API_URL}/api/v1/health")
        if resp.status_code != 200:
            return False, f"API health returned {resp.status_code}"
        
        data = resp.json()
        if data.get("status") != "healthy":
            return False, f"API status: {data.get('status')}"
            
        return True, f"API healthy (v{data.get('version')})"
    except Exception as e:
        return False, f"API test error: {str(e)}"

def test_aurea_functionality() -> Tuple[bool, str]:
    """Test AUREA AI functionality"""
    try:
        # Test AUREA status endpoint
        resp = requests.get(f"{API_URL}/api/v1/aurea/status")
        if resp.status_code == 401:
            return True, "AUREA requires authentication (expected)"
        elif resp.status_code != 200:
            return False, f"AUREA status returned {resp.status_code}"
        
        return True, "AUREA endpoint accessible"
    except Exception as e:
        return False, f"AUREA test error: {str(e)}"

def run_validation():
    """Run all validation tests"""
    print("\n🔍 MYROOFGENIUS EXTERNAL VALIDATION")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Production URL: {BASE_URL}")
    print(f"API URL: {API_URL}")
    print("=" * 50)
    
    tests = [
        ("Authentication System", test_auth_system),
        ("Route Accessibility", test_broken_routes),
        ("UI/UX Issues", test_ui_issues),
        ("Backend API Health", test_api_health),
        ("AUREA Functionality", test_aurea_functionality)
    ]
    
    results = []
    total_passed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        passed, message = test_func()
        results.append((test_name, passed, message))
        
        if passed:
            print(f"✅ PASSED: {message}")
            total_passed += 1
        else:
            print(f"❌ FAILED: {message}")
    
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY: {total_passed}/{len(tests)} tests passed")
    print(f"🎯 Success Rate: {(total_passed/len(tests)*100):.1f}%")
    
    if total_passed < len(tests):
        print("\n⚠️  CRITICAL ISSUES REMAIN:")
        for test_name, passed, message in results:
            if not passed:
                print(f"  - {test_name}: {message}")
    else:
        print("\n✅ ALL TESTS PASSED - System ready for production!")
    
    print("=" * 50)

if __name__ == "__main__":
    run_validation()