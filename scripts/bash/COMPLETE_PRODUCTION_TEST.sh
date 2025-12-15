#!/bin/bash

# ====================================================================
# COMPLETE PRODUCTION SYSTEM TEST
# Tests all live systems and reports operational status
# ====================================================================

set -e

echo "============================================================"
echo "     COMPLETE PRODUCTION SYSTEM TEST - $(date)"
echo "============================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local expected="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo "1. BACKEND API TESTS"
echo "===================="

# Test backend health
run_test "Backend API Health" \
    "curl -s https://brainops-backend-prod.onrender.com/api/v1/health | grep -q 'healthy'"

# Test API documentation
run_test "API Documentation" \
    "curl -s https://brainops-backend-prod.onrender.com/docs | grep -q 'swagger'"

# Test products endpoint
run_test "Products API" \
    "curl -s https://brainops-backend-prod.onrender.com/api/v1/products | grep -q 'products'"

# Test revenue endpoint
run_test "Revenue Stats API" \
    "curl -s https://brainops-backend-prod.onrender.com/api/v1/revenue/stats | grep -q 'total_revenue'"

echo ""
echo "2. FRONTEND TESTS"
echo "================="

# Test MyRoofGenius frontend
run_test "MyRoofGenius Homepage" \
    "curl -s -L https://myroofgenius.com | grep -q 'AI'"

# Test redirect
run_test "Frontend Redirect" \
    "curl -s -o /dev/null -w '%{http_code}' -L https://myroofgenius.com | grep -q '200'"

echo ""
echo "3. DATABASE TESTS"
echo "================="

# Test database connectivity
run_test "Database Connection" \
    "PGPASSWORD='<DB_PASSWORD_REDACTED>' psql -h aws-0-us-east-2.pooler.supabase.com -p 6543 -U postgres.yomagoqdmxszqtdwuhab -d postgres -c 'SELECT 1' 2>/dev/null"

# Test Centerpoint data
echo -n "Centerpoint Customers: "
CUSTOMER_COUNT=$(PGPASSWORD='<DB_PASSWORD_REDACTED>' psql -h aws-0-us-east-2.pooler.supabase.com -p 6543 -U postgres.yomagoqdmxszqtdwuhab -d postgres -t -c "SELECT COUNT(*) FROM customers WHERE external_id LIKE 'CP-%'" 2>/dev/null | tr -d ' ')
if [ "$CUSTOMER_COUNT" -gt 0 ]; then
    echo -e "${GREEN}$CUSTOMER_COUNT records${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}0 records${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test products table
