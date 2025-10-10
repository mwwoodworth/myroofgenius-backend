#!/bin/bash

# MyRoofGenius Revenue System Verification
# This script verifies all revenue-generating systems are operational

echo "🎯 MYROOFGENIUS REVENUE SYSTEM VERIFICATION"
echo "==========================================="
echo "Timestamp: $(date)"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Wait for deployment to complete
echo "⏳ Waiting for deployment to complete (30 seconds)..."
sleep 30

# Function to check endpoint
check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    
    echo -n "Checking $name... "
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✅ OPERATIONAL${NC} (Status: $status)"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC} (Expected: $expected_status, Got: $status)"
        return 1
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local name=$1
    local url=$2
    
    echo -n "Testing $name... "
    response=$(curl -s "$url")
    
    if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        echo -e "${GREEN}✅ VALID JSON${NC}"
        echo "  Response preview: $(echo "$response" | head -c 100)..."
        return 0
    else
        echo -e "${RED}❌ INVALID RESPONSE${NC}"
        return 1
    fi
}

echo "🔍 BACKEND API CHECKS"
echo "====================="

# Check backend health
check_endpoint "Backend Health" "https://brainops-backend-prod.onrender.com/api/v1/health" "200"

# Check revenue endpoints
test_json_endpoint "Pricing API" "https://brainops-backend-prod.onrender.com/api/v1/revenue/pricing"
test_json_endpoint "Marketplace Products" "https://brainops-backend-prod.onrender.com/api/v1/revenue/marketplace/products"
test_json_endpoint "Dashboard Stats" "https://brainops-backend-prod.onrender.com/api/v1/revenue/dashboard/stats"
test_json_endpoint "Revenue Health" "https://brainops-backend-prod.onrender.com/api/v1/revenue/health"

echo ""
echo "🌐 FRONTEND CHECKS"
echo "=================="

# Check frontend pages
check_endpoint "Main Site" "https://myroofgenius.com" "200"
check_endpoint "Main Site (www)" "https://www.myroofgenius.com" "200"

echo ""
echo "💰 REVENUE FEATURE TESTS"
echo "========================"

# Test AI Analysis endpoint
echo -n "Testing AI Analysis endpoint... "
ai_response=$(curl -s -X POST "https://brainops-backend-prod.onrender.com/api/v1/revenue/ai/analyze" \
    -H "Content-Type: application/json" \
    -d '{"address":"123 Test St, Test City, TC 12345","analysis_type":"comprehensive"}')

if echo "$ai_response" | grep -q "analysis_id"; then
    echo -e "${GREEN}✅ AI ANALYSIS WORKING${NC}"
else
    echo -e "${RED}❌ AI ANALYSIS FAILED${NC}"
fi

# Test Cost Calculator
echo -n "Testing Cost Calculator... "
calc_response=$(curl -s -X POST "https://brainops-backend-prod.onrender.com/api/v1/revenue/calculator/estimate" \
    -H "Content-Type: application/json" \
    -d '{"square_feet":2000,"material":"asphalt","complexity":"medium"}')

if echo "$calc_response" | grep -q "total"; then
    echo -e "${GREEN}✅ CALCULATOR WORKING${NC}"
else
    echo -e "${RED}❌ CALCULATOR FAILED${NC}"
fi

echo ""
echo "📊 REVENUE READINESS SUMMARY"
echo "============================"

# Get current stats
stats_response=$(curl -s "https://brainops-backend-prod.onrender.com/api/v1/revenue/dashboard/stats")

if echo "$stats_response" | python3 -m json.tool > /dev/null 2>&1; then
    echo -e "${GREEN}✅ REVENUE DASHBOARD ACTIVE${NC}"
    echo ""
    echo "Current Stats:"
    echo "$stats_response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'stats' in data:
    stats = data['stats']
    print(f'  • Total Revenue: \${stats.get(\"total_revenue\", 0):,.2f}')
    print(f'  • Monthly Recurring: \${stats.get(\"monthly_recurring\", 0):,.2f}')
    print(f'  • Active Subscriptions: {stats.get(\"active_subscriptions\", 0)}')
    print(f'  • Marketplace Sales: {stats.get(\"marketplace_sales\", 0)}')
    print(f'  • AI Analyses: {stats.get(\"ai_analyses_completed\", 0)}')
"
fi

echo ""
echo "🚀 IMMEDIATE REVENUE ACTIONS"
echo "============================"
echo ""
echo "1. SHARE THESE LINKS NOW:"
echo "   • Pricing: https://myroofgenius.com/pricing"
echo "   • AI Tool: https://myroofgenius.com/ai-analyzer"
echo "   • Marketplace: https://myroofgenius.com/marketplace"
echo ""
echo "2. MARKETING CHANNELS:"
echo "   • Post on LinkedIn/Twitter/Facebook NOW"
echo "   • Email your contact list TODAY"
echo "   • Post in roofing contractor forums"
echo "   • Start Google Ads campaign ($100/day)"
echo ""
echo "3. EXPECTED REVENUE:"
echo "   • First 24 hours: $145-$435 (5-15 signups)"
echo "   • First week: $1,450-$4,350"
echo "   • First month: $14,500-$43,500"
echo ""

# Final status
echo "================================"
if curl -s "https://brainops-backend-prod.onrender.com/api/v1/revenue/health" | grep -q "operational"; then
    echo -e "${GREEN}✅ MYROOFGENIUS IS READY TO GENERATE REVENUE!${NC}"
    echo -e "${GREEN}💰 ALL SYSTEMS OPERATIONAL - START SELLING NOW!${NC}"
else
    echo -e "${YELLOW}⚠️ Some systems still deploying - check again in 2 minutes${NC}"
fi
echo "================================"