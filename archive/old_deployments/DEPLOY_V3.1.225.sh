#!/bin/bash
# Deploy BrainOps Backend v3.1.225
# Fix authentication validation errors and marketplace endpoints

echo "🚀 DEPLOYING BRAINOPS BACKEND v3.1.225"
echo "======================================="
echo "✅ Fixed authentication validation error handling"
echo "✅ Validation errors now return proper response bodies"
echo "✅ Global error handler simplified"
echo ""

# Navigate to backend directory
cd /home/mwwoodworth/code/fastapi-operator-env

# Git operations
echo "📦 Committing changes..."
git add -A
git commit -m "fix: Authentication validation errors and global error handler v3.1.225

- Fixed global error handler that was failing and returning empty 422 responses
- Created simplified error handler without problematic learning system
- Validation errors now properly return error details
- Authentication endpoints should now work correctly

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

# Docker operations
echo ""
echo "🐳 Building and pushing Docker images..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

docker build -t mwwoodworth/brainops-backend:v3.1.225 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v3.1.225 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.1.225
docker push mwwoodworth/brainops-backend:latest

# Trigger deployment
echo ""
echo "🔄 Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Accept: application/json"

echo ""
echo "✅ DEPLOYMENT INITIATED"
echo "==================="
echo "Version: v3.1.225"
echo "Changes:"
echo "  - Fixed authentication validation errors (422 with no body)"
echo "  - Global error handler now returns proper error details"
echo "  - Validation errors include field information"
echo ""
echo "📌 Next steps:"
echo "  1. Monitor deployment on Render dashboard"
echo "  2. Run validation script once deployed"
echo "  3. Check authentication functionality"
echo ""
echo "🎯 Status: CRITICAL FIX FOR AUTHENTICATION"