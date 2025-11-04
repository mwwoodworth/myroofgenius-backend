#!/bin/bash
# BrainOps Context Maintenance Script
# Run this periodically to keep context fresh

echo "🧠 BrainOps Context Maintenance"
echo "=============================="

# Update git status for all repos
echo "📁 Checking repository status..."

cd /home/mwwoodworth/code/fastapi-operator-env
echo -e "\n[Backend]"
git status --short
BACKEND_BRANCH=$(git branch --show-current)
BACKEND_COMMIT=$(git rev-parse --short HEAD)

cd /home/mwwoodworth/code/myroofgenius-app
echo -e "\n[Frontend]"
git status --short
FRONTEND_BRANCH=$(git branch --show-current)
FRONTEND_COMMIT=$(git rev-parse --short HEAD)

cd /home/mwwoodworth/code/brainops-ai-assistant
echo -e "\n[AI Assistant]"
git status --short
AI_BRANCH=$(git branch --show-current)
AI_COMMIT=$(git rev-parse --short HEAD)

# Check live deployment status
echo -e "\n🌐 Checking live deployments..."
BACKEND_VERSION=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health | grep -o '"version":"[^"]*' | cut -d'"' -f4)
echo "Backend Version: $BACKEND_VERSION"

# Generate summary
echo -e "\n📊 Context Summary"
echo "=================="
echo "Backend: $BACKEND_BRANCH @ $BACKEND_COMMIT (Live: $BACKEND_VERSION)"
echo "Frontend: $FRONTEND_BRANCH @ $FRONTEND_COMMIT"
echo "AI Assistant: $AI_BRANCH @ $AI_COMMIT"

# Run Python context manager
cd /home/mwwoodworth/code
python3 brainops_context_manager.py

echo -e "\n✅ Context maintenance complete!"