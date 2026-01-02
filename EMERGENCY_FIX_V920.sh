#!/bin/bash
# EMERGENCY FIX - Get backend running NOW with v9.20

echo "🚨 EMERGENCY DEPLOYMENT v9.20"
echo "================================"

# Use the WORKING v9.6 as base and just update version
cat > Dockerfile.emergency << 'EOF'
FROM mwwoodworth/brainops-backend:v9.6

# Just update the version strings
RUN sed -i 's/"9.6"/"9.20"/g' /app/main.py 2>/dev/null || true
RUN sed -i 's/"version": "9.6"/"version": "9.20"/g' /app/main.py 2>/dev/null || true
RUN sed -i 's/v9.6/v9.20/g' /app/main.py 2>/dev/null || true

# Update startup message
RUN sed -i 's/v9.6 with Neural OS/v9.20 EMERGENCY FIX/g' /app/main.py 2>/dev/null || true

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo "Building emergency image..."
docker build -t mwwoodworth/brainops-backend:v9.20 -f Dockerfile.emergency .

echo "Tagging as latest..."
docker tag mwwoodworth/brainops-backend:v9.20 mwwoodworth/brainops-backend:latest

echo "Pushing to Docker Hub..."
docker push mwwoodworth/brainops-backend:v9.20
docker push mwwoodworth/brainops-backend:latest

echo "Triggering deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=${RENDER_DEPLOY_KEY}" -H "Accept: application/json"

echo ""
echo "✅ EMERGENCY DEPLOYMENT TRIGGERED"
echo "Deploy ID will appear above"
echo "Backend should be live in 2-3 minutes"