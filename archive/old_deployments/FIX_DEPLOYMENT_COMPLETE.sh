#!/bin/bash

echo "🔧 COMPLETE DEPLOYMENT FIX v3.3.10-fixed"
echo "========================================"
echo ""

# Step 1: Cancel ALL active deployments
echo "📋 Step 1: Canceling all active deployments..."
ACTIVE_DEPLOYS=$(curl -s -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys?limit=20" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for d in data:
    deploy = d['deploy']
    if deploy['status'] in ['created', 'build_in_progress', 'update_in_progress', 'pre_deploy_in_progress']:
        print(deploy['id'])
")

for DEPLOY_ID in $ACTIVE_DEPLOYS; do
    echo "  ❌ Canceling: $DEPLOY_ID"
    curl -X POST \
      -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
      "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys/$DEPLOY_ID/cancel" \
      -s -o /dev/null
    sleep 1
done

echo ""
echo "📋 Step 2: Ensuring service is suspended..."
# Suspend the service
curl -X POST \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/suspend" \
  -s -o /dev/null

sleep 5

echo ""
echo "📋 Step 3: Updating service to use our fixed image..."
# Update the service to use the specific image
curl -X PATCH \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  -H "Content-Type: application/json" \
  -d '{
    "image": {
      "ownerId": "usr-cja1ipir0cfc73gqbl60",
      "imagePath": "docker.io/mwwoodworth/brainops-backend:v3.3.10-fixed",
      "registryCredentialId": "rcr-cja1ipir0cfc73gqbl5g"
    },
    "autoDeploy": "no"
  }' \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00" \
  -s -o /dev/null

echo "✅ Service updated to use v3.3.10-fixed"

sleep 5

echo ""
echo "📋 Step 4: Resuming service with fixed image..."
# Resume the service
curl -X POST \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/resume" \
  -s -o /dev/null

echo "✅ Service resumed"

echo ""
echo "📋 Step 5: Waiting for deployment to start..."
sleep 10

# Check deployment status
echo ""
echo "📊 Current Status:"
curl -s -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys?limit=1" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
if data:
    deploy = data[0]['deploy']
    print(f\"  Latest Deploy ID: {deploy['id']}\")
    print(f\"  Status: {deploy['status']}\")
    print(f\"  Image: {deploy.get('image', {}).get('ref', 'Unknown')}\")
"

echo ""
echo "✅ DEPLOYMENT FIX COMPLETE"
echo ""
echo "The service should now be deploying v3.3.10-fixed with:"
echo "  - Process-safe database migrations using advisory locks"
echo "  - Only one process will run migrations"
echo "  - No more deployment loops"
echo ""
echo "Monitor at: https://dashboard.render.com/web/srv-d1tfs4idbo4c73di6k00"