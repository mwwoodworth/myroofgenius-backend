#!/bin/bash

echo "🚀 COMPLETE BUILD AND DEPLOY v4.37"
echo "==================================="
echo ""

# Navigate to backend directory
cd /home/mwwoodworth/code/fastapi-operator-env/apps/backend

# Update version
echo "📝 Updating version to 4.37..."
sed -i 's/VERSION = "4.36"/VERSION = "4.37"/' main.py

# Ensure all route files exist
echo "✅ Verifying route files..."
ls -la routes/ | grep -E "ai_board_status|memory_recent|marketplace_products|agents_list|langgraph_workflows" || echo "New routes need to be added"

# Create a complete Dockerfile that works
cat > Dockerfile.complete << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Ensure routes directory is included
COPY routes/ ./routes/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Build Docker image
echo "🔨 Building Docker image v4.37..."
export DOCKER_CONFIG=/tmp/.docker
mkdir -p $DOCKER_CONFIG
echo '{"auths":{"https://index.docker.io/v1/":{"auth":"'$(echo -n "mwwoodworth:dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho" | base64)'"}}}' > $DOCKER_CONFIG/config.json

DOCKER_CONFIG=/tmp/.docker docker build -t mwwoodworth/brainops-backend:v4.37 -f Dockerfile.complete . --quiet

# Tag as latest
DOCKER_CONFIG=/tmp/.docker docker tag mwwoodworth/brainops-backend:v4.37 mwwoodworth/brainops-backend:latest

# Push to Docker Hub
echo "📤 Pushing to Docker Hub..."
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:v4.37 --quiet
DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:latest --quiet

echo "✅ Docker images pushed"

# Trigger deployment
echo "🚀 Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Content-Type: application/json" \
  -d '{"clear_cache": true}'

echo ""
echo "==================================="
echo "✅ BUILD AND DEPLOY COMPLETE"
echo "==================================="
echo ""
echo "Version: 4.37"
echo "Status: Deploying to production"
echo ""
echo "Test in 2-3 minutes:"
echo "curl https://brainops-backend-prod.onrender.com/api/v1/health"
echo "curl https://brainops-backend-prod.onrender.com/api/v1/ai-board/status"
echo "curl https://brainops-backend-prod.onrender.com/api/v1/marketplace/products"