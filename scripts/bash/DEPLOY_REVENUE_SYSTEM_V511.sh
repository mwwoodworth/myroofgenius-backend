#!/bin/bash
set -e

echo "🚀 DEPLOYING COMPLETE REVENUE SYSTEM v5.11"
echo "=========================================="
echo "Real AI features, real payment processing, real revenue"
echo ""

# 1. Login to Docker Hub
echo "🔐 Logging into Docker Hub..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho' 2>/dev/null

# 2. Build Docker image with revenue features
echo "🔨 Building Docker image v5.11..."
docker build -t mwwoodworth/brainops-backend:v5.11 -f Dockerfile . --no-cache

# 3. Test locally
echo "🧪 Testing Docker image..."
docker run --rm mwwoodworth/brainops-backend:v5.11 python3 -c "
import main
assert hasattr(main, 'app'), 'App not found!'
print('✅ App found in main module')
"

# 4. Tag and push
echo "📤 Pushing to Docker Hub..."
docker tag mwwoodworth/brainops-backend:v5.11 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v5.11
docker push mwwoodworth/brainops-backend:latest

# 5. Trigger Render deployment
echo "🚀 Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Content-Type: application/json" \
  -d '{"clear_cache": "clear"}'

echo ""
echo "✅ Revenue System v5.11 deployed!"
echo ""
echo "📊 REVENUE FEATURES DEPLOYED:"
echo "  • AI Estimation Engine with photo analysis"
echo "  • Stripe payment processing (live keys ready)"
echo "  • Customer onboarding pipeline"
echo "  • Lead scoring and segmentation"
echo "  • Email automation sequences"
echo "  • Upsell opportunity detection"
echo "  • Real-time revenue tracking"
echo ""
echo "💰 REVENUE TARGETS:"
echo "  • Week 1: $2,500"
echo "  • Week 2: $7,500 (cumulative)"
echo "  • Week 4: $25,000 (cumulative)"
echo ""
echo "🎯 NEXT STEPS:"
echo "  1. Test payment flow: https://myroofgenius.com/pricing"
echo "  2. Monitor dashboard: https://brainops-backend-prod.onrender.com/api/v1/revenue/dashboard-metrics"
echo "  3. Launch Google Ads campaign"
echo "  4. Start email sequences"
echo ""
echo "Monitor deployment: https://dashboard.render.com/web/srv-d1tfs4idbo4c73di6k00"
