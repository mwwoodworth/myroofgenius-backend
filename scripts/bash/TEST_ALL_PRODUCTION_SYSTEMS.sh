#!/bin/bash

# COMPREHENSIVE PRODUCTION SYSTEMS TEST
# Tests all live endpoints and critical functionality

echo "🔬 COMPREHENSIVE PRODUCTION SYSTEMS TEST"
echo "========================================"
echo "Testing all live production endpoints..."
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3
    local method=${4:-GET}
    local data=${5:-}
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    fi
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✅${NC} $name: $response (Expected: $expected_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌${NC} $name: $response (Expected: $expected_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo "1️⃣ BACKEND API ENDPOINTS"
echo "-------------------------"
test_endpoint "Health Check" "https://brainops-backend-prod.onrender.com/api/v1/health" "200"
test_endpoint "API Version" "https://brainops-backend-prod.onrender.com/api/v1/version" "200"
test_endpoint "Public Products" "https://brainops-backend-prod.onrender.com/api/v1/products/public" "200"
test_endpoint "AUREA Chat Public" "https://brainops-backend-prod.onrender.com/api/v1/aurea/public/chat" "200" "POST" '{"message":"test"}'
test_endpoint "CRM Customers" "https://brainops-backend-prod.onrender.com/api/v1/crm/customers" "401"
test_endpoint "Revenue Stats" "https://brainops-backend-prod.onrender.com/api/v1/revenue/stats" "401"
test_endpoint "AI Board Status" "https://brainops-backend-prod.onrender.com/api/v1/ai-board/status" "200"
test_endpoint "Task OS Status" "https://brainops-backend-prod.onrender.com/api/v1/task-os/status" "200"
test_endpoint "Memory Recent" "https://brainops-backend-prod.onrender.com/api/v1/memory/recent" "200"
test_endpoint "Marketplace Products" "https://brainops-backend-prod.onrender.com/api/v1/marketplace/products" "200"

echo ""
echo "2️⃣ FRONTEND APPLICATIONS"
echo "------------------------"
test_endpoint "MyRoofGenius Main" "https://myroofgenius.com" "200"
test_endpoint "MyRoofGenius App" "https://myroofgenius-app.vercel.app" "200"
test_endpoint "WeatherCraft ERP" "https://weathercraft-erp.vercel.app" "200"
test_endpoint "WeatherCraft App" "https://weathercraft-app.vercel.app" "200"
test_endpoint "BrainOps Task OS" "https://brainops-task-os.vercel.app" "200"
test_endpoint "BrainOps AIOS" "https://brainops-aios-ops.vercel.app" "200"

echo ""
echo "3️⃣ DATABASE CONNECTIVITY"
echo "------------------------"
DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"

# Test database connection
echo -n "Database Connection: "
if psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Connected"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌${NC} Failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Check data counts
echo ""
echo "📊 Database Statistics:"
psql "$DATABASE_URL" -t -c "
    SELECT 
        'Customers: ' || COUNT(*) FROM customers WHERE external_id LIKE 'CP-%'
    UNION ALL
    SELECT 
        'Jobs: ' || COUNT(*) FROM jobs
    UNION ALL
    SELECT 
        'Invoices: ' || COUNT(*) FROM invoices
    UNION ALL
    SELECT 
        'Products: ' || COUNT(*) FROM products
" 2>/dev/null | sed 's/^/  /'

echo ""
echo "4️⃣ CENTERPOINT SYNC STATUS"
echo "--------------------------"
# Check if sync is running
if pgrep -f "centerpoint-sync-service.sh" > /dev/null; then
    echo -e "${GREEN}✅${NC} Sync Service: Running (PID: $(pgrep -f centerpoint-sync-service.sh))"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠️${NC} Sync Service: Not Running"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Check recent sync
echo -n "Last Sync: "
psql "$DATABASE_URL" -t -c "
    SELECT 'Completed ' || 
           EXTRACT(EPOCH FROM (NOW() - completed_at))::INT / 60 || 
           ' minutes ago'
    FROM centerpoint_sync_log 
    WHERE status = 'completed' 
    ORDER BY completed_at DESC 
    LIMIT 1
" 2>/dev/null || echo "No sync history"

echo ""
echo "5️⃣ REVENUE SYSTEM"
echo "-----------------"
# Test revenue endpoints
echo -n "Revenue Processing: "
revenue_response=$(curl -s "https://brainops-backend-prod.onrender.com/api/v1/revenue/stats" 2>/dev/null)
if echo "$revenue_response" | grep -q "total_revenue\|mrr\|error"; then
    echo -e "${GREEN}✅${NC} API Responding"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌${NC} Not Responding"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "6️⃣ MONITORING SYSTEMS"
echo "---------------------"
# Check AUREA monitoring
if pgrep -f "AUREA_CLAUDEOS_QC_SYSTEM.py" > /dev/null; then
    echo -e "${GREEN}✅${NC} AUREA QC: Running"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠️${NC} AUREA QC: Not Running"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Check ClaudeOS health check
if [ -f "/tmp/claudeos_health.log" ]; then
    last_check=$(stat -c %Y /tmp/claudeos_health.log 2>/dev/null)
    current_time=$(date +%s)
    diff=$((current_time - last_check))
    if [ $diff -lt 3600 ]; then
        echo -e "${GREEN}✅${NC} ClaudeOS Health: Active (checked $(($diff/60)) min ago)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${YELLOW}⚠️${NC} ClaudeOS Health: Stale (last check $(($diff/3600)) hours ago)"
    fi
else
    echo -e "${RED}❌${NC} ClaudeOS Health: No logs"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "========================================"
echo "📊 TEST SUMMARY"
echo "========================================"
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo ""
if [ $SUCCESS_RATE -ge 90 ]; then
    echo -e "${GREEN}✅ SYSTEM STATUS: OPERATIONAL ($SUCCESS_RATE%)${NC}"
elif [ $SUCCESS_RATE -ge 70 ]; then
    echo -e "${YELLOW}⚠️ SYSTEM STATUS: DEGRADED ($SUCCESS_RATE%)${NC}"
else
    echo -e "${RED}❌ SYSTEM STATUS: CRITICAL ($SUCCESS_RATE%)${NC}"
fi

echo "========================================"
echo ""

# Generate detailed report
echo "📝 Generating detailed report..."
cat > /home/mwwoodworth/code/PRODUCTION_TEST_REPORT.md << EOF
# Production Systems Test Report
Generated: $(date '+%Y-%m-%d %H:%M:%S')

## Test Results
- Total Tests: $TOTAL_TESTS
- Passed: $PASSED_TESTS
- Failed: $FAILED_TESTS
- Success Rate: $SUCCESS_RATE%

## System Status
$(if [ $SUCCESS_RATE -ge 90 ]; then echo "✅ OPERATIONAL"; elif [ $SUCCESS_RATE -ge 70 ]; then echo "⚠️ DEGRADED"; else echo "❌ CRITICAL"; fi)

## Recommendations
$(if [ $FAILED_TESTS -gt 0 ]; then
    echo "- Investigate failed endpoints immediately"
    echo "- Check Docker container health on Render"
    echo "- Review recent deployment logs"
else
    echo "- All systems operational"
    echo "- Continue monitoring for stability"
fi)

## Next Steps
1. Monitor system health continuously
2. Set up alerting for failures
3. Document any issues found
4. Schedule regular health checks
EOF

echo "✅ Report saved to: /home/mwwoodworth/code/PRODUCTION_TEST_REPORT.md"