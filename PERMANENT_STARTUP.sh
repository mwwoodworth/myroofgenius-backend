#!/bin/bash

# BrainOps Permanent Startup Script
# This ensures all services are running regardless of how the system starts

echo "🚀 BrainOps Permanent Startup Sequence Initiated"
echo "================================================"
echo "Time: $(date)"

# Set environment variables
export DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
export DOCKER_PAT="dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho"

# Function to check if service is running
check_service() {
    local port=$1
    local name=$2
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $name running on port $port"
        return 0
    else
        echo "❌ $name not running on port $port - Starting..."
        return 1
    fi
}

# Kill any existing services to ensure clean start
echo ""
echo "📋 Cleaning up old processes..."
pkill -f "start_mcp_" 2>/dev/null
pkill -f "start_agent_" 2>/dev/null
sleep 2

# Start MCP servers
echo ""
echo "🔧 Starting MCP Servers..."
for i in {1..6}; do
    port=$((5000 + i))
    name=""
    case $i in
        1) name="MCP Database" ;;
        2) name="MCP CRM" ;;
        3) name="MCP ERP" ;;
        4) name="MCP AI Orchestrator" ;;
        5) name="MCP Monitoring" ;;
        6) name="MCP Automation" ;;
    esac
    
    if ! check_service $port "$name"; then
        nohup python3 /home/mwwoodworth/code/start_mcp_${i}.py > /tmp/mcp_${i}.log 2>&1 &
        echo "Started $name with PID $!"
    fi
done

# Start AI agents
echo ""
echo "🤖 Starting AI Agents..."
for i in {1..6}; do
    port=$((6000 + i))
    name=""
    case $i in
        1) name="Agent Orchestrator" ;;
        2) name="Agent Analyst" ;;
        3) name="Agent Automation" ;;
        4) name="Agent Customer" ;;
        5) name="Agent Monitoring" ;;
        6) name="Agent Revenue" ;;
    esac
    
    if ! check_service $port "$name"; then
        nohup python3 /home/mwwoodworth/code/start_agent_${i}.py > /tmp/agent_${i}.log 2>&1 &
        echo "Started $name with PID $!"
    fi
done

# Wait for services to start
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 5

# Verify all services
echo ""
echo "🔍 Verifying all services..."
all_running=true

for i in {1..6}; do
    port=$((5000 + i))
    if ! nc -z localhost $port 2>/dev/null; then
        echo "❌ MCP service on port $port failed to start"
        all_running=false
    fi
done

for i in {1..6}; do
    port=$((6000 + i))
    if ! nc -z localhost $port 2>/dev/null; then
        echo "❌ AI agent on port $port failed to start"
        all_running=false
    fi
done

if $all_running; then
    echo ""
    echo "✅ ALL SERVICES RUNNING SUCCESSFULLY!"
else
    echo ""
    echo "⚠️ Some services failed to start. Check logs in /tmp/"
fi

# Test backend API
echo ""
echo "🌐 Testing Backend API..."
if curl -s https://brainops-backend-prod.onrender.com/api/v1/health > /dev/null; then
    echo "✅ Backend API is operational"
else
    echo "❌ Backend API is not responding"
fi

# Save startup status
echo ""
echo "📝 Saving startup status..."
cat > /home/mwwoodworth/code/LAST_STARTUP.txt << EOF
Last Startup: $(date)
MCP Services: $(pgrep -f "start_mcp_" | wc -l)/6
AI Agents: $(pgrep -f "start_agent_" | wc -l)/6
Backend Status: $(curl -s https://brainops-backend-prod.onrender.com/api/v1/health | grep -q "healthy" && echo "ONLINE" || echo "OFFLINE")
EOF

echo ""
echo "================================================"
echo "🎯 BrainOps Startup Complete!"
echo "================================================"