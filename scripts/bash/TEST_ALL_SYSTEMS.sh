#!/bin/bash
# COMPLETE SYSTEM TEST - v5.03
# Tests ALL endpoints and reports errors

echo "🔍 BRAINOPS COMPLETE SYSTEM TEST"
echo "================================="
echo "Date: $(date)"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local url=$1
    local expected=$2
    local name=$3
    
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$STATUS" = "$expected" ]; then
        echo -e "${GREEN}✅${NC} $name: $url"
        return 0
    else
        echo -e "${RED}❌${NC} $name: $url (Expected $expected, Got $STATUS)"
        return 1
    fi
}

# Initialize counters
PASSED=0
FAILED=0

echo "1. BACKEND ENDPOINTS:"
echo "--------------------"

# Backend health checks
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/health" "200" "Health Check" && ((PASSED++)) || ((FAILED++))
test_endpoint "https://brainops-backend-prod.onrender.com/" "200" "Root Endpoint" && ((PASSED++)) || ((FAILED++))
test_endpoint "https://brainops-backend-prod.onrender.com/health" "200" "Render Health" && ((PASSED++)) || ((FAILED++))

# Marketplace endpoints
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/marketplace/products" "200" "Products" && ((PASSED++)) || ((FAILED++))
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/marketplace/cart" "200" "Cart" && ((PASSED++)) || ((FAILED++))

# Automation endpoints
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/automations" "200" "Automations" && ((PASSED++)) || ((FAILED++))

# AI Agent endpoints
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/agents" "200" "AI Agents" && ((PASSED++)) || ((FAILED++))

# Database status
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/database/status" "200" "Database Status" && ((PASSED++)) || ((FAILED++))

# CenterPoint status
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/centerpoint/status" "200" "CenterPoint Status" && ((PASSED++)) || ((FAILED++))

echo ""
echo "2. FRONTEND SITES:"
echo "-----------------"

# Frontend sites
test_endpoint "https://myroofgenius.com" "200" "MyRoofGenius" && ((PASSED++)) || ((FAILED++))
test_endpoint "https://weathercraft-app.vercel.app" "200" "WeatherCraft" && ((PASSED++)) || ((FAILED++))
test_endpoint "https://brainops-task-os.vercel.app" "200" "Task OS" && ((PASSED++)) || ((FAILED++))

echo ""
echo "3. DETAILED BACKEND CHECK:"
echo "-------------------------"

# Get version
VERSION=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health | python3 -c "import json, sys; d=json.load(sys.stdin); print(f'Version: {d.get(\"version\", \"unknown\")}'); print(f'Database: {d.get(\"database\", \"unknown\")}'); print(f'Port: {d.get(\"port\", \"unknown\")}')" 2>/dev/null)
echo "$VERSION"

echo ""
echo "4. DATABASE CHECK:"
echo "-----------------"

# Check database connectivity
DB_STATUS=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/database/status 2>/dev/null)
if [ ! -z "$DB_STATUS" ]; then
    echo "$DB_STATUS" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'Connected: {data.get(\"connected\", False)}')
    tables = data.get('tables', {})
    if tables:
        for table, count in tables.items():
            print(f'  {table}: {count} records')
    error = data.get('error')
    if error:
        print(f'  Error: {error}')
except:
    print('Failed to parse database status')
" 2>/dev/null
fi

echo ""
echo "5. PRODUCTS CHECK:"
echo "-----------------"

# Check products
PRODUCTS=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/marketplace/products 2>/dev/null)
if [ ! -z "$PRODUCTS" ]; then
    echo "$PRODUCTS" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'Total Products: {data.get(\"total\", 0)}')
    print(f'Source: {data.get(\"source\", \"unknown\")}')
    products = data.get('products', [])
    for p in products[:3]:
        print(f'  - {p.get(\"name\", \"unknown\")}: \${p.get(\"price_cents\", 0)/100:.2f}')
except:
    print('Failed to parse products')
" 2>/dev/null
fi

echo ""
echo "================================="
echo "📊 TEST SUMMARY:"
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${RED}Failed:${NC} $FAILED"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
else
    echo -e "${YELLOW}⚠️  $FAILED tests failed - investigation needed${NC}"
fi

echo ""
echo "🎯 RECOMMENDATIONS:"
if [ $FAILED -gt 0 ]; then
    echo "• Fix failing endpoints immediately"
    echo "• Check Render logs for errors"
    echo "• Verify database connectivity"
else
    echo "• System fully operational"
    echo "• Continue monitoring"
    echo "• Test end-to-end transactions"
fi

exit $FAILED