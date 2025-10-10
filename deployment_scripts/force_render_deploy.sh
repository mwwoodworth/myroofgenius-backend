#!/bin/bash
# Force Render deployment

echo "Attempting to force Render deployment..."
echo ""
echo "MANUAL STEPS REQUIRED:"
echo "1. Go to https://dashboard.render.com"
echo "2. Find the 'brainops-backend' service"
echo "3. Click 'Manual Deploy' button"
echo "4. Or update the service to use Docker image: mwwoodworth/brainops-backend:latest"
echo ""
echo "Alternative: Deploy using Render CLI"
echo "$ render deploy --service brainops-backend"
echo ""
echo "If service doesn't exist, create new Docker web service:"
echo "- Image URL: mwwoodworth/brainops-backend:latest"
echo "- Health Check Path: /health"
echo "- Port: 8000"
echo ""

# Try to use render CLI if available
if command -v render &> /dev/null; then
    echo "Render CLI detected. Attempting deployment..."
    render deploy --service brainops-backend
else
    echo "Render CLI not found. Please deploy manually via dashboard."
fi