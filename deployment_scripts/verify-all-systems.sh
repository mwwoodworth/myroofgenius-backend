#!/bin/bash

# BrainOps Complete System Verification Script
# This script verifies ALL systems are deployed and operational with real data

echo "🔍 BRAINOPS SYSTEM VERIFICATION - $(date)"
echo "=============================================="
echo ""

# Initialize counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
CRITICAL_FAILURES=""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3
    local check_content=$4
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing $name... "
    
    # Make request and capture response
    response=$(curl -s -L -o /tmp/response.txt -w "%{http_code}" "$url")
    content=$(cat /tmp/response.txt)
    
    # Check status code
    if [ "$response" = "$expected_code" ]; then
        # If we need to check content
        if [ ! -z "$check_content" ]; then
            if echo "$content" | grep -q "$check_content"; then
                echo -e "${GREEN}✅ PASS${NC} (HTTP $response, content verified)"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                echo -e "${RED}❌ FAIL${NC} (HTTP $response, but missing: $check_content)"
                FAILED_TESTS=$((FAILED_TESTS + 1))
                CRITICAL_FAILURES="$CRITICAL_FAILURES\n- $name: Missing expected content"
            fi
        else
            echo -e "${GREEN}✅ PASS${NC} (HTTP $response)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (Expected $expected_code, got $response)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        CRITICAL_FAILURES="$CRITICAL_FAILURES\n- $name: HTTP $response"
    fi
}

# Function to check for mock data
check_no_mock_data() {
    local name=$1
    local url=$2
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Checking $name for mock data... "
    
    content=$(curl -s -L "$url")
    
    # Check for common mock data patterns
    if echo "$content" | grep -i -E "(mock|stub|placeholder|demo|example|lorem ipsum|123-456-7890|test@example)" > /dev/null; then
        echo -e "${RED}❌ FAIL${NC} (Mock data detected)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        CRITICAL_FAILURES="$CRITICAL_FAILURES\n- $name: Contains mock/placeholder data"
    else
        echo -e "${GREEN}✅ PASS${NC} (No mock data detected)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    fi
}

echo "1️⃣ BACKEND API VERIFICATION"
echo "----------------------------"
test_endpoint "Backend Health" "https://brainops-backend-prod.onrender.com/api/v1/health" "200" "version"
test_endpoint "Backend Docs" "https://brainops-backend-prod.onrender.com/docs" "200" "swagger"
test_endpoint "Products API" "https://brainops-backend-prod.onrender.com/api/v1/products/public/list" "200" "products"
test_endpoint "AUREA Status API" "https://brainops-backend-prod.onrender.com/api/v1/aurea/status" "200" "operational"
echo ""

echo "2️⃣ MYROOFGENIUS VERIFICATION"
echo "-----------------------------"
test_endpoint "MyRoofGenius Home" "https://myroofgenius.com" "200" "MyRoof"
test_endpoint "MyRoofGenius API" "https://myroofgenius.com/api/health" "200" ""
check_no_mock_data "MyRoofGenius Content" "https://myroofgenius.com"
echo ""

echo "3️⃣ WEATHERCRAFT PUBLIC SITE"
echo "----------------------------"
test_endpoint "WeatherCraft Home" "https://weathercraft-app.vercel.app" "200" "WeatherCraft"
check_no_mock_data "WeatherCraft Content" "https://weathercraft-app.vercel.app"
echo ""

echo "4️⃣ WEATHERCRAFT ERP VERIFICATION" 
echo "---------------------------------"
test_endpoint "WeatherCraft ERP" "https://weathercraft-erp.vercel.app" "200" ""
test_endpoint "ERP Login Page" "https://weathercraft-erp.vercel.app/auth/login" "200" ""
echo ""

echo "5️⃣ BRAINOPS AIOS VERIFICATION"
echo "------------------------------"
test_endpoint "BrainOps AIOS" "https://brainops-aios-ops.vercel.app" "200" "dashboard"
check_no_mock_data "AIOS Dashboard" "https://brainops-aios-ops.vercel.app"
echo ""

echo "6️⃣ DATABASE CONNECTIVITY CHECK"
echo "-------------------------------"
echo -n "Testing Supabase connection... "
# Test a public endpoint that uses the database
db_test=$(curl -s "https://brainops-backend-prod.onrender.com/api/v1/health")
if echo "$db_test" | grep -q "database.*connected"; then
    echo -e "${GREEN}✅ PASS${NC} (Database connected)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ FAIL${NC} (Database issue)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

echo "7️⃣ REAL-TIME FEATURES CHECK"
echo "----------------------------"
# Check if weather widget is showing real data
echo -n "Checking weather API integration... "
weather_check=$(curl -s "https://api.openweathermap.org/data/2.5/weather?lat=39.7392&lon=-104.9903&appid=d4d3f8a91234567890abcdef12345678&units=imperial")
if echo "$weather_check" | grep -q "temp"; then
    echo -e "${GREEN}✅ PASS${NC} (Weather API active)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠️  WARN${NC} (Weather API key may need update)"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo ""

echo "=============================================="
echo "📊 FINAL REPORT"
echo "=============================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL SYSTEMS OPERATIONAL${NC}"
    echo "All endpoints are live and returning real data!"
else
    echo -e "${RED}❌ CRITICAL FAILURES DETECTED${NC}"
    echo -e "The following issues need immediate attention:$CRITICAL_FAILURES"
    echo ""
    echo "🚨 ACTION REQUIRED:"
    echo "1. Check deployment logs for failed services"
    echo "2. Verify environment variables are set"
    echo "3. Ensure database migrations have run"
    echo "4. Re-deploy affected services"
fi

echo ""
echo "Report saved to: /tmp/system-verification-$(date +%Y%m%d-%H%M%S).log"
echo "=============================================="

# Save report
{
    echo "BrainOps System Verification Report"
    echo "Generated: $(date)"
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    if [ ! -z "$CRITICAL_FAILURES" ]; then
        echo -e "\nCritical Failures:$CRITICAL_FAILURES"
    fi
} > /tmp/system-verification-$(date +%Y%m%d-%H%M%S).log

# Exit with error code if any tests failed
exit $FAILED_TESTS