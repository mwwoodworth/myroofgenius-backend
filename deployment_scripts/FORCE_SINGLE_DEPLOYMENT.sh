#!/bin/bash

echo "🛑 FORCE SINGLE DEPLOYMENT - BREAKING THE LOOP"
echo "=============================================="
echo ""

# Step 1: Cancel ALL deployments
echo "Step 1: Canceling ALL active deployments..."
ACTIVE=$(curl -s -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys?limit=50" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
active = []
for d in data:
    deploy = d['deploy']
    if deploy['status'] in ['created', 'build_in_progress', 'update_in_progress', 'pre_deploy_in_progress']:
        active.append(deploy['id'])
print(' '.join(active))
")

for ID in $ACTIVE; do
  echo "  Canceling: $ID"
  curl -X POST \
    -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
    "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys/$ID/cancel" \
    -s -o /dev/null
done

# Step 2: Clear the service configuration
echo ""
echo "Step 2: Clearing service configuration..."
curl -X PATCH \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  -H "Content-Type: application/json" \
  -d '{
    "autoDeploy": "no",
    "branch": null,
    "repo": null
  }' \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00" \
  -s -o /dev/null

# Step 3: Suspend the service to break any loops
echo ""
echo "Step 3: Suspending service to break loops..."
curl -X POST \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/suspend" \
  -s -o /dev/null

echo "Waiting 10 seconds for suspension..."
sleep 10

# Step 4: Update to use specific version
echo ""
echo "Step 4: Setting specific Docker image version..."
curl -X PATCH \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  -H "Content-Type: application/json" \
  -d '{
    "image": {
      "ownerId": "usr-cja1ipir0cfc73gqbl60",
      "imagePath": "docker.io/mwwoodworth/brainops-backend:v3.3.10-fixed",
      "registryCredentialId": "rcr-cja1ipir0cfc73gqbl5g"
    }
  }' \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00" \
  -s -o /dev/null

# Step 5: Resume the service with the fixed image
echo ""
echo "Step 5: Resuming service with v3.3.10-fixed..."
curl -X POST \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/resume" \
  -s -o /dev/null

echo ""
echo "✅ Service resumed with v3.3.10-fixed"
echo ""
echo "Waiting 15 seconds for deployment to start..."
sleep 15

# Check the status
echo ""
echo "📊 Deployment Status:"
curl -s -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys?limit=1" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
if data:
    deploy = data[0]['deploy']
    print(f\"  Deploy ID: {deploy['id']}\")
    print(f\"  Status: {deploy['status']}\")
    print(f\"  Image: {deploy.get('image', {}).get('ref', 'Unknown')}\")
    print(f\"  Created: {deploy['createdAt']}\")
"

echo ""
echo "🎯 CRITICAL: Monitor this deployment closely!"
echo "If it gets canceled, something external is triggering deployments."
echo ""
echo "To manually deploy later if needed:"
echo "  curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"