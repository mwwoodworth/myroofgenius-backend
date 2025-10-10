#!/bin/bash
# Monitor deployment status

echo "Monitoring deployment status..."
echo "Checking every 30 seconds..."
echo ""

while true; do
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Check backend
    backend_status=$(curl -s -w "%{http_code}" -o /dev/null https://brainops-backend.onrender.com/health)
    
    if [ "$backend_status" = "200" ]; then
        echo "[$timestamp] ✅ BACKEND IS UP! (Status: $backend_status)"
        curl -s https://brainops-backend.onrender.com/health | python3 -m json.tool
        break
    else
        echo "[$timestamp] ⏳ Backend not ready (Status: $backend_status)"
    fi
    
    sleep 30
done

echo ""
echo "Deployment successful! Backend is operational."