#!/bin/bash

# DEPLOY VERSION 4.36 - COMPLETE SYSTEM ACTIVATION
# Date: 2025-08-17
# Changes: Added missing endpoints, activated AI memory, enabled automations

echo "🚀 DEPLOYING VERSION 4.36..."
echo "=============================="
echo ""

# Navigate to backend directory
cd /home/mwwoodworth/code/fastapi-operator-env/apps/backend

# Login to Docker Hub
echo "🔐 Logging into Docker Hub..."
export DOCKER_CONFIG=/tmp/.docker
mkdir -p $DOCKER_CONFIG
echo '{"auths":{"https://index.docker.io/v1/":{"auth":"'$(echo -n "mwwoodworth:dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho" | base64)'"}}}' > $DOCKER_CONFIG/config.json

# Build Docker image
echo "🏗️ Building Docker image v4.36..."
DOCKER_CONFIG=/tmp/.docker docker build -t mwwoodworth/brainops-backend:v4.36 -f Dockerfile . --quiet

# Tag as latest
echo "🏷️ Tagging as latest..."
DOCKER_CONFIG=/tmp/.docker docker tag mwwoodworth/brainops-backend:v4.36 mwwoodworth/brainops-backend:latest

# Push to Docker Hub
echo "📤 Pushing to Docker Hub..."
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:v4.36 --quiet
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:latest --quiet

echo "✅ Docker images pushed successfully"
echo ""

# Trigger Render deployment
echo "🚀 Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Content-Type: application/json" \
  -d '{"clear_cache": true}'

echo ""
echo "=============================="
echo "✅ DEPLOYMENT INITIATED"
echo "=============================="
echo ""
echo "Version: 4.36"
echo "Changes:"
echo "  - Added AI Board status endpoints"
echo "  - Added Memory system endpoints"
echo "  - Added Marketplace products endpoints"
echo "  - Added Agents list endpoints"
echo "  - Added LangGraph workflows endpoints"
echo "  - Activated AI memory system"
echo "  - Enabled automation rules"
echo "  - CenterPoint sync running"
echo ""
echo "Monitor deployment at:"
echo "https://dashboard.render.com"
echo ""
echo "Test endpoints:"
echo "  curl https://brainops-backend-prod.onrender.com/api/v1/health"
echo "  curl https://brainops-backend-prod.onrender.com/api/v1/ai-board/status"
echo "  curl https://brainops-backend-prod.onrender.com/api/v1/memory/recent"
echo "  curl https://brainops-backend-prod.onrender.com/api/v1/marketplace/products"
echo "  curl https://brainops-backend-prod.onrender.com/api/v1/agents/list"
echo "  curl https://brainops-backend-prod.onrender.com/api/v1/langgraph/workflows"