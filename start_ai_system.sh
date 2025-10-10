#!/bin/bash
# AI OS System Startup Script
# This ensures all AI components are running

echo "🚀 Starting AI Operating System..."
echo "=================================="

# Change to the correct directory
cd /home/matt-woodworth/fastapi-operator-env

# Activate virtual environment
source venv/bin/activate

# Kill any existing agents
pkill -f "start_all_agents" 2>/dev/null

# Start the AI orchestration system
echo "Starting AI Agents..."
nohup python3 ai_orchestration/start_all_agents.py > /var/log/ai_agents.log 2>&1 &
AGENT_PID=$!

echo "✅ AI Agents started (PID: $AGENT_PID)"

# Check status after 5 seconds
sleep 5
python3 ai_orchestration/start_all_agents.py status

echo ""
echo "=================================="
echo "🎉 AI OS System Started Successfully!"
echo ""
echo "Monitor logs: tail -f /var/log/ai_agents.log"
echo "Check status: python3 ai_orchestration/start_all_agents.py status"
echo ""