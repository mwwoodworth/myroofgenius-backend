#!/bin/bash
# Deploy BrainOps Backend v3.1.231
# CRITICAL FIX: Load the fixed auth.py instead of auth_simple_v228

echo "🚀 DEPLOYING BRAINOPS BACKEND v3.1.231 - LOAD CORRECT AUTH ROUTE"
echo "================================================================"
echo "✅ Fixed auth.py with proper parameter names"
echo "✅ Updated ROUTE_PRIORITY to load 'auth' instead of 'auth_simple_v228'"
echo ""

# Navigate to backend directory
cd /home/mwwoodworth/code/fastapi-operator-env

# Git operations
echo ""
echo "📦 Committing changes..."
git add -A
git commit -m "fix: Load original auth.py instead of auth_simple_v228 v3.1.231

- Updated ROUTE_PRIORITY to load 'auth' route
- This loads the fixed auth.py with proper parameter names
- Previously was loading auth_simple_v228 which doesn't have the fix

CRITICAL: This should finally fix authentication!

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com)"

git push origin main

# Docker operations
echo ""
echo "🐳 Building and pushing Docker images..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

docker build -t mwwoodworth/brainops-backend:v3.1.231 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v3.1.231 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.1.231
docker push mwwoodworth/brainops-backend:latest

# Trigger deployment
echo ""
echo "🔄 Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Accept: application/json"

echo ""
echo "✅ DEPLOYMENT INITIATED"
echo "===================="
echo "Version: v3.1.231"
echo "Critical Changes:"
echo "  - Load correct auth route (auth.py)"
echo "  - No longer loading auth_simple_v228"
echo "  - Fixed auth.py will now be used"
echo ""
echo "📌 Expected Results:"
echo "  - Login endpoint will finally work!"
echo "  - All auth endpoints functional"
echo "  - Proper error messages on validation"
echo ""
echo "🎯 THIS SHOULD BE THE FINAL FIX!"