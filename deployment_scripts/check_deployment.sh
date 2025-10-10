#!/bin/bash

echo "🔍 Checking MyRoofGenius Deployment Status..."
echo "========================================="
echo ""

# Check main site
echo "1. Main Site (https://www.myroofgenius.com):"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://www.myroofgenius.com)
if [ "$STATUS" == "200" ]; then
    echo "   ✅ Status: $STATUS - LIVE!"
else
    echo "   ❌ Status: $STATUS - Not ready yet"
fi

# Check API health
echo ""
echo "2. Backend API (https://brainops-backend-prod.onrender.com):"
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://brainops-backend-prod.onrender.com/api/v1/health)
if [ "$API_STATUS" == "200" ]; then
    echo "   ✅ Status: $API_STATUS - Operational"
else
    echo "   ❌ Status: $API_STATUS - Issues detected"
fi

# Check specific pages
echo ""
echo "3. Key Pages:"
for PAGE in "login" "marketplace" "ai-estimator" "admin"; do
    PAGE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://www.myroofgenius.com/$PAGE)
    if [ "$PAGE_STATUS" == "200" ] || [ "$PAGE_STATUS" == "307" ]; then
        echo "   ✅ /$PAGE - Status: $PAGE_STATUS"
    else
        echo "   ❌ /$PAGE - Status: $PAGE_STATUS"
    fi
done

echo ""
echo "========================================="
echo "Note: Vercel deployments typically take 2-5 minutes"
echo "Run this script again in a minute to check progress"