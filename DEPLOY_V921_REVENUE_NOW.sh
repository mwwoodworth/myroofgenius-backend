#!/bin/bash
echo "🚀 EMERGENCY REVENUE DEPLOYMENT v9.21"
echo "====================================="

# Login to Docker
echo "Logging into Docker Hub..."
DOCKER_CONFIG=/tmp/.docker docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

# Build clean image with revenue enabled
echo "Building v9.21 with revenue system..."
DOCKER_CONFIG=/tmp/.docker docker build -t mwwoodworth/brainops-backend:v9.21 -f Dockerfile . --quiet

# Tag as latest
echo "Tagging as latest..."
DOCKER_CONFIG=/tmp/.docker docker tag mwwoodworth/brainops-backend:v9.21 mwwoodworth/brainops-backend:latest

# Push to Docker Hub
echo "Pushing to Docker Hub..."
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:v9.21 --quiet
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:latest --quiet

# Trigger deployment
echo "Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json"

echo ""
echo "✅ v9.21 DEPLOYMENT TRIGGERED"
echo "Backend will be live in 2-3 minutes"
echo "Starting revenue activation..."
