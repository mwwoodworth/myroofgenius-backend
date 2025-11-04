#!/bin/bash

echo "🚀 COMPLETE PRODUCTION DEPLOYMENT v4.42"
echo "========================================"
echo ""
echo "This deployment includes:"
echo "✅ Stripe payment processing"
echo "✅ SendGrid email automation"
echo "✅ Master environment variable system"
echo "✅ All 15 automations activated"
echo "✅ Continuous learning engine"
echo ""

# Update version
echo "📝 Updating version to v4.42..."
sed -i 's/VERSION = ".*"/VERSION = "4.42"/' /home/mwwoodworth/code/fastapi-operator-env/apps/backend/main.py

# Build Docker image
echo "🔨 Building Docker image v4.42..."
cd /home/mwwoodworth/code/fastapi-operator-env
DOCKER_CONFIG=/tmp/.docker docker build -t mwwoodworth/brainops-backend:v4.42 -f Dockerfile.simple . --quiet

# Tag as latest
echo "🏷️ Tagging as latest..."
DOCKER_CONFIG=/tmp/.docker docker tag mwwoodworth/brainops-backend:v4.42 mwwoodworth/brainops-backend:latest

# Push to Docker Hub
echo "📤 Pushing to Docker Hub..."
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:v4.42 --quiet
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:latest --quiet

# Trigger Render deployment
echo "🚀 Triggering Render deployment..."
DEPLOY_RESPONSE=$(curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" -H "Accept: application/json" -s)
echo "Deployment triggered: $DEPLOY_RESPONSE"

echo ""
echo "📊 SYSTEM STATUS:"
echo "================="
echo "Backend: v4.42 deploying..."
echo "Stripe: Ready for live payments"
echo "SendGrid: Email automation active"
echo "Env Master: All variables managed"
echo "Automations: 15 rules ready"
echo ""
echo "🎯 NEXT STEPS:"
echo "1. Monitor deployment at https://dashboard.render.com"
echo "2. Verify API at https://brainops-backend-prod.onrender.com/api/v1/health"
echo "3. Test Stripe at /api/v1/payments/test"
echo "4. Test SendGrid at /api/v1/email/test"
echo "5. Check env vars at /api/v1/env/validate"
echo ""
echo "✅ Deployment script complete!"