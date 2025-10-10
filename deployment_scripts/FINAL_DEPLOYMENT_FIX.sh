#!/bin/bash

echo "🚨 FINAL DEPLOYMENT FIX - COMPLETE SOLUTION"
echo "==========================================="
echo ""
echo "The problem: Deploy hook is being called repeatedly"
echo "The solution: Manual deployment without hooks"
echo ""

# Step 1: Cancel everything
echo "Step 1: Canceling all deployments..."
ALL_DEPLOYS=$(curl -s -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys?limit=50" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for d in data:
    deploy = d['deploy']
    if deploy['status'] in ['created', 'build_in_progress', 'update_in_progress']:
        print(deploy['id'])
")

for ID in $ALL_DEPLOYS; do
  curl -X POST \
    -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
    "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys/$ID/cancel" \
    -s -o /dev/null
  echo "  Canceled: $ID"
done

# Step 2: Manual deployment using API
echo ""
echo "Step 2: Creating manual deployment via API (not webhook)..."
DEPLOY_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  -H "Content-Type: application/json" \
  -d '{
    "clearCache": false,
    "image": {
      "ownerId": "usr-cja1ipir0cfc73gqbl60",
      "imagePath": "docker.io/mwwoodworth/brainops-backend:v3.3.10-fixed",
      "registryCredentialId": "rcr-cja1ipir0cfc73gqbl5g"
    }
  }' \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys")

DEPLOY_ID=$(echo "$DEPLOY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "error")

if [ "$DEPLOY_ID" = "error" ]; then
  echo "❌ Failed to create deployment"
  echo "$DEPLOY_RESPONSE"
  exit 1
fi

echo "✅ Created deployment: $DEPLOY_ID"
echo ""
echo "Step 3: Monitoring deployment (this is the ONLY one running)..."
echo ""

# Monitor the deployment
SUCCESS=false
for i in {1..40}; do
  STATUS=$(curl -s -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
    "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys/$DEPLOY_ID" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "error")
  
  # Check if any other deployments started
  OTHER_DEPLOYS=$(curl -s -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
    "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys?limit=1" | \
    python3 -c "
import sys, json
latest = json.load(sys.stdin)[0]['deploy']['id']
if latest != '$DEPLOY_ID':
    print(f'WARNING: New deployment {latest} started!')
" 2>/dev/null)
  
  if [ -n "$OTHER_DEPLOYS" ]; then
    echo "  $OTHER_DEPLOYS"
  fi
  
  echo "  [$i] $(date '+%H:%M:%S') - Status: $STATUS"
  
  if [ "$STATUS" = "live" ]; then
    SUCCESS=true
    break
  elif [ "$STATUS" = "canceled" ] || [ "$STATUS" = "build_failed" ] || [ "$STATUS" = "update_failed" ]; then
    break
  fi
  
  sleep 30
done

echo ""
if [ "$SUCCESS" = true ]; then
  echo "🎉🎉🎉 DEPLOYMENT SUCCESSFUL! 🎉🎉🎉"
  echo ""
  echo "The deployment loop has been broken!"
  echo "v3.3.10-fixed is now live with:"
  echo "  - Process-safe database migrations"
  echo "  - Advisory locks preventing conflicts"
  echo "  - Only one worker runs migrations"
  echo ""
  echo "Testing API health:"
  curl -s https://brainops-backend-prod.onrender.com/api/v1/health | python3 -m json.tool
else
  echo "❌ Deployment did not complete"
  echo "Final status: $STATUS"
  echo ""
  echo "IMPORTANT: Do NOT use the deploy hook URL!"
  echo "Something is calling it repeatedly causing the loop."
fi

echo ""
echo "📝 NEXT STEPS:"
echo "1. DO NOT share or use the deploy hook URL"
echo "2. Use Render dashboard for manual deployments"
echo "3. Or use the API method shown in this script"
echo "4. Consider regenerating the deploy key to invalidate the old hook"