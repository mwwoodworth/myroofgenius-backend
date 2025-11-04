#!/bin/bash

echo "🚀 Creating systemd services for all MCP and AI services..."

# Create systemd service files for MCP servers
for i in {1..6}; do
    SERVICE_NAME=""
    case $i in
        1) SERVICE_NAME="mcp-database" ;;
        2) SERVICE_NAME="mcp-crm" ;;
        3) SERVICE_NAME="mcp-erp" ;;
        4) SERVICE_NAME="mcp-ai-orchestrator" ;;
        5) SERVICE_NAME="mcp-monitoring" ;;
        6) SERVICE_NAME="mcp-automation" ;;
    esac
    
    PORT=$((5000 + $i))
    
    cat > /tmp/${SERVICE_NAME}.service << EOF
[Unit]
Description=BrainOps ${SERVICE_NAME} Server
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=$USER
WorkingDirectory=/home/mwwoodworth/code
ExecStart=/usr/bin/python3 /home/mwwoodworth/code/start_mcp_${i}.py
StandardOutput=journal
StandardError=journal
Environment="PORT=${PORT}"

[Install]
WantedBy=multi-user.target
EOF
    
    echo "Created /tmp/${SERVICE_NAME}.service"
done

# Create systemd service files for AI agents
for i in {1..6}; do
    SERVICE_NAME=""
    case $i in
        1) SERVICE_NAME="ai-agent-orchestrator" ;;
        2) SERVICE_NAME="ai-agent-analyst" ;;
        3) SERVICE_NAME="ai-agent-automation" ;;
        4) SERVICE_NAME="ai-agent-customer" ;;
        5) SERVICE_NAME="ai-agent-monitoring" ;;
        6) SERVICE_NAME="ai-agent-revenue" ;;
    esac
    
    PORT=$((6000 + $i))
    
    cat > /tmp/${SERVICE_NAME}.service << EOF
[Unit]
Description=BrainOps ${SERVICE_NAME}
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=$USER
WorkingDirectory=/home/mwwoodworth/code
ExecStart=/usr/bin/python3 /home/mwwoodworth/code/start_agent_${i}.py
StandardOutput=journal
StandardError=journal
Environment="PORT=${PORT}"

[Install]
WantedBy=multi-user.target
EOF
    
    echo "Created /tmp/${SERVICE_NAME}.service"
done

# Create master control service
cat > /tmp/brainops-master.service << 'EOF'
[Unit]
Description=BrainOps Master Control Service
After=network.target
Wants=mcp-database.service mcp-crm.service mcp-erp.service mcp-ai-orchestrator.service mcp-monitoring.service mcp-automation.service
Wants=ai-agent-orchestrator.service ai-agent-analyst.service ai-agent-automation.service ai-agent-customer.service ai-agent-monitoring.service ai-agent-revenue.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/home/mwwoodworth/code/start_all_services.sh
ExecStop=/home/mwwoodworth/code/stop_all_services.sh
User=mwwoodworth

[Install]
WantedBy=multi-user.target
EOF

echo "Created /tmp/brainops-master.service"

echo ""
echo "✅ All systemd service files created in /tmp/"
echo ""
echo "To install them system-wide, run:"
echo "sudo cp /tmp/*.service /etc/systemd/system/"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable brainops-master.service"
echo "sudo systemctl start brainops-master.service"