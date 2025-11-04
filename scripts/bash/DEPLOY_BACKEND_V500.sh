#!/bin/bash
# DEPLOY BACKEND v5.00 TO PRODUCTION
# Complete operational deployment

set -e

echo "🚀 DEPLOYING BACKEND v5.00"
echo "=========================="
echo ""

# 1. Login to Docker Hub
echo "1. Logging into Docker Hub..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

# 2. Navigate to backend directory
cd /home/mwwoodworth/code/fastapi-operator-env

# 3. Update version
echo "2. Updating version to 5.00..."
sed -i 's/API_VERSION = "4.49"/API_VERSION = "5.00"/' apps/backend/main.py || true
sed -i 's/"version": "4.49"/"version": "5.00"/' apps/backend/api_health.py || true

# 4. Build Docker image
echo "3. Building Docker image..."
docker build -t mwwoodworth/brainops-backend:v5.00 -f Dockerfile . --quiet

# 5. Tag as latest
echo "4. Tagging as latest..."
docker tag mwwoodworth/brainops-backend:v5.00 mwwoodworth/brainops-backend:latest

# 6. Push to Docker Hub
echo "5. Pushing to Docker Hub..."
docker push mwwoodworth/brainops-backend:v5.00 --quiet
docker push mwwoodworth/brainops-backend:latest --quiet

# 7. Trigger Render deployment
echo "6. Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"

echo ""
echo "✅ BACKEND v5.00 DEPLOYMENT INITIATED"
echo ""
echo "Monitor deployment at:"
echo "  https://dashboard.render.com/web/srv-d1tfs4idbo4c73di6k00"
echo ""
echo "Test when ready:"
echo "  curl https://brainops-backend-prod.onrender.com/api/v1/health"
echo ""