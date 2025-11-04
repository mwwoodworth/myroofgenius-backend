#!/bin/bash
# Unified Deployment Automation System
# Version: 1.0.0
# Date: 2025-08-18

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
DOCKER_USER="mwwoodworth"
DOCKER_PAT="dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho"
RENDER_HOOK="https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"

echo -e "${GREEN}🚀 BRAINOPS UNIFIED DEPLOYMENT SYSTEM${NC}"
echo "======================================="

# Function to deploy backend
deploy_backend() {
    echo -e "${YELLOW}📦 Deploying Backend...${NC}"
    
    cd /home/mwwoodworth/code/fastapi-operator-env
    
    # Get next version
    CURRENT_VERSION=$(grep 'API_VERSION' main.py | cut -d'"' -f2)
    IFS='.' read -ra VERSION_PARTS <<< "$CURRENT_VERSION"
    PATCH=$((VERSION_PARTS[2] + 1))
    NEW_VERSION="${VERSION_PARTS[0]}.${VERSION_PARTS[1]}.$PATCH"
    
    # Update version
    sed -i "s/API_VERSION = \".*\"/API_VERSION = \"$NEW_VERSION\"/" main.py
    
    # Docker build and push
    echo -e "${YELLOW}🐳 Building Docker image v$NEW_VERSION...${NC}"
    docker login -u $DOCKER_USER -p "$DOCKER_PAT" 2>/dev/null
    docker build -t mwwoodworth/brainops-backend:v$NEW_VERSION -f Dockerfile . --quiet
    docker tag mwwoodworth/brainops-backend:v$NEW_VERSION mwwoodworth/brainops-backend:latest
    docker push mwwoodworth/brainops-backend:v$NEW_VERSION --quiet
    docker push mwwoodworth/brainops-backend:latest --quiet
    
    # Trigger Render deployment
    echo -e "${YELLOW}🔄 Triggering Render deployment...${NC}"
    curl -X POST "$RENDER_HOOK" -H "Content-Type: application/json" -s
    
    echo -e "${GREEN}✅ Backend deployed: v$NEW_VERSION${NC}"
}

# Function to deploy frontend
deploy_frontend() {
    echo -e "${YELLOW}🎨 Deploying Frontend...${NC}"
    
    cd /home/mwwoodworth/code/myroofgenius-app
    git add -A
    git commit -m "chore: Auto-deployment $(date +%Y%m%d-%H%M%S)" || true
    git push origin main
    
    echo -e "${GREEN}✅ Frontend deployment triggered${NC}"
}

# Function to run tests
run_tests() {
    echo -e "${YELLOW}🧪 Running tests...${NC}"
    
    # Test API health
    response=$(curl -s -o /dev/null -w "%{http_code}" https://brainops-backend-prod.onrender.com/api/v1/health)
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ API health check passed${NC}"
    else
        echo -e "${RED}❌ API health check failed${NC}"
        exit 1
    fi
}

# Main execution
case "${1:-all}" in
    backend)
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    test)
        run_tests
        ;;
    all)
        deploy_backend
        sleep 30
        run_tests
        deploy_frontend
        ;;
    *)
        echo "Usage: $0 {backend|frontend|test|all}"
        exit 1
        ;;
esac

echo -e "${GREEN}🎉 Deployment complete!${NC}"
