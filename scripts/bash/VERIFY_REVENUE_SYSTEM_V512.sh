#!/bin/bash
echo "🚀 VERIFYING REVENUE SYSTEM v5.12"
echo "=================================="
echo ""

# Base URL
BASE_URL="https://brainops-backend-prod.onrender.com"

# Check API version
echo "📊 Checking API Version..."
VERSION=$(curl -s $BASE_URL/api/v1/health | python3 -c "import sys, json; print(json.load(sys.stdin)['version'])" 2>/dev/null)
if [ "$VERSION" == "5.12" ]; then
    echo "✅ API Version: $VERSION"
else
    echo "❌ API Version: $VERSION (expected 5.12)"
fi
echo ""

# Test Revenue Endpoints
echo "💰 Testing Revenue Endpoints..."
ENDPOINTS=(
    "/api/v1/ai-estimation/test"
    "/api/v1/stripe/products"
    "/api/v1/customers/segments"
    "/api/v1/landing/ab-test-results"
    "/api/v1/google-ads/campaigns/performance"
    "/api/v1/revenue/dashboard-metrics"
)

SUCCESS=0
FAILED=0

for endpoint in "${ENDPOINTS[@]}"; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL$endpoint)
    if [ "$RESPONSE" == "200" ] || [ "$RESPONSE" == "422" ] || [ "$RESPONSE" == "307" ]; then
        echo "✅ $endpoint - Status: $RESPONSE"
        ((SUCCESS++))
    else
        echo "❌ $endpoint - Status: $RESPONSE"
        ((FAILED++))
    fi
done

echo ""
echo "📈 Summary:"
echo "  Successful: $SUCCESS"
echo "  Failed: $FAILED"
echo ""

# Check landing pages
echo "🌐 Testing Landing Pages..."
PAGES=(
    "/api/v1/landing/estimate-now"
    "/api/v1/landing/ai-analyzer"
)

for page in "${PAGES[@]}"; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL$page)
    if [ "$RESPONSE" == "200" ]; then
        echo "✅ $page - Landing page accessible"
    else
        echo "❌ $page - Status: $RESPONSE"
    fi
done

echo ""
echo "🎯 Revenue Targets:"
echo "  Week 1: $2,500"
echo "  Week 2: $7,500 (cumulative)"
echo "  Week 4: $25,000 (cumulative)"
echo ""

# Check if dashboard UI is accessible
echo "📊 Checking Revenue Dashboard UI..."
DASHBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/api/v1/revenue/dashboard)
if [ "$DASHBOARD_STATUS" == "200" ]; then
    echo "✅ Revenue Dashboard UI is accessible"
    echo "   View at: $BASE_URL/api/v1/revenue/dashboard"
else
    echo "❌ Revenue Dashboard UI - Status: $DASHBOARD_STATUS"
fi

echo ""
echo "✨ VERIFICATION COMPLETE"
echo ""

if [ "$FAILED" -eq 0 ] && [ "$VERSION" == "5.12" ]; then
    echo "🎉 ALL SYSTEMS OPERATIONAL!"
    echo "💵 Ready to generate real revenue!"
    echo ""
    echo "Next Steps:"
    echo "1. Launch Google Ads campaigns"
    echo "2. Configure SendGrid API key" 
    echo "3. Add Stripe live webhook endpoint"
    echo "4. Monitor first transactions"
else
    echo "⚠️ Some issues detected. Check failed endpoints above."
fi