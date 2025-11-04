#!/bin/bash
# Start all services if not running

# Check and start MCP servers
for port in 5001 5002 5003 5004 5005 5006; do
    if ! ss -tulpn 2>/dev/null | grep -q ":$port"; then
        case $port in
            5001) cd /home/mwwoodworth/code/mcp-servers/database-mcp && nohup python3 server.py > /dev/null 2>&1 & ;;
            5002) cd /home/mwwoodworth/code/mcp-servers/crm-mcp && nohup python3 server.py > /dev/null 2>&1 & ;;
            5003) cd /home/mwwoodworth/code/mcp-servers/erp-mcp && nohup python3 server.py > /dev/null 2>&1 & ;;
            5004) cd /home/mwwoodworth/code/mcp-servers/ai-orchestrator-mcp && nohup python3 server.py > /dev/null 2>&1 & ;;
            5005) cd /home/mwwoodworth/code/mcp-servers/monitoring-mcp && nohup python3 server.py > /dev/null 2>&1 & ;;
            5006) cd /home/mwwoodworth/code/mcp-servers/automation-mcp && nohup python3 server.py > /dev/null 2>&1 & ;;
        esac
    fi
done

# Check and start AI agents
for port in 6001 6002 6003 6004 6005 6006; do
    if ! ss -tulpn 2>/dev/null | grep -q ":$port"; then
        case $port in
            6001) cd /home/mwwoodworth/code/ai-agents/orchestrator-agent && nohup python3 agent.py > /dev/null 2>&1 & ;;
            6002) cd /home/mwwoodworth/code/ai-agents/analyst-agent && nohup python3 agent.py > /dev/null 2>&1 & ;;
            6003) cd /home/mwwoodworth/code/ai-agents/automation-agent && nohup python3 agent.py > /dev/null 2>&1 & ;;
            6004) cd /home/mwwoodworth/code/ai-agents/customer-service-agent && nohup python3 agent.py > /dev/null 2>&1 & ;;
            6005) cd /home/mwwoodworth/code/ai-agents/monitoring-agent && nohup python3 agent.py > /dev/null 2>&1 & ;;
            6006) cd /home/mwwoodworth/code/ai-agents/revenue-agent && nohup python3 agent.py > /dev/null 2>&1 & ;;
        esac
    fi
done
