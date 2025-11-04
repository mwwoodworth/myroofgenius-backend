#!/bin/sh

echo "🚀 Starting BrainOps MCP Gateway..."

# Set environment variables from config if not already set
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres}"
export MCP_CONFIG="${MCP_CONFIG:-/app/config.json}"
export NODE_ENV="${NODE_ENV:-production}"

# Start health check server in background
echo "🏥 Starting health monitoring..."
node /app/health-server.js &
HEALTH_PID=$!

# Wait for health server to start
sleep 2

# Start MCP gateway
echo "📡 Starting MCP Gateway on port 8080..."
node /app/mcp-gateway.js &
GATEWAY_PID=$!

# Monitor processes
while true; do
  # Check if gateway is still running
  if ! kill -0 $GATEWAY_PID 2>/dev/null; then
    echo "⚠️ MCP Gateway crashed, restarting..."
    node /app/mcp-gateway.js &
    GATEWAY_PID=$!
  fi
  
  # Check if health server is still running
  if ! kill -0 $HEALTH_PID 2>/dev/null; then
    echo "⚠️ Health server crashed, restarting..."
    node /app/health-server.js &
    HEALTH_PID=$!
  fi
  
  sleep 10
done