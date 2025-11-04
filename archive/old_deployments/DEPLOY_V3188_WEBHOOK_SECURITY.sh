#!/bin/bash
# CLAUDEOS Deployment Script v3.1.188 - Webhook Security Update

echo "🚀 CLAUDEOS DEPLOYMENT v3.1.188 - WEBHOOK SECURITY"
echo "=================================================="

# Update version
echo "1. Updating version to v3.1.188..."
cd /home/mwwoodworth/code/fastapi-operator-env
sed -i 's/__version__ = "3.1.187"/__version__ = "3.1.188"/' apps/backend/main.py

# Login to Docker Hub
echo "2. Logging into Docker Hub..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

# Build Docker image
echo "3. Building Docker image v3.1.188..."
docker build -t mwwoodworth/brainops-backend:v3.1.188 -f Dockerfile .

# Tag as latest
echo "4. Tagging as latest..."
docker tag mwwoodworth/brainops-backend:v3.1.188 mwwoodworth/brainops-backend:latest

# Push to Docker Hub
echo "5. Pushing to Docker Hub..."
docker push mwwoodworth/brainops-backend:v3.1.188
docker push mwwoodworth/brainops-backend:latest

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "MANUAL STEPS REQUIRED:"
echo "1. Add to Render environment: VERCEL_WEBHOOK_SECRET=MQikxE5QJWYkTxc6sxMQgV5A"
echo "2. Deploy v3.1.188 on Render dashboard"
echo "3. Configure Vercel webhooks with this endpoint:"
echo "   https://brainops-backend-prod.onrender.com/api/v1/webhooks/vercel"
echo ""
echo "🎯 Once complete, the system will be 100% AUTONOMOUS!"