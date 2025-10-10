#!/bin/bash

echo "🚀 Monitoring v9.4 Deployment"
echo "============================="
echo "Started: $(date)"
echo ""

# Function to check version
check_version() {
    VERSION=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('version', 'error'))" 2>/dev/null || echo "offline")
    echo "$(date +%H:%M:%S) - Version: $VERSION"
    
    if [ "$VERSION" = "9.4" ]; then
        echo ""
        echo "✅ v9.4 DEPLOYED!"
        return 0
    fi
    return 1
}

# Monitor for 5 minutes
TIMEOUT=300
ELAPSED=0
INTERVAL=15

while [ $ELAPSED -lt $TIMEOUT ]; do
    if check_version; then
        echo ""
        echo "🎉 v9.4 Deployment Complete!"
        echo ""
        echo "Now testing AI endpoints..."
        python3 TEST_AI_OS_V93.py
        exit 0
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""
echo "⏱️ Timeout. Check Render dashboard."