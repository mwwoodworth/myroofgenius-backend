#!/bin/bash
# Script to build and push the base Docker image for faster subsequent builds

echo "🐳 Building BrainOps Backend Base Image..."
echo "========================================="

# Login to Docker Hub
echo "📦 Logging into Docker Hub..."
export DOCKER_CONFIG=/tmp/.docker
mkdir -p $DOCKER_CONFIG
echo '{"auths":{"https://index.docker.io/v1/":{"auth":"'$(echo -n "mwwoodworth:dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho" | base64)'"}}}' > $DOCKER_CONFIG/config.json

cd /home/mwwoodworth/code/fastapi-operator-env

# Build the base image
echo "🔨 Building base image with all dependencies..."
DOCKER_CONFIG=/tmp/.docker docker build -t mwwoodworth/brainops-backend:base -f Dockerfile.base . --no-cache

if [ $? -eq 0 ]; then
    echo "✅ Base image built successfully"
    
    # Push to Docker Hub
    echo "📤 Pushing base image to Docker Hub..."
    DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:base
    
    if [ $? -eq 0 ]; then
        echo "✅ Base image pushed successfully"
        echo ""
        echo "🎯 NEXT STEPS:"
        echo "1. Update Dockerfile to use: FROM mwwoodworth/brainops-backend:base"
        echo "2. Future builds will be much faster!"
        echo ""
        echo "Example optimized Dockerfile:"
        echo "----------------------------"
        echo "FROM mwwoodworth/brainops-backend:base"
        echo "WORKDIR /app"
        echo "COPY . ."
        echo "ENV PYTHONPATH=/app"
        echo "EXPOSE 10000"
        echo 'CMD ["python", "-m", "uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "10000"]'
    else
        echo "❌ Failed to push base image"
        exit 1
    fi
else
    echo "❌ Failed to build base image"
    exit 1
fi

echo ""
echo "✨ Base image creation complete!"