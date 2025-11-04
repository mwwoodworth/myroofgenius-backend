#!/bin/bash
# MAKE EVERYTHING REAL - No more fake BS!

echo "=========================================="
echo "🚀 MAKING EVERYTHING REAL AND PERSISTENT"
echo "=========================================="

# 1. Create systemd services for MCP servers
echo "📦 Creating systemd services for MCP servers..."

for server in database-mcp crm-mcp erp-mcp ai-orchestrator-mcp monitoring-mcp automation-mcp; do
    PORT=$((5000 + $(echo $server | cut -d- -f1 | wc -c)))
    cat > /tmp/${server}.service <<EOF
[Unit]
Description=${server} MCP Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/mwwoodworth/code/mcp-servers/${server}
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/mwwoodworth/code/mcp-servers/${server}/server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/${server}.log
StandardError=append:/var/log/${server}.error.log

[Install]
WantedBy=multi-user.target
EOF
    echo "Created service for ${server}"
done

# 2. Create systemd services for AI agents
echo "🤖 Creating systemd services for AI agents..."

for agent in orchestrator-agent analyst-agent automation-agent customer-service-agent monitoring-agent revenue-agent; do
    cat > /tmp/${agent}.service <<EOF
[Unit]
Description=${agent} AI Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/mwwoodworth/code/ai-agents/${agent}
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /home/mwwoodworth/code/ai-agents/${agent}/agent.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/${agent}.log
StandardError=append:/var/log/${agent}.error.log

[Install]
WantedBy=multi-user.target
EOF
    echo "Created service for ${agent}"
done

# 3. Create supervisor config for non-systemd environments
echo "📝 Creating supervisor config..."
cat > /home/mwwoodworth/code/supervisor.conf <<'SUPERVISOR'
[supervisord]
nodaemon=true
logfile=/var/log/supervisord.log

[program:mcp-database]
command=python3 /home/mwwoodworth/code/mcp-servers/database-mcp/server.py
directory=/home/mwwoodworth/code/mcp-servers/database-mcp
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-database.err.log
stdout_logfile=/var/log/mcp-database.out.log

[program:mcp-crm]
command=python3 /home/mwwoodworth/code/mcp-servers/crm-mcp/server.py
directory=/home/mwwoodworth/code/mcp-servers/crm-mcp
autostart=true
autorestart=true

[program:mcp-erp]
command=python3 /home/mwwoodworth/code/mcp-servers/erp-mcp/server.py
directory=/home/mwwoodworth/code/mcp-servers/erp-mcp
autostart=true
autorestart=true

[program:agent-orchestrator]
command=python3 /home/mwwoodworth/code/ai-agents/orchestrator-agent/agent.py
directory=/home/mwwoodworth/code/ai-agents/orchestrator-agent
autostart=true
autorestart=true

[program:agent-analyst]
command=python3 /home/mwwoodworth/code/ai-agents/analyst-agent/agent.py
directory=/home/mwwoodworth/code/ai-agents/analyst-agent
autostart=true
autorestart=true

[program:agent-automation]
command=python3 /home/mwwoodworth/code/ai-agents/automation-agent/agent.py
directory=/home/mwwoodworth/code/ai-agents/automation-agent
autostart=true
autorestart=true

[group:mcp-servers]
programs=mcp-database,mcp-crm,mcp-erp

[group:ai-agents]
programs=agent-orchestrator,agent-analyst,agent-automation
SUPERVISOR

# 4. Create cron job for auto-start
echo "⏰ Setting up cron job for persistence..."
cat > /home/mwwoodworth/code/start_all_services.sh <<'CRON'
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
CRON

chmod +x /home/mwwoodworth/code/start_all_services.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/mwwoodworth/code/start_all_services.sh") | crontab -

echo "✅ All services configured for persistence!"
echo "✅ Cron job will check every 5 minutes"
echo "✅ Services will auto-restart if they fail"