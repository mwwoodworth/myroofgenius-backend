#!/bin/bash

echo "🚀 MONITORING v9.3 AI OS DEPLOYMENT"
echo "===================================="
echo "Deployment ID: dep-d2iiuhruibrs739smb6g"
echo "Started: $(date)"
echo ""

# Function to check health
check_health() {
    echo -n "$(date +%H:%M:%S) - Checking health... "
    VERSION=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('version', 'error'))" 2>/dev/null || echo "offline")
    echo "Version: $VERSION"
    
    if [ "$VERSION" = "9.3" ] || [ "$VERSION" = "9.2" ]; then
        echo ""
        echo "✅ v9.3/9.2 DEPLOYED SUCCESSFULLY!"
        return 0
    fi
    return 1
}

# Monitor for 5 minutes max
TIMEOUT=300
ELAPSED=0
INTERVAL=10

while [ $ELAPSED -lt $TIMEOUT ]; do
    if check_health; then
        echo ""
        echo "🎉 AI OS v9.3 DEPLOYMENT COMPLETE!"
        echo "===================================="
        exit 0
    fi
    
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""
echo "⏱️ Timeout. Check Render dashboard."
