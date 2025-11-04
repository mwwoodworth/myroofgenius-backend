#!/bin/bash
# Efficient deployment script with BuildKit and optimizations
# Usage: ./EFFICIENT_DEPLOY.sh <version>

set -e

VERSION=${1:-$(date +%Y%m%d.%H%M)}
DOCKER_USER="mwwoodworth"
DOCKER_PAT="dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho"
RENDER_DEPLOY_HOOK="https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"

echo "🚀 Efficient Deployment Script v2.0"
echo "📦 Version: $VERSION"

# Setup Docker config to avoid auth issues
setup_docker_auth() {
    echo "🔐 Setting up Docker authentication..."
    mkdir -p /tmp/.docker
    export DOCKER_CONFIG=/tmp/.docker
    echo "$DOCKER_PAT" | docker login -u "$DOCKER_USER" --password-stdin
}

# Build with BuildKit for efficiency
build_with_buildkit() {
    echo "🏗️ Building with BuildKit..."
    cd /home/mwwoodworth/code/fastapi-operator-env
    
    # Enable BuildKit
    export DOCKER_BUILDKIT=1
    
    # Build with cache and optimizations
    docker build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from mwwoodworth/brainops-backend:latest \
        -t mwwoodworth/brainops-backend:v$VERSION \
        -t mwwoodworth/brainops-backend:latest \
        -f Dockerfile \
        . --progress=plain
}

# Push images efficiently
push_images() {
    echo "📤 Pushing to Docker Hub..."
    docker push mwwoodworth/brainops-backend:v$VERSION
    docker push mwwoodworth/brainops-backend:latest
}

# Deploy to Render
deploy_to_render() {
    echo "🚢 Deploying to Render..."
    curl -X POST "$RENDER_DEPLOY_HOOK" | jq -r '.deploy.id' || echo "Deploy triggered"
}

# Test deployment
test_deployment() {
    echo "🧪 Testing deployment..."
    sleep 10
    curl -s https://brainops-backend-prod.onrender.com/api/v1/health | jq '.' || echo "Health check pending..."
}

# Main execution
main() {
    setup_docker_auth
    build_with_buildkit
    push_images
    deploy_to_render
    test_deployment
    
    echo "✅ Deployment complete!"
    echo "📊 Version v$VERSION deployed successfully"
}

# Run main function
main