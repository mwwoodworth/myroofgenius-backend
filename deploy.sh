#!/usr/bin/env bash
# BrainOps Backend (Render) - Docker image deploy
#
# This service is deployed to Render from a Docker Hub image:
#   docker.io/mwwoodworth/brainops-backend:latest
#
# Safety:
# - Requires RENDER_API_KEY in env (do not hardcode).
# - Does not print secrets.
# - Verifies deploy by comparing /health version before/after.

set -euo pipefail

SERVICE_ID="srv-d1tfs4idbo4c73di6k00"
HEALTH_URL="https://brainops-backend-prod.onrender.com/health"
IMAGE_REPO="mwwoodworth/brainops-backend"

if [ -z "${RENDER_API_KEY:-}" ]; then
  echo "ERROR: RENDER_API_KEY not set. Source scripts/brainops-env.sh first." >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required" >&2
  exit 1
fi

VERSION="$(
  python3 -c "from version import __version__; print(__version__)" 2>/dev/null | tr -d '[:space:]'
)"
if [ -z "${VERSION:-}" ]; then
  echo "ERROR: Unable to determine version from version.py" >&2
  exit 1
fi

echo "=========================================="
echo "Deploying BrainOps Backend v$VERSION"
echo "=========================================="

PRE_HEALTH="$(curl -s "$HEALTH_URL" 2>/dev/null || true)"
PRE_VERSION="$(echo "$PRE_HEALTH" | jq -r '.version // empty' 2>/dev/null | tr -d '[:space:]' || true)"
echo "Pre-deploy version: ${PRE_VERSION:-unknown}"

echo ""
echo "Step 1: Build Docker image..."
docker build -t "${IMAGE_REPO}:latest" -t "${IMAGE_REPO}:v${VERSION}" -f Dockerfile .

echo ""
echo "Step 2: Push to Docker Hub..."
docker push "${IMAGE_REPO}:latest"
docker push "${IMAGE_REPO}:v${VERSION}"

echo ""
echo "Step 3: Trigger Render deploy..."
DEPLOY_RESPONSE="$(
  curl -s -X POST "https://api.render.com/v1/services/${SERVICE_ID}/deploys" \
    -H "Authorization: Bearer ${RENDER_API_KEY}" \
    -H "Content-Type: application/json"
)"

DEPLOY_ID="$(echo "$DEPLOY_RESPONSE" | jq -r '.id // empty' 2>/dev/null || true)"
DEPLOY_STATUS="$(echo "$DEPLOY_RESPONSE" | jq -r '.status // empty' 2>/dev/null || true)"
if [ -z "${DEPLOY_ID:-}" ] || [ -z "${DEPLOY_STATUS:-}" ]; then
  echo "ERROR: Render deploy trigger returned unexpected response:" >&2
  echo "$DEPLOY_RESPONSE" | jq . 2>/dev/null || echo "$DEPLOY_RESPONSE" >&2
  exit 1
fi
echo "Deploy ID: $DEPLOY_ID"
echo "Deploy status: $DEPLOY_STATUS"

echo ""
echo "Step 4: Wait for Render deploy to go live..."
for i in {1..30}; do
  sleep 10
  STATUS_RESPONSE="$(curl -s "https://api.render.com/v1/services/${SERVICE_ID}/deploys/${DEPLOY_ID}" \
    -H "Authorization: Bearer ${RENDER_API_KEY}" \
    -H "Content-Type: application/json" || true)"
  LIVE_STATUS="$(echo "$STATUS_RESPONSE" | jq -r '.status // "unknown"' 2>/dev/null || echo unknown)"
  if [ "$LIVE_STATUS" = "live" ]; then
    break
  fi
  if [ "$LIVE_STATUS" = "failed" ] || [ "$LIVE_STATUS" = "build_failed" ] || [ "$LIVE_STATUS" = "canceled" ]; then
    echo "ERROR: Render deploy status: $LIVE_STATUS" >&2
    echo "$STATUS_RESPONSE" | jq . 2>/dev/null || echo "$STATUS_RESPONSE" >&2
    exit 1
  fi
  echo "  Render status: $LIVE_STATUS"
done

echo ""
echo "Step 5: Verify /health reflects new version..."
POST_VERSION=""
for j in {1..24}; do
  sleep 5
  HEALTH="$(curl -s "$HEALTH_URL" 2>/dev/null || true)"
  POST_VERSION="$(echo "$HEALTH" | jq -r '.version // empty' 2>/dev/null | tr -d '[:space:]' || true)"
  if [ -n "${POST_VERSION:-}" ] && [ "$POST_VERSION" != "${PRE_VERSION:-}" ]; then
    break
  fi
done

echo "Post-deploy version: ${POST_VERSION:-unknown}"
if [ "$POST_VERSION" = "$VERSION" ]; then
  echo "✅ SUCCESS: v$VERSION deployed"
else
  echo "⚠️  Could not confirm version changed to v$VERSION via /health" >&2
  echo "   Expected: $VERSION" >&2
  echo "   Current:  ${POST_VERSION:-unknown}" >&2
fi
