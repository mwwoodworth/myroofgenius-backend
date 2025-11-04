#!/bin/bash
# Force deployment of v3.3.26 with revenue generation

echo "=================================================="
echo "🚀 FORCE DEPLOYING v3.3.26 - REVENUE GENERATION"
echo "=================================================="

# Ensure Docker is configured
export DOCKER_CONFIG=/tmp/.docker
mkdir -p $DOCKER_CONFIG
echo '{"auths":{"https://index.docker.io/v1/":{"auth":"'$(echo -n "mwwoodworth:dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho" | base64)'"}}}' > $DOCKER_CONFIG/config.json

# Rebuild with timestamp to force new image
cd /home/mwwoodworth/code/fastapi-operator-env

# Add timestamp to force rebuild
echo "BUILD_TIME=$(date +%s)" >> Dockerfile

# Build and push
echo "🔨 Building Docker image..."
DOCKER_CONFIG=/tmp/.docker docker build --no-cache -t mwwoodworth/brainops-backend:v3.3.26-rev2 -f Dockerfile .
DOCKER_CONFIG=/tmp/.docker docker tag mwwoodworth/brainops-backend:v3.3.26-rev2 mwwoodworth/brainops-backend:latest
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:v3.3.26-rev2
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:latest

# Multiple deployment triggers
echo "🎯 Triggering deployment (attempt 1)..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"

sleep 2

echo "🎯 Triggering deployment (attempt 2)..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT TRIGGERED - CHECK STATUS"
echo "=================================================="
echo ""
echo "Monitor at: https://dashboard.render.com"
echo "Health: https://brainops-backend-prod.onrender.com/api/v1/health"
echo ""
echo "💰 REVENUE ENDPOINTS READY:"
echo "  - /api/v1/aurea/revenue/generate"
echo "  - /api/v1/revenue/opportunities"
echo "  - /api/v1/revenue/dashboard"
echo ""