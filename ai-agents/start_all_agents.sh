#!/bin/bash
# Start all AI agents

echo "Starting AI agents..."


echo "Starting orchestrator-agent..."
cd /home/mwwoodworth/code/ai-agents/orchestrator-agent
nohup python3 agent.py > orchestrator-agent.log 2>&1 &
echo $! > orchestrator-agent.pid

echo "Starting analyst-agent..."
cd /home/mwwoodworth/code/ai-agents/analyst-agent
nohup python3 agent.py > analyst-agent.log 2>&1 &
echo $! > analyst-agent.pid

echo "Starting automation-agent..."
cd /home/mwwoodworth/code/ai-agents/automation-agent
nohup python3 agent.py > automation-agent.log 2>&1 &
echo $! > automation-agent.pid

echo "Starting customer-service-agent..."
cd /home/mwwoodworth/code/ai-agents/customer-service-agent
nohup python3 agent.py > customer-service-agent.log 2>&1 &
echo $! > customer-service-agent.pid

echo "Starting monitoring-agent..."
cd /home/mwwoodworth/code/ai-agents/monitoring-agent
nohup python3 agent.py > monitoring-agent.log 2>&1 &
echo $! > monitoring-agent.pid

echo "Starting revenue-agent..."
cd /home/mwwoodworth/code/ai-agents/revenue-agent
nohup python3 agent.py > revenue-agent.log 2>&1 &
echo $! > revenue-agent.pid

echo "All AI agents started!"
echo "Check logs in /home/mwwoodworth/code/ai-agents/*/
echo "Monitor with: ps aux | grep agent
