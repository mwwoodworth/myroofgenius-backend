#!/bin/bash
# Deploy BrainOps Backend v3.1.226
# CRITICAL FIX: Authentication and public endpoints

echo "🚀 DEPLOYING BRAINOPS BACKEND v3.1.226 - CRITICAL FIX"
echo "===================================================="
echo "✅ Fixed authentication parameter naming conflict"
echo "✅ Fixed public marketplace endpoints"
echo "✅ Fixed public automation endpoints"
echo "✅ Added comprehensive logging"
echo ""

# Navigate to backend directory
cd /home/mwwoodworth/code/fastapi-operator-env

# Git operations
echo "📦 Committing changes..."
git add -A
git commit -m "fix: Critical authentication and public endpoint fixes v3.1.226

- Fixed login endpoint parameter conflict (request -> login_data)
- Fixed all auth endpoints with proper parameter names
- Added comprehensive logging to all auth operations
- Fixed marketplace public endpoints to not require auth
- Fixed automation status endpoint to be public
- Clear error messages for all validation failures

CRITICAL: This fixes the 422 empty body issue that was blocking launch

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

# Docker operations
echo ""
echo "🐳 Building and pushing Docker images..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

docker build -t mwwoodworth/brainops-backend:v3.1.226 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v3.1.226 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.1.226
docker push mwwoodworth/brainops-backend:latest

# Trigger deployment
echo ""
echo "🔄 Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Accept: application/json"

echo ""
echo "✅ DEPLOYMENT INITIATED"
echo "==================="
echo "Version: v3.1.226"
echo "Critical Changes:"
echo "  - Login endpoint fixed (no more 422 empty body)"
echo "  - All auth endpoints use proper parameter names"
echo "  - Marketplace /products endpoint is now PUBLIC"
echo "  - Automations /status endpoint is now PUBLIC"
echo "  - Comprehensive logging for debugging"
echo ""
echo "📌 Expected Results:"
echo "  - Authentication will work properly"
echo "  - Login will return tokens with user data"
echo "  - Public endpoints will return 200 without auth"
echo "  - Validation errors will show proper messages"
echo ""
echo "🎯 Status: CRITICAL FIX FOR LAUNCH BLOCKER"