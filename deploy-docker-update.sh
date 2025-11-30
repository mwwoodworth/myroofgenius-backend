#!/bin/bash

# MyRoofGenius Backend Docker Deployment Script
# Updates the dockerized backend on Render via Docker Hub

set -e

echo "🚀 Starting MyRoofGenius Backend Docker Deployment"

# Configuration
DOCKER_USERNAME="myroofgenius"
DOCKER_REPO="myroofgenius-backend"
IMAGE_TAG="latest"
RENDER_SERVICE_ID="srv-d1tfs4idbo4c73di6k00"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t $DOCKER_USERNAME/$DOCKER_REPO:$IMAGE_TAG .

# Push to Docker Hub
echo "⬆️ Pushing to Docker Hub..."
docker push $DOCKER_USERNAME/$DOCKER_REPO:$IMAGE_TAG

# Trigger Render deployment
echo "🔄 Triggering Render deployment..."
curl -X POST \
  "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache": "clear"}'

echo "✅ Deployment triggered successfully!"
echo "📊 Monitor at: https://dashboard.render.com/web/$RENDER_SERVICE_ID"