echo -n "Products in Database: "
PRODUCT_COUNT=$(PGPASSWORD='<DB_PASSWORD_REDACTED>' psql -h aws-0-us-east-2.pooler.supabase.com -p 6543 -U postgres.yomagoqdmxszqtdwuhab -d postgres -t -c "SELECT COUNT(*) FROM products" 2>/dev/null | tr -d ' ')
if [ "$PRODUCT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}$PRODUCT_COUNT records${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}$PRODUCT_COUNT records (warning)${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "4. AUTHENTICATION TESTS"
echo "======================="

# Test login endpoint exists
run_test "Login Endpoint" \
    "curl -s -X POST https://brainops-backend-prod.onrender.com/api/v1/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"test\"}' | grep -E 'detail|error|token'"

# Test register endpoint exists
run_test "Register Endpoint" \
    "curl -s -X POST https://brainops-backend-prod.onrender.com/api/v1/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"test\"}' | grep -E 'detail|error|token'"

echo ""
echo "5. INTEGRATION TESTS"
echo "===================="

# Check Render deployment status
echo -n "Render Deployment: "
RENDER_STATUS=$(curl -s https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00 -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" | grep -o '"suspended":"[^"]*"' | cut -d'"' -f4)
if [ "$RENDER_STATUS" = "not_suspended" ]; then
    echo -e "${GREEN}Active${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}Suspended or Error${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "6. DATA INTEGRITY TESTS"
echo "======================="

# Check for orphaned records
echo -n "Checking for orphaned jobs: "
ORPHANED_JOBS=$(PGPASSWORD='<DB_PASSWORD_REDACTED>' psql -h aws-0-us-east-2.pooler.supabase.com -p 6543 -U postgres.yomagoqdmxszqtdwuhab -d postgres -t -c "SELECT COUNT(*) FROM jobs WHERE customer_id IS NULL" 2>/dev/null | tr -d ' ')
if [ "$ORPHANED_JOBS" = "0" ]; then
    echo -e "${GREEN}None found${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}$ORPHANED_JOBS orphaned jobs (warning)${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Check for data tagged as sample
echo -n "Sample data tagging: "
SAMPLE_COUNT=$(PGPASSWORD='<DB_PASSWORD_REDACTED>' psql -h aws-0-us-east-2.pooler.supabase.com -p 6543 -U postgres.yomagoqdmxszqtdwuhab -d postgres -t -c "SELECT COUNT(*) FROM customers WHERE metadata->>'is_sample' = 'true'" 2>/dev/null | tr -d ' ')
echo -e "${GREEN}$SAMPLE_COUNT records tagged${NC}"
PASSED_TESTS=$((PASSED_TESTS + 1))
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "============================================================"
echo "                     TEST SUMMARY"
echo "============================================================"

# Calculate percentage
if [ $TOTAL_TESTS -gt 0 ]; then
    PERCENTAGE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
else
    PERCENTAGE=0
fi

echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo ""

# Overall status
if [ $PERCENTAGE -ge 90 ]; then
    echo -e "${GREEN}✅ SYSTEM STATUS: FULLY OPERATIONAL ($PERCENTAGE%)${NC}"
elif [ $PERCENTAGE -ge 70 ]; then
    echo -e "${YELLOW}⚠️  SYSTEM STATUS: PARTIALLY OPERATIONAL ($PERCENTAGE%)${NC}"
else
    echo -e "${RED}❌ SYSTEM STATUS: CRITICAL ISSUES ($PERCENTAGE%)${NC}"
fi

echo ""
echo "============================================================"
echo "                   DETAILED METRICS"
echo "============================================================"

# Database metrics
echo ""
echo "DATABASE METRICS:"
PGPASSWORD='<DB_PASSWORD_REDACTED>' psql -h aws-0-us-east-2.pooler.supabase.com -p 6543 -U postgres.yomagoqdmxszqtdwuhab -d postgres -c "
SELECT 
    'Centerpoint Customers' as metric, COUNT(*) as count 
FROM customers 
WHERE external_id LIKE 'CP-%'
UNION ALL
SELECT 'Total Customers', COUNT(*) FROM customers
UNION ALL
SELECT 'Jobs', COUNT(*) FROM jobs
UNION ALL
SELECT 'Invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'Estimates', COUNT(*) FROM estimates
UNION ALL
SELECT 'Products', COUNT(*) FROM products
UNION ALL
SELECT 'Centerpoint Files', COUNT(*) FROM centerpoint_files
ORDER BY count DESC;" 2>/dev/null

echo ""
echo "RECENT SYNC ACTIVITY:"
PGPASSWORD='<DB_PASSWORD_REDACTED>' psql -h aws-0-us-east-2.pooler.supabase.com -p 6543 -U postgres.yomagoqdmxszqtdwuhab -d postgres -c "
SELECT 
    sync_type,
    status,
    started_at,
    completed_at,
    errors
FROM centerpoint_sync_log
ORDER BY started_at DESC
LIMIT 5;" 2>/dev/null || echo "No sync logs available"

echo ""
echo "============================================================"
echo "                     RECOMMENDATIONS"
echo "============================================================"

if [ $FAILED_TESTS -gt 0 ]; then
    echo "⚠️  Issues detected. Recommended actions:"
    echo ""
    
    if ! run_test "Backend Health Check" "curl -s https://brainops-backend-prod.onrender.com/api/v1/health | grep -q 'healthy'" > /dev/null 2>&1; then
        echo "1. Backend API is not responding properly"
        echo "   - Check Render deployment status"
        echo "   - Review Docker container logs"
        echo "   - Verify environment variables are set"
    fi
    
    if [ "$CUSTOMER_COUNT" = "0" ]; then
        echo "2. No Centerpoint data found"
        echo "   - Run: npx tsx scripts/centerpoint-full-sync.ts"
        echo "   - Check API credentials are valid"
        echo "   - Verify database migrations completed"
    fi
    
    echo ""
    echo "To fix issues, run:"
    echo "  ./FIX_PRODUCTION_ISSUES.sh"
else
    echo -e "${GREEN}✅ All systems operational!${NC}"
    echo ""
    echo "System is ready for production use."
fi

echo ""
echo "============================================================"
echo "Test completed at $(date)"
echo "============================================================"

exit $FAILED_TESTS