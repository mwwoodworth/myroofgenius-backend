#!/bin/bash

echo "🔍 COMPLETE SYSTEM TEST v4.32"
echo "=============================="
echo "Testing all systems for 100% operational status"
echo ""

TOTAL=0
WORKING=0
FAILED_TESTS=""

test_endpoint() {
    local url=$1
    local expected=$2
    local name=$3
    
    TOTAL=$((TOTAL + 1))
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected" ]; then
        WORKING=$((WORKING + 1))
        echo "✅ $name: $response"
    else
        echo "❌ $name: $response (expected $expected)"
        FAILED_TESTS="$FAILED_TESTS\n  - $name: got $response, expected $expected"
    fi
}

echo "1️⃣ BACKEND API TESTS"
echo "-------------------"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/health" "200" "Health Check"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/version" "200" "Version"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/products/public" "200" "Public Products"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/aurea/chat" "200" "AUREA Chat"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/task-os/status" "200" "Task OS Status"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/revenue/dashboard" "200" "Revenue Dashboard"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/crm/customers" "200" "CRM Customers"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/estimates" "200" "Estimates"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/jobs" "200" "Jobs"

echo ""
echo "2️⃣ FRONTEND APPLICATIONS"
echo "------------------------"
test_endpoint "https://myroofgenius.com" "200" "MyRoofGenius Main"
test_endpoint "https://weathercraft-erp.vercel.app" "200" "WeatherCraft ERP"
test_endpoint "https://brainops-task-os.vercel.app" "200" "BrainOps Task OS"
test_endpoint "https://myroofgenius-app.vercel.app" "200" "MyRoofGenius App"

echo ""
echo "3️⃣ DATABASE & SYNC"
echo "------------------"
# Test database connection
echo -n "Database Connection: "
if DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require" psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
    WORKING=$((WORKING + 1))
    TOTAL=$((TOTAL + 1))
    echo "✅ Connected"
else
    TOTAL=$((TOTAL + 1))
    echo "❌ Failed"
    FAILED_TESTS="$FAILED_TESTS\n  - Database connection failed"
fi

# Check CenterPoint sync
echo -n "CenterPoint Sync: "
if pgrep -f "centerpoint-sync-service.sh" > /dev/null; then
    WORKING=$((WORKING + 1))
    TOTAL=$((TOTAL + 1))
    echo "✅ Running (PID: $(pgrep -f centerpoint-sync-service.sh))"
else
    TOTAL=$((TOTAL + 1))
    echo "❌ Not running"
    FAILED_TESTS="$FAILED_TESTS\n  - CenterPoint sync not running"
fi

echo ""
echo "4️⃣ REVENUE PROCESSING"
echo "--------------------"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/revenue/products" "200" "Revenue Products"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/revenue/subscriptions" "200" "Subscriptions"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/revenue/metrics" "200" "Revenue Metrics"

echo ""
echo "5️⃣ DATA INTEGRITY CHECK"
echo "-----------------------"
echo "Checking CenterPoint data..."
DATA_CHECK=$(DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require" psql "$DATABASE_URL" -t -c "
SELECT 
    'Customers: ' || COUNT(*) || ' (CP: ' || COUNT(CASE WHEN external_id LIKE 'CP-%' THEN 1 END) || ')'
FROM customers
UNION ALL
SELECT 
    'Jobs: ' || COUNT(*)
FROM jobs
UNION ALL
SELECT 
    'Invoices: ' || COUNT(*)
FROM invoices
UNION ALL
SELECT 
    'Products: ' || COUNT(*)
FROM products;" 2>/dev/null)

if [ -n "$DATA_CHECK" ]; then
    echo "$DATA_CHECK"
    WORKING=$((WORKING + 1))
    TOTAL=$((TOTAL + 1))
else
    echo "❌ Could not verify data"
    TOTAL=$((TOTAL + 1))
    FAILED_TESTS="$FAILED_TESTS\n  - Data integrity check failed"
fi

echo ""
echo "=============================="
SUCCESS_RATE=$((WORKING * 100 / TOTAL))
echo "📊 SYSTEM STATUS: ${SUCCESS_RATE}% OPERATIONAL"
echo "=============================="
echo "✅ Passed: $WORKING/$TOTAL tests"

if [ $SUCCESS_RATE -lt 100 ]; then
    echo ""
    echo "❌ FAILED TESTS:$FAILED_TESTS"
fi

if [ $SUCCESS_RATE -ge 95 ]; then
    echo ""
    echo "🎉 SYSTEM IS PRODUCTION READY!"
elif [ $SUCCESS_RATE -ge 80 ]; then
    echo ""
    echo "⚠️ System operational but needs attention"
else
    echo ""
    echo "🚨 CRITICAL: System below operational threshold"
fi

# Save results
cat > /home/mwwoodworth/code/SYSTEM_TEST_RESULTS.json << EOF
{
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%6NZ")",
    "version": "4.32",
    "total_tests": $TOTAL,
    "passed": $WORKING,
    "failed": $((TOTAL - WORKING)),
    "success_rate": $SUCCESS_RATE,
    "status": "$([ $SUCCESS_RATE -ge 95 ] && echo "production_ready" || echo "needs_attention")"
}
EOF

echo ""
echo "Results saved to SYSTEM_TEST_RESULTS.json"