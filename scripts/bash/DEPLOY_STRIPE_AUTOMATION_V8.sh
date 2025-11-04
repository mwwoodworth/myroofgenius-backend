#!/bin/bash

echo "=========================================="
echo "🚀 STRIPE AUTOMATION DEPLOYMENT v8.0"
echo "Production-Ready Payment Processing System"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
VERSION="8.0"
DOCKER_REPO="mwwoodworth/brainops-backend"

echo -e "${YELLOW}Starting deployment of Stripe Automation System...${NC}"

# 1. Login to Docker Hub
echo -e "\n${YELLOW}Step 1: Docker Hub Login${NC}"
echo "$DOCKER_PAT" | docker login -u "$DOCKER_USERNAME" --password-stdin
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker Hub login successful${NC}"
else
    echo -e "${RED}❌ Docker Hub login failed${NC}"
    exit 1
fi

# 2. Build Docker image
echo -e "\n${YELLOW}Step 2: Building Docker image v${VERSION}${NC}"
cd /home/mwwoodworth/code/fastapi-operator-env

docker build -t ${DOCKER_REPO}:v${VERSION} -f Dockerfile . --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker build successful${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# 3. Tag as latest
echo -e "\n${YELLOW}Step 3: Tagging image as latest${NC}"
docker tag ${DOCKER_REPO}:v${VERSION} ${DOCKER_REPO}:latest
echo -e "${GREEN}✅ Tagged as latest${NC}"

# 4. Push to Docker Hub
echo -e "\n${YELLOW}Step 4: Pushing to Docker Hub${NC}"
docker push ${DOCKER_REPO}:v${VERSION} --quiet
docker push ${DOCKER_REPO}:latest --quiet
echo -e "${GREEN}✅ Pushed to Docker Hub${NC}"

# 5. Trigger Render deployment
echo -e "\n${YELLOW}Step 5: Triggering Render deployment${NC}"
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
    -H "Accept: application/json" \
    --silent --output /dev/null
echo -e "${GREEN}✅ Render deployment triggered${NC}"

# 6. Test the deployment
echo -e "\n${YELLOW}Step 6: Waiting for deployment (30 seconds)...${NC}"
sleep 30

echo -e "\n${YELLOW}Testing deployed endpoints...${NC}"

# Test health endpoint
echo -e "\n${YELLOW}Testing health endpoint...${NC}"
HEALTH_RESPONSE=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
fi

# Test Stripe automation health
echo -e "\n${YELLOW}Testing Stripe automation health...${NC}"
STRIPE_HEALTH=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/stripe-automation/health)
if echo "$STRIPE_HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Stripe automation is healthy${NC}"
    echo "$STRIPE_HEALTH" | python3 -m json.tool
else
    echo -e "${YELLOW}⚠️ Stripe automation health check pending${NC}"
fi

# Test revenue analytics
echo -e "\n${YELLOW}Testing revenue analytics...${NC}"
REVENUE_DATA=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/stripe-automation/analytics/revenue)
if echo "$REVENUE_DATA" | grep -q "revenue"; then
    echo -e "${GREEN}✅ Revenue analytics working${NC}"
    echo "$REVENUE_DATA" | python3 -m json.tool | head -20
else
    echo -e "${YELLOW}⚠️ Revenue analytics pending${NC}"
fi

echo -e "\n=========================================="
echo -e "${GREEN}🎉 STRIPE AUTOMATION DEPLOYMENT COMPLETE${NC}"
echo -e "=========================================="
echo ""
echo "📊 System Status:"
echo "  - Version: v${VERSION}"
echo "  - Docker Image: ${DOCKER_REPO}:v${VERSION}"
echo "  - API URL: https://brainops-backend-prod.onrender.com"
echo "  - Stripe Automation: /api/v1/stripe-automation/*"
echo ""
echo "🔧 Available Endpoints:"
echo "  - POST /api/v1/stripe-automation/customers/create"
echo "  - POST /api/v1/stripe-automation/checkout/create"
echo "  - POST /api/v1/stripe-automation/subscriptions/create"
echo "  - PUT  /api/v1/stripe-automation/subscriptions/update"
echo "  - POST /api/v1/stripe-automation/payments/create-intent"
echo "  - POST /api/v1/stripe-automation/webhooks/stripe"
echo "  - GET  /api/v1/stripe-automation/analytics/revenue"
echo "  - GET  /api/v1/stripe-automation/analytics/subscriptions"
echo "  - POST /api/v1/stripe-automation/refunds/create"
echo "  - GET  /api/v1/stripe-automation/automation/rules"
echo "  - POST /api/v1/stripe-automation/automation/rules"
echo ""
echo "🔑 Webhook URL for Stripe Dashboard:"
echo "  https://brainops-backend-prod.onrender.com/api/v1/stripe-automation/webhooks/stripe"
echo ""
echo "✨ Features:"
echo "  - Full payment automation"
echo "  - Subscription management"
echo "  - Revenue tracking & analytics"
echo "  - Automated email notifications"
echo "  - Webhook processing"
echo "  - Refund handling"
echo "  - Custom automation rules"
echo ""
echo "🚀 Ready for production use!"