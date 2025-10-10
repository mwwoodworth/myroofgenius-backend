#!/bin/bash

echo "🚀 MONITORING v9.5 DEPLOYMENT - COMPLETE AI FIX"
echo "=============================================="
echo "Started: $(date)"
echo ""

# Function to check and test
check_and_test() {
    VERSION=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('version', 'error'))" 2>/dev/null || echo "offline")
    echo "$(date +%H:%M:%S) - Version: $VERSION"
    
    if [ "$VERSION" = "9.5" ]; then
        echo ""
        echo "✅ v9.5 DEPLOYED!"
        echo ""
        echo "Testing all endpoints..."
        python3 LIVE_PRODUCTION_TEST_COMPLETE.py
        return 0
    fi
    return 1
}

# Monitor for 5 minutes
TIMEOUT=300
ELAPSED=0
INTERVAL=20

while [ $ELAPSED -lt $TIMEOUT ]; do
    if check_and_test; then
        exit 0
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""
echo "⏱️ Timeout. Manual check needed."