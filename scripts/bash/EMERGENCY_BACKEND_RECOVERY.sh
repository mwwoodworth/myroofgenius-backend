#!/bin/bash
echo "🚨 EMERGENCY BACKEND RECOVERY"
echo "============================"

# Get latest version
cd /home/mwwoodworth/code/fastapi-operator-env
VERSION=$(grep 'version = ' main.py | cut -d'"' -f2)
echo "Current version: $VERSION"

# Increment patch version
NEW_VERSION="${VERSION%.*}.$((${VERSION##*.} + 1))"
echo "New version: $NEW_VERSION"

# Update version in files
sed -i "s/version = \"$VERSION\"/version = \"$NEW_VERSION\"/" main.py
sed -i "s/\"version\": \"$VERSION\"/\"version\": \"$NEW_VERSION\"/" routes/api_health.py

# Build and push Docker
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'
docker build -t mwwoodworth/brainops-backend:v$NEW_VERSION -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v$NEW_VERSION mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v$NEW_VERSION
docker push mwwoodworth/brainops-backend:latest

echo "✅ Recovery deployment v$NEW_VERSION pushed"
echo "📌 Manual deployment required on Render"
