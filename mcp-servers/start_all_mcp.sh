#!/bin/bash
# Start all MCP servers

echo "Starting MCP servers..."


echo "Starting database-mcp..."
cd /home/mwwoodworth/code/mcp-servers/database-mcp
nohup python3 server.py > database-mcp.log 2>&1 &
echo $! > database-mcp.pid

echo "Starting crm-mcp..."
cd /home/mwwoodworth/code/mcp-servers/crm-mcp
nohup python3 server.py > crm-mcp.log 2>&1 &
echo $! > crm-mcp.pid

echo "Starting erp-mcp..."
cd /home/mwwoodworth/code/mcp-servers/erp-mcp
nohup python3 server.py > erp-mcp.log 2>&1 &
echo $! > erp-mcp.pid

echo "Starting ai-orchestrator-mcp..."
cd /home/mwwoodworth/code/mcp-servers/ai-orchestrator-mcp
nohup python3 server.py > ai-orchestrator-mcp.log 2>&1 &
echo $! > ai-orchestrator-mcp.pid

echo "Starting monitoring-mcp..."
cd /home/mwwoodworth/code/mcp-servers/monitoring-mcp
nohup python3 server.py > monitoring-mcp.log 2>&1 &
echo $! > monitoring-mcp.pid

echo "Starting automation-mcp..."
cd /home/mwwoodworth/code/mcp-servers/automation-mcp
nohup python3 server.py > automation-mcp.log 2>&1 &
echo $! > automation-mcp.pid

echo "All MCP servers started!"
echo "Check logs in /home/mwwoodworth/code/mcp-servers/*/
