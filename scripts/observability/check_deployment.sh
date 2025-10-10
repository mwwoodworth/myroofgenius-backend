#!/bin/bash
# Comprehensive deployment checker for Render

echo "============================================"
echo "RENDER DEPLOYMENT STATUS CHECK"
echo "============================================"
echo "Time: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
echo ""

# Check what Docker image hash is currently deployed
echo "🐳 CHECKING DOCKER IMAGE..."
echo "Latest image on Docker Hub:"
docker manifest inspect mwwoodworth/brainops-backend:latest 2>/dev/null | grep -A 2 "digest" | head -3 || echo "Unable to check Docker Hub"

echo ""
echo "📦 CHECKING DEPLOYED VERSION..."
# Get the actual version from the API
VERSION=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null)
echo "API reports version: $VERSION"

echo ""
echo "🔍 TESTING REVENUE ENDPOINTS..."
# Test each revenue endpoint
endpoints=(
    "test-revenue"
    "ai-estimation"
    "stripe-revenue"
    "customer-pipeline"
    "landing-pages"
    "google-ads"
    "revenue-dashboard"
)

for endpoint in "${endpoints[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "https://brainops-backend-prod.onrender.com/api/v1/$endpoint/")
    if [ "$response" = "404" ]; then
        echo "  ❌ /api/v1/$endpoint/ - Not Found (404)"
    else
        echo "  ✅ /api/v1/$endpoint/ - Accessible ($response)"
    fi
done

echo ""
echo "📝 CHECKING LOCAL VERSION..."
# Check what version is in our local main.py
LOCAL_VERSION=$(grep -E "version.*=" main.py | head -1 | sed 's/.*version.*=.*"\(.*\)".*/\1/')
echo "Local main.py version: $LOCAL_VERSION"

echo ""
echo "🚀 DEPLOYMENT RECOMMENDATIONS:"
if [ "$VERSION" != "$LOCAL_VERSION" ]; then
    echo "  ⚠️  Version mismatch! Deployed: $VERSION, Local: $LOCAL_VERSION"
    echo "  1. Build new Docker image: docker build -t mwwoodworth/brainops-backend:v$LOCAL_VERSION ."
    echo "  2. Tag as latest: docker tag mwwoodworth/brainops-backend:v$LOCAL_VERSION mwwoodworth/brainops-backend:latest"
    echo "  3. Push both: docker push mwwoodworth/brainops-backend:v$LOCAL_VERSION && docker push mwwoodworth/brainops-backend:latest"
    echo "  4. Trigger Render deploy webhook or manual deploy"
else
    echo "  ✅ Versions match"
fi

echo ""
echo "💡 TO DEBUG FURTHER:"
echo "  1. Check container logs: export RENDER_API_KEY=rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx"
echo "  2. SSH to container: ssh srv-d1tfs4idbo4c73di6k00@ssh.oregon.render.com"
echo "  3. Inside container: python3 -c 'import main; print(main.app.routes)'"
echo "  4. Check imports: python3 -c 'from routes import test_revenue'"
echo ""
echo "============================================"