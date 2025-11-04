#!/bin/bash

echo "🚨 EMERGENCY RENDER DEPLOYMENT STOP"
echo "===================================="
echo ""

# First, get ALL deployments in any active state
echo "📋 Finding all active/pending deployments..."
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

echo "Found deployments to cancel:"
echo "$ACTIVE_DEPLOYS"
echo ""

# Cancel each one
for DEPLOY_ID in $ACTIVE_DEPLOYS; do
    echo "❌ Canceling deployment: $DEPLOY_ID"
    curl -X POST \
      -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
      "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys/$DEPLOY_ID/cancel" \
      -s -o /dev/null
    sleep 0.5
done

echo ""
echo "🔧 Disabling auto-deploy completely..."

# Disable auto-deploy at service level
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

echo "✅ Auto-deploy disabled"
echo ""

# Suspend the service temporarily to break the loop
echo "⏸️  Suspending service temporarily to break the loop..."
curl -X POST \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/suspend" \
  -s -o /dev/null

sleep 5

echo "▶️  Resuming service..."
curl -X POST \
  -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/resume" \
  -s -o /dev/null

echo ""
echo "📊 Final Status Check:"
curl -s -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
  "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Service: {data.get('name')}\")
print(f\"Status: {data.get('suspended')}\")
print(f\"Auto-deploy: {data.get('autoDeploy')}\")
"

echo ""
echo "✅ EMERGENCY STOP COMPLETE"
echo ""
echo "The deployment loop should now be stopped."
echo "Wait 30 seconds before attempting any new deployments."
echo ""
echo "To deploy manually later, use:"
echo "  curl -X POST https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"