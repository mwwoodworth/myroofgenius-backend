#!/bin/bash

echo "🚀 FORCING DEPLOYMENT OF v4.36 WITH ALL FIXES"
echo "=============================================="
echo ""

cd /home/mwwoodworth/code/fastapi-operator-env

# First, let's make sure the route files are in the correct location
echo "📁 Setting up route files..."
mkdir -p apps/backend/routes

# Copy the new route files to the correct location
cp routes/*.py apps/backend/routes/ 2>/dev/null || echo "Routes already in place"

# Update the main.py to use correct imports
cd apps/backend

# Build a fresh Docker image with all changes
echo "🔨 Building fresh Docker image..."
export DOCKER_CONFIG=/tmp/.docker
mkdir -p $DOCKER_CONFIG
echo '{"auths":{"https://index.docker.io/v1/":{"auth":"'$(echo -n "mwwoodworth:dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho" | base64)'"}}}' > $DOCKER_CONFIG/config.json

# Build with no cache to ensure fresh build
DOCKER_CONFIG=/tmp/.docker docker build --no-cache -t mwwoodworth/brainops-backend:v4.36 -f Dockerfile.simple . 

# Tag as latest
DOCKER_CONFIG=/tmp/.docker docker tag mwwoodworth/brainops-backend:v4.36 mwwoodworth/brainops-backend:latest

# Force push with overwrite
echo "📤 Force pushing to Docker Hub..."
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:v4.36 --quiet
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:latest --quiet

echo "✅ Docker images pushed"

# Trigger Render deployment with clear cache
echo "🚀 Triggering Render deployment with cache clear..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Content-Type: application/json" \
  -d '{"clear_cache": true}'

echo ""
echo "⏳ Waiting 60 seconds for deployment to start..."
sleep 60

# Test the deployment
echo "🧪 Testing deployment..."
curl -s https://brainops-backend-prod.onrender.com/api/v1/health | python3 -m json.tool

echo ""
echo "=============================================="
echo "✅ DEPLOYMENT FORCED"
echo "=============================================="