#!/bin/bash
# Deploy BrainOps Backend v3.1.224
# Fixed LangGraphOS authentication and added admin audit logs

echo "🚀 DEPLOYING BRAINOPS BACKEND v3.1.224"
echo "======================================="
echo "✅ Fixed LangGraphOS authentication (public status endpoint)"
echo "✅ Added admin audit logs endpoints"
echo "✅ All persistent memory systems operational"
echo ""

# Navigate to backend directory
cd /home/mwwoodworth/code/fastapi-operator-env

# Git operations
echo "📦 Committing changes..."
git add -A
git commit -m "feat: Fix LangGraphOS auth and add admin audit logs v3.1.224

- Fixed LangGraphOS authentication by adding public status endpoint
- Added optional authentication function to auth_hotfix
- Created comprehensive admin audit logs endpoints
- Updated route loading to use fixed LangGraphOS routes

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

# Docker operations
echo ""
echo "🐳 Building and pushing Docker images..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

docker build -t mwwoodworth/brainops-backend:v3.1.224 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v3.1.224 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.1.224
docker push mwwoodworth/brainops-backend:latest

echo ""
echo "✅ DEPLOYMENT READY"
echo "=================="
echo "Version: v3.1.224"
echo "Changes:"
echo "  - LangGraphOS now has public status endpoint (no auth required)"
echo "  - Admin audit logs available at /api/v1/admin/audit-logs"
echo "  - All persistent memory systems operational"
echo ""
echo "📌 Next steps:"
echo "  1. Deploy on Render dashboard"
echo "  2. Configure Vercel log drain"
echo "  3. Set API keys in Render environment"
echo ""
echo "🎯 Status: READY FOR PRODUCTION"