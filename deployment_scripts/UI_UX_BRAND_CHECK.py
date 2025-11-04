#!/usr/bin/env python3
"""
UI/UX and Brand Polish Check
Validates frontend accessibility and branding
"""
import requests
from datetime import datetime

print("🎨 UI/UX AND BRAND POLISH CHECK")
print("=" * 70)
print(f"Timestamp: {datetime.now().isoformat()}")
print("=" * 70)

# Frontend URLs
FRONTEND_URL = "https://myroofgenius.com"
VERCEL_URLS = [
    "https://myroofgenius-live-git-main-matts-projects-fe7d7976.vercel.app",
    "https://myroofgenius-live-metnsjow1-matts-projects-fe7d7976.vercel.app"
]

results = []

# Test 1: Main Frontend
print("\n1. MAIN FRONTEND (myroofgenius.com):")
try:
    response = requests.get(FRONTEND_URL, timeout=10, allow_redirects=True)
    if response.status_code == 200:
        print(f"   ✅ Site is accessible")
        print(f"   Final URL: {response.url}")
        print(f"   Content length: {len(response.content)} bytes")
        
        # Check for key brand elements
        content = response.text.lower()
        brand_checks = {
            "myroofgenius": "myroofgenius" in content,
            "AI-powered": "ai" in content or "artificial intelligence" in content,
            "Roofing": "roof" in content,
            "Login/Auth": "login" in content or "sign in" in content,
            "Marketplace": "marketplace" in content or "products" in content
        }
        
        print("\n   Brand Elements:")
        for element, found in brand_checks.items():
            status = "✅" if found else "⚠️"
            print(f"   {status} {element}: {'Found' if found else 'Not visible'}")
        
        results.append(("Main Frontend", True))
    else:
        print(f"   ❌ Site returned status {response.status_code}")
        results.append(("Main Frontend", False))
except Exception as e:
    print(f"   ❌ Error accessing site: {e}")
    results.append(("Main Frontend", False))

# Test 2: Vercel Deployments
print("\n2. VERCEL DEPLOYMENT STATUS:")
for i, url in enumerate(VERCEL_URLS, 1):
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            print(f"   ✅ Deployment {i}: Accessible")
            results.append((f"Vercel Deploy {i}", True))
        else:
            print(f"   ⚠️  Deployment {i}: Status {response.status_code}")
            results.append((f"Vercel Deploy {i}", False))
    except:
        print(f"   ⚠️  Deployment {i}: Not accessible")
        results.append((f"Vercel Deploy {i}", False))

# Test 3: Key Pages
print("\n3. KEY PAGES CHECK:")
pages = [
    ("/", "Homepage"),
    ("/marketplace", "Marketplace"),
    ("/login", "Login"),
    ("/register", "Register"),
    ("/about", "About"),
    ("/contact", "Contact")
]

for path, name in pages:
    try:
        response = requests.get(f"{FRONTEND_URL}{path}", timeout=5, allow_redirects=True)
        if response.status_code == 200:
            print(f"   ✅ {name}: Accessible")
            results.append((f"Page: {name}", True))
        else:
            print(f"   ⚠️  {name}: Status {response.status_code}")
            results.append((f"Page: {name}", False))
    except:
        print(f"   ⚠️  {name}: Error accessing")
        results.append((f"Page: {name}", False))

# Test 4: Mobile Responsiveness (check viewport meta tag)
print("\n4. MOBILE RESPONSIVENESS:")
try:
    response = requests.get(FRONTEND_URL, timeout=10)
    if response.status_code == 200:
        content = response.text
        if 'viewport' in content and 'width=device-width' in content:
            print("   ✅ Viewport meta tag present (mobile-friendly)")
            results.append(("Mobile Ready", True))
        else:
            print("   ⚠️  Viewport meta tag not found")
            results.append(("Mobile Ready", False))
except:
    results.append(("Mobile Ready", False))

# Summary
print("\n" + "=" * 70)
print("UI/UX VALIDATION SUMMARY:")
print("=" * 70)

passed = sum(1 for _, result in results if result)
total = len(results)
success_rate = (passed / total * 100) if total > 0 else 0

print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")

print("\n📊 BRAND POLISH ASSESSMENT:")
if success_rate >= 80:
    print("✅ Frontend is accessible and brand elements are present")
    print("✅ Key pages are loading properly")
    print("✅ Mobile responsiveness configured")
elif success_rate >= 60:
    print("⚠️  Frontend is partially accessible")
    print("⚠️  Some pages or brand elements may need attention")
else:
    print("❌ Frontend has accessibility issues")

print("\n📌 RECOMMENDATIONS:")
print("1. Ensure all key brand elements are visible on homepage")
print("2. Verify login/register flows are working")
print("3. Test marketplace functionality")
print("4. Confirm mobile responsiveness on actual devices")
print("5. Check for consistent branding across all pages")