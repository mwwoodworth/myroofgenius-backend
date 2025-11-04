#!/bin/bash
set -e

echo "🚨 EMERGENCY DEPLOYMENT v5.10 - FIXING BUILD ERROR"
echo "=================================================="

# 1. Ensure we have the latest code
cd /home/mwwoodworth/code/fastapi-operator-env

# 2. Create a simple working Dockerfile that directly uses main_v504.py
cat > Dockerfile.emergency << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    psycopg2-binary \
    pydantic \
    python-jose[cryptography] \
    passlib[bcrypt] \
    python-multipart \
    httpx \
    python-dotenv \
    stripe \
    google-generativeai \
    redis

# Copy application - main_v504.py IS our main.py
COPY main_v504.py /app/main.py
COPY routes /app/routes

# Environment
ENV PYTHONUNBUFFERED=1
ENV API_VERSION=5.10
ENV PORT=10000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:10000/api/v1/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
EOF

# 3. Build with specific tag
echo "🔨 Building Docker image v5.10..."
docker build -t mwwoodworth/brainops-backend:v5.10 -f Dockerfile.emergency . --no-cache

# 4. Test locally that app exists
echo "🧪 Testing Docker image..."
docker run --rm mwwoodworth/brainops-backend:v5.10 python3 -c "import main; assert hasattr(main, 'app'), 'App not found!'; print('✅ App found in main module')"

# 5. Tag as latest
docker tag mwwoodworth/brainops-backend:v5.10 mwwoodworth/brainops-backend:latest

# 6. Login to Docker Hub
echo "🔐 Logging into Docker Hub..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho' 2>/dev/null

# 7. Push to Docker Hub
echo "📤 Pushing to Docker Hub..."
docker push mwwoodworth/brainops-backend:v5.10
docker push mwwoodworth/brainops-backend:latest

# 8. Update the main Dockerfile to match the emergency one
cp Dockerfile.emergency Dockerfile

# 9. Commit and push
echo "📝 Committing changes..."
git add -A
git commit -m "emergency: Force v5.10 deployment with explicit main.py copy

- Directly copy main_v504.py as /app/main.py
- Only copy necessary routes directory
- Explicit port 10000 in CMD
- Verified app attribute exists before deployment

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

# 10. Trigger Render deployment with cache clear
echo "🚀 Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Content-Type: application/json" \
  -d '{"clear_cache": "clear"}'

echo ""
echo "✅ Emergency deployment v5.10 initiated!"
echo "Monitor at: https://dashboard.render.com/web/srv-d1tfs4idbo4c73di6k00"
echo ""
echo "Wait 2-3 minutes then test with:"
echo "curl https://brainops-backend-prod.onrender.com/api/v1/health"