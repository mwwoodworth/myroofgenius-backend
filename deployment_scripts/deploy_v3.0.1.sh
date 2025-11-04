#!/bin/bash

# BrainOps Backend v3.0.1 Deployment Script
# Fixes: Router crashes and memory duplicate key protection

echo "🚀 BrainOps Backend v3.0.1 Deployment"
echo "====================================="
echo ""
echo "This script will build and push the Docker image."
echo ""

# Navigate to the backend directory
cd /home/mwwoodworth/code/fastapi-operator-env || exit 1

# Docker Hub credentials
DOCKER_USERNAME="mwwoodworth"
DOCKER_TOKEN="dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho"
VERSION="v3.0.1"

echo "1. Login to Docker Hub..."
docker login -u ${DOCKER_USERNAME} -p '${DOCKER_TOKEN}'

echo ""
echo "2. Building Docker image..."
docker build -t ${DOCKER_USERNAME}/brainops-backend:${VERSION} -f Dockerfile .

echo ""
echo "3. Tagging as latest..."
docker tag ${DOCKER_USERNAME}/brainops-backend:${VERSION} ${DOCKER_USERNAME}/brainops-backend:latest

echo ""
echo "4. Pushing to Docker Hub..."
docker push ${DOCKER_USERNAME}/brainops-backend:${VERSION}
docker push ${DOCKER_USERNAME}/brainops-backend:latest

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "Key fixes in v3.0.1:"
echo "- Added duplicate key protection to memory service"
echo "- Fixed router crashes by skipping problematic ERP routes"
echo "- Handles UniqueViolation errors gracefully"
echo ""
echo "Next steps:"
echo "1. Go to Render dashboard"
echo "2. Manually trigger deployment"
echo "3. Monitor logs for any issues"
echo ""
echo "Test endpoints:"
echo "- https://brainops-backend-prod.onrender.com/health"
echo "- https://brainops-backend-prod.onrender.com/api/v1/health"
echo "- https://brainops-backend-prod.onrender.com/api/v1/memory/persistent/read"