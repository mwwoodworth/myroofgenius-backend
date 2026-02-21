#!/bin/bash

echo "🤖 AI OS COMPLETE SYSTEM VERIFICATION"
echo "====================================="
echo "Date: $(date)"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend API Check
echo "1. BACKEND API STATUS"
echo "---------------------"
HEALTH=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health 2>/dev/null)
if [ ! -z "$HEALTH" ]; then
    VERSION=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null)
    echo -e "${GREEN}✅ Backend Online - Version: $VERSION${NC}"
    echo "$HEALTH" | python3 -m json.tool | head -20
else
    echo -e "${RED}❌ Backend Offline${NC}"
fi

echo ""
echo "2. AI COMPONENTS STATUS"
echo "-----------------------"

# Check each AI component
check_endpoint() {
    local NAME=$1
    local URL=$2
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "405" ]; then
        echo -e "${GREEN}✅ $NAME: Operational (HTTP $HTTP_CODE)${NC}"
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "${YELLOW}⚠️  $NAME: Not Found (HTTP 404) - May not be deployed yet${NC}"
    else
        echo -e "${RED}❌ $NAME: Error (HTTP $HTTP_CODE)${NC}"
    fi
}

check_endpoint "AI Board" "https://brainops-backend-prod.onrender.com/api/v1/ai-board/status"
check_endpoint "AUREA Intelligence" "https://brainops-backend-prod.onrender.com/api/v1/aurea/status"
check_endpoint "LangGraph Orchestrator" "https://brainops-backend-prod.onrender.com/api/v1/langgraph/status"
check_endpoint "ERP System" "https://brainops-backend-prod.onrender.com/api/v1/erp/status"
check_endpoint "CRM System" "https://brainops-backend-prod.onrender.com/api/v1/crm/customers"
check_endpoint "Revenue System" "https://brainops-backend-prod.onrender.com/api/v1/revenue/metrics"

echo ""
echo "3. FRONTEND APPLICATIONS"
echo "------------------------"

check_frontend() {
    local NAME=$1
    local URL=$2
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ $NAME: Online${NC}"
    else
        echo -e "${RED}❌ $NAME: Offline (HTTP $HTTP_CODE)${NC}"
    fi
}

check_frontend "MyRoofGenius" "https://myroofgenius.com"
check_frontend "WeatherCraft ERP" "https://weathercraft-erp.vercel.app"
check_frontend "BrainOps Task OS" "https://brainops-task-os.vercel.app"

echo ""
echo "4. DOCKER IMAGES"
echo "----------------"
LATEST_IMAGE=$(docker images mwwoodworth/brainops-backend --format "table {{.Tag}}\t{{.CreatedSince}}" | head -2 | tail -1)
echo "Latest Image: $LATEST_IMAGE"

echo ""
echo "5. GIT STATUS"
echo "-------------"
cd /home/mwwoodworth/code/fastapi-operator-env
LAST_COMMIT=$(git log --oneline -1)
echo "Last Commit: $LAST_COMMIT"
BRANCH=$(git branch --show-current)
echo "Current Branch: $BRANCH"

echo ""
echo "6. AI OS FEATURE SUMMARY"
echo "------------------------"
echo "Expected in v9.2:"
echo "  • AI Board - Neural network decision making"
echo "  • AUREA - 8 consciousness levels"
echo "  • LangGraph - 5 workflow orchestrations"
echo "  • Unified AI OS - System coordination"
echo "  • ERP - Complete business management"
echo "  • CRM - Customer relationship management"
echo "  • Revenue - Automated revenue generation"

echo ""
echo "7. DEPLOYMENT INFORMATION"
echo "-------------------------"
echo "Docker Hub: mwwoodworth/brainops-backend"
echo "Render Service: srv-d1tfs4idbo4c73di6k00"
echo "Last Deploy ID: dep-d2ii8aur433s73dqf3rg"
echo "Deploy Hook: https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=\${RENDER_DEPLOY_KEY}"

echo ""
echo "====================================="
if [ "$VERSION" = "9.2" ]; then
    echo -e "${GREEN}🎉 AI OS v9.2 FULLY DEPLOYED!${NC}"
elif [ "$VERSION" = "9.0" ] || [ "$VERSION" = "9.1" ]; then
    echo -e "${YELLOW}⏳ Deployment in progress... (Currently v$VERSION)${NC}"
else
    echo -e "${RED}⚠️  Unknown state - Check manually${NC}"
fi
echo "====================================="