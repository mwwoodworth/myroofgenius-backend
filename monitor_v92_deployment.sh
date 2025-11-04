#!/bin/bash

echo "🚀 MONITORING v9.2 AI OS DEPLOYMENT"
echo "===================================="
echo "Deployment ID: dep-d2ii8aur433s73dqf3rg"
echo "Started: $(date)"
echo ""

# Function to check health
check_health() {
    echo -n "$(date +%H:%M:%S) - Checking health... "
    VERSION=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('version', 'error'))" 2>/dev/null || echo "offline")
    echo "Version: $VERSION"
    
    if [ "$VERSION" = "9.2" ]; then
        echo ""
        echo "✅ v9.2 DEPLOYED SUCCESSFULLY!"
        return 0
    fi
    return 1
}

# Function to test AI endpoints
test_ai_endpoints() {
    echo ""
    echo "Testing AI OS Endpoints:"
    echo "------------------------"
    
    # Test AI Board
    echo -n "AI Board: "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://brainops-backend-prod.onrender.com/api/v1/ai-board/status)
    [ "$HTTP_CODE" = "200" ] && echo "✅ Operational" || echo "❌ Error ($HTTP_CODE)"
    
    # Test AUREA
    echo -n "AUREA: "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://brainops-backend-prod.onrender.com/api/v1/aurea/status)
    [ "$HTTP_CODE" = "200" ] && echo "✅ Operational" || echo "❌ Error ($HTTP_CODE)"
    
    # Test LangGraph
    echo -n "LangGraph: "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://brainops-backend-prod.onrender.com/api/v1/langgraph/status)
    [ "$HTTP_CODE" = "200" ] && echo "✅ Operational" || echo "❌ Error ($HTTP_CODE)"
}

# Monitor for up to 10 minutes
TIMEOUT=600
ELAPSED=0
INTERVAL=15

while [ $ELAPSED -lt $TIMEOUT ]; do
    if check_health; then
        test_ai_endpoints
        echo ""
        echo "🎉 AI OS v9.2 DEPLOYMENT COMPLETE!"
        echo "===================================="
        echo "Features:"
        echo "  - AI Board with neural network decision making"
        echo "  - AUREA intelligence with 8 consciousness levels"
        echo "  - LangGraph with 5 workflow orchestrations"
        echo "  - Unified AI OS orchestration"
        echo ""
        echo "API Endpoints:"
        echo "  - https://brainops-backend-prod.onrender.com/api/v1/ai-board/*"
        echo "  - https://brainops-backend-prod.onrender.com/api/v1/aurea/*"
        echo "  - https://brainops-backend-prod.onrender.com/api/v1/langgraph/*"
        echo ""
        echo "Monitor at: https://dashboard.render.com/web/srv-d1tfs4idbo4c73di6k00"
        exit 0
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""
echo "⏱️ Timeout reached. Deployment may still be in progress."
echo "Check Render dashboard for status."