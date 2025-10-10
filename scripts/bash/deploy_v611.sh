#!/bin/bash
set -e

echo "🚀 Deploying Backend v6.11 with Complete Revenue System"

# Docker login
echo "Logging into Docker Hub..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

# Build and push
echo "Building Docker image..."
docker build -t mwwoodworth/brainops-backend:v6.11 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v6.11 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v6.11
docker push mwwoodworth/brainops-backend:latest

echo "✅ Docker images pushed successfully"

# Trigger Render deployment
echo "Triggering Render deployment..."
curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM

echo "✅ Deployment triggered. Monitoring status..."
sleep 10

# Test the API
echo "Testing API health..."
curl -s https://brainops-backend-prod.onrender.com/api/v1/health | python3 -m json.tool

echo "✅ Backend v6.11 deployment complete!"
