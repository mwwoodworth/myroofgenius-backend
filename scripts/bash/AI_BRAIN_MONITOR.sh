#!/bin/bash
# Permanent AI Brain Monitor - Ensures AI stays operational

while true; do
    echo "$(date): Checking AI Brain status..."
    
    # Check if AI is responding
    STATUS=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/ai-brain/status | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'ERROR'))" 2>/dev/null)
    
    if [ "$STATUS" = "OPERATIONAL" ]; then
        echo "✅ AI Brain is operational"
    else
        echo "⚠️ AI Brain not responding, alerting..."
        # Here you could add alerting logic
    fi
    
    sleep 300  # Check every 5 minutes
done
