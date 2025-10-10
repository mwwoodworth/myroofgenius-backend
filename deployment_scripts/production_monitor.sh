#!/bin/bash
# Production Monitoring Script v3.3.56

while true; do
    echo "🔍 Checking production systems at $(date)"
    
    # Check backend
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://brainops-backend-prod.onrender.com/api/v1/health)
    if [ "$BACKEND_STATUS" = "200" ]; then
        echo "✅ Backend: Operational"
    else
        echo "❌ Backend: Error (HTTP $BACKEND_STATUS)"
        # Alert mechanism here
    fi
    
    # Check WeatherCraft
    WEATHERCRAFT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://weathercraft-erp.vercel.app)
    if [ "$WEATHERCRAFT_STATUS" = "200" ]; then
        echo "✅ WeatherCraft: Operational"
    else
        echo "⚠️  WeatherCraft: HTTP $WEATHERCRAFT_STATUS"
    fi
    
    # Check MyRoofGenius
    MRG_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://myroofgenius.com)
    if [ "$MRG_STATUS" = "200" ]; then
        echo "✅ MyRoofGenius: Operational"
    else
        echo "⚠️  MyRoofGenius: HTTP $MRG_STATUS"
    fi
    
    echo "---"
    sleep 300  # Check every 5 minutes
done
