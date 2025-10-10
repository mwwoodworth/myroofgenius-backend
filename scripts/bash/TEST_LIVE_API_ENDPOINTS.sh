#!/bin/bash

# ============================================================
# LIVE API ENDPOINT TESTING
# Tests all critical API endpoints with real requests
# ============================================================

API_URL="https://brainops-backend-prod.onrender.com"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================================"
echo "          LIVE API ENDPOINT TESTING"
echo "============================================================"
echo ""

TOTAL=0
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local expected="$4"
    local description="$5"
    
    TOTAL=$((TOTAL + 1))
    echo -n "$description: "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -w "\nHTTP_STATUS:%{http_code}" \
            "$API_URL$endpoint")
    fi
    
    http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d':' -f2)
    body=$(echo "$response" | sed '/HTTP_STATUS:/d')
    
    if [ "$http_status" = "$expected" ]; then
        echo -e "${GREEN}✅ PASS${NC} (Status: $http_status)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (Expected: $expected, Got: $http_status)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "1. HEALTH & STATUS ENDPOINTS"
echo "============================="
test_endpoint "GET" "/api/v1/health" "" "200" "Health Check"
test_endpoint "GET" "/docs" "" "200" "API Documentation"
test_endpoint "GET" "/api/v1/version" "" "200" "Version Info"

echo ""
echo "2. PUBLIC ENDPOINTS (No Auth)"
echo "=============================="
test_endpoint "GET" "/api/v1/products" "" "200" "Products List"
test_endpoint "GET" "/api/v1/products/public" "" "200" "Public Products"
test_endpoint "GET" "/api/v1/revenue/stats" "" "200" "Revenue Stats"

echo ""
echo "3. AUTHENTICATION ENDPOINTS"
echo "============================"
test_endpoint "POST" "/api/v1/auth/register" \
    '{"email":"test'$(date +%s)'@test.com","password":"TestPass123!","name":"Test User"}' \
    "200" "User Registration"

test_endpoint "POST" "/api/v1/auth/login" \
    '{"email":"admin@brainops.com","password":"AdminPassword123!"}' \
    "200" "User Login"

echo ""
echo "4. AI ENDPOINTS"
echo "==============="
test_endpoint "POST" "/api/v1/aurea/chat" \
    '{"message":"Hello, test message"}' \
    "200" "AUREA Chat"

test_endpoint "GET" "/api/v1/aurea/status" "" "200" "AUREA Status"

echo ""
echo "5. BUSINESS DATA ENDPOINTS"
echo "==========================="

# Get auth token for protected endpoints
echo -n "Getting auth token... "
AUTH_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@brainops.com","password":"AdminPassword123!"}' \
    "$API_URL/api/v1/auth/login")

TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅${NC}"
    
    # Test protected endpoints
    test_protected() {
        local method="$1"
        local endpoint="$2"
        local description="$3"
        
        TOTAL=$((TOTAL + 1))
        echo -n "$description: "
        
        response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
            -H "Authorization: Bearer $TOKEN" \
            "$API_URL$endpoint")
        
        http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d':' -f2)
        
        if [ "$http_status" = "200" ] || [ "$http_status" = "201" ]; then
            echo -e "${GREEN}✅ PASS${NC} (Status: $http_status)"
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}❌ FAIL${NC} (Status: $http_status)"
            FAILED=$((FAILED + 1))
        fi
    }
    
    test_protected "GET" "/api/v1/customers" "Customers List"
    test_protected "GET" "/api/v1/jobs" "Jobs List"
    test_protected "GET" "/api/v1/invoices" "Invoices List"
    test_protected "GET" "/api/v1/estimates" "Estimates List"
else
    echo -e "${RED}❌ Failed to get token${NC}"
fi

echo ""
echo "6. CENTERPOINT INTEGRATION"
echo "=========================="
test_endpoint "GET" "/api/v1/centerpoint/status" "" "200" "CenterPoint Status"

echo ""
echo "7. WEBHOOKS & AUTOMATION"
echo "========================"
test_endpoint "POST" "/api/v1/webhooks/test" \
    '{"event":"test","data":{}}' \
    "200" "Webhook Test"

echo ""
echo "============================================================"
echo "                    TEST RESULTS"
echo "============================================================"

SUCCESS_RATE=$((PASSED * 100 / TOTAL))

echo "Total Tests: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Success Rate: $SUCCESS_RATE%"

echo ""
if [ $SUCCESS_RATE -ge 90 ]; then
    echo -e "${GREEN}✅ API FULLY OPERATIONAL${NC}"
elif [ $SUCCESS_RATE -ge 70 ]; then
    echo -e "${YELLOW}⚠️ API PARTIALLY OPERATIONAL${NC}"
else
    echo -e "${RED}❌ API CRITICAL ISSUES${NC}"
fi

echo "============================================================"