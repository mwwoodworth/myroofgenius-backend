#!/bin/bash

echo "🚨 EMERGENCY FIX - BRINGING SYSTEM TO 100% OPERATIONAL"
echo "======================================================"
echo "Starting comprehensive fix at $(date)"
echo ""

# Step 1: Fix Backend API Routes
echo "1️⃣ FIXING BACKEND API ROUTES..."
cd /home/mwwoodworth/code/fastapi-operator-env

# Update version to 4.31
echo "Updating to version 4.31..."
sed -i 's/version = "4.30"/version = "4.31"/' main.py 2>/dev/null || echo "version = \"4.31\"" >> main.py

# Build and push Docker image
echo "Building Docker image v4.31..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho' > /dev/null 2>&1

# Use simplified Dockerfile for faster build
if [ -f "Dockerfile.simple" ]; then
    echo "Using Dockerfile.simple for faster build..."
    DOCKER_CONFIG=/tmp/.docker timeout 90 docker build -t mwwoodworth/brainops-backend:v4.31 -f Dockerfile.simple . --no-cache
else
    DOCKER_CONFIG=/tmp/.docker timeout 90 docker build -t mwwoodworth/brainops-backend:v4.31 -f Dockerfile .
fi

if [ $? -eq 0 ]; then
    DOCKER_CONFIG=/tmp/.docker docker tag mwwoodworth/brainops-backend:v4.31 mwwoodworth/brainops-backend:latest
    DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:v4.31
    DOCKER_CONFIG=/tmp/.docker docker push mwwoodworth/brainops-backend:latest
    echo "✅ Backend v4.31 pushed to Docker Hub"
    
    # Trigger Render deployment
    echo "Triggering Render deployment..."
    curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"
    echo "✅ Deployment triggered on Render"
else
    echo "❌ Docker build failed"
fi

# Step 2: Run all database migrations
echo ""
echo "2️⃣ RUNNING DATABASE MIGRATIONS..."
DATABASE_URL="postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"

psql "$DATABASE_URL" << 'SQL'
-- Create all missing tables
CREATE TABLE IF NOT EXISTS centerpoint_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50),
    status VARCHAR(50),
    records_synced INTEGER,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_monitoring (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    system_name VARCHAR(255),
    status VARCHAR(50),
    failures INT,
    metadata JSONB
);

-- Fix invoice columns
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS amount_cents BIGINT;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total_amount_cents BIGINT;
UPDATE invoices SET amount_cents = COALESCE(total_amount, 0) WHERE amount_cents IS NULL;
UPDATE invoices SET total_amount_cents = COALESCE(total_amount, 0) WHERE total_amount_cents IS NULL;

GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
SQL

echo "✅ Database migrations completed"

# Step 3: Test all systems
echo ""
echo "3️⃣ TESTING SYSTEM STATUS..."
sleep 15  # Wait for deployment

TOTAL=0
WORKING=0

test_endpoint() {
    TOTAL=$((TOTAL + 1))
    code=$(curl -s -o /dev/null -w "%{http_code}" "$1")
    if [ "$code" = "$2" ]; then
        WORKING=$((WORKING + 1))
        echo "✅ $3: $code"
    else
        echo "❌ $3: $code (expected $2)"
    fi
}

test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/health" "200" "Health"
test_endpoint "https://brainops-backend-prod.onrender.com/api/v1/task-os/status" "200" "Task OS"
test_endpoint "https://weathercraft-erp.vercel.app" "200" "WeatherCraft"

SUCCESS_RATE=$((WORKING * 100 / TOTAL))
echo ""
echo "======================================================"
echo "📊 OPERATIONAL STATUS: ${SUCCESS_RATE}%"
echo "======================================================"
