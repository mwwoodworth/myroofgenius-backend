#!/bin/bash
# Force clean Docker build for BrainOps Backend v1.3.4
# This ensures no stale cache affects the build

echo "=== BrainOps Backend Clean Docker Build v1.3.4 ==="
echo ""

# Login to Docker Hub
echo "Logging into Docker Hub..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

# Clean up any existing containers and images
echo ""
echo "Cleaning up existing containers and images..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker rmi mwwoodworth/brainops-backend:v1.3.4 2>/dev/null || true
docker rmi mwwoodworth/brainops-backend:latest 2>/dev/null || true

# Prune Docker build cache
echo ""
echo "Pruning Docker build cache..."
docker builder prune -af

# Build with no cache
echo ""
echo "Building Docker image with no cache..."
cd /home/mwwoodworth/code/fastapi-operator-env
docker build --no-cache -t mwwoodworth/brainops-backend:v1.3.4 -f Dockerfile .

# Tag as latest
echo ""
echo "Tagging as latest..."
docker tag mwwoodworth/brainops-backend:v1.3.4 mwwoodworth/brainops-backend:latest

# Push both tags
echo ""
echo "Pushing to Docker Hub..."
docker push mwwoodworth/brainops-backend:v1.3.4
docker push mwwoodworth/brainops-backend:latest

echo ""
echo "=== Build Complete ==="
echo "Images pushed:"
echo "  - mwwoodworth/brainops-backend:v1.3.4"
echo "  - mwwoodworth/brainops-backend:latest"
echo ""
echo "Ready for deployment on Render!"