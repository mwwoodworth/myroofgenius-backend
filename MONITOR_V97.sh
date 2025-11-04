#!/bin/bash

echo "🚀 Monitoring v9.7 deployment..."
echo "================================"

for i in {1..20}; do
    VERSION=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('version', 'error'))" 2>/dev/null || echo "offline")
    echo "$(date +%H:%M:%S) - Version: $VERSION"
    
    if [ "$VERSION" = "9.7" ]; then
        echo ""
        echo "✅ v9.7 DEPLOYED!"
        echo ""
        echo "Testing all endpoints..."
        python3 TEST_V97_COMPLETE.py
        exit 0
    fi
    
    sleep 15
done

echo ""
echo "⏱️ Timeout. v9.7 not deployed yet."
echo "Current version: $VERSION"