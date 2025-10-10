#!/bin/bash

echo "🔒 ENSURING PERMANENT OPERATION OF ALL BRAINOPS SYSTEMS"
echo "========================================================"
echo "Time: $(date)"

# 1. Add to user's bashrc for login startup
echo ""
echo "1️⃣ Adding to bashrc for login startup..."
if ! grep -q "start_all_services.sh" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# BrainOps Auto-Start" >> ~/.bashrc
    echo "/home/mwwoodworth/code/start_all_services.sh > /dev/null 2>&1 &" >> ~/.bashrc
    echo "✅ Added to ~/.bashrc"
else
    echo "✅ Already in ~/.bashrc"
fi

# 2. Ensure cron job exists and is active
echo ""
echo "2️⃣ Verifying cron job..."
if crontab -l 2>/dev/null | grep -q "start_all_services.sh"; then
    echo "✅ Cron job exists (runs every 5 minutes)"
else
    echo "Adding cron job..."
    (crontab -l 2>/dev/null; echo "*/5 * * * * /home/mwwoodworth/code/start_all_services.sh") | crontab -
    echo "✅ Cron job added"
fi

# 3. Create @reboot cron entry
echo ""
echo "3️⃣ Adding @reboot cron entry..."
if ! crontab -l 2>/dev/null | grep -q "@reboot.*start_all_services"; then
    (crontab -l 2>/dev/null; echo "@reboot /home/mwwoodworth/code/start_all_services.sh") | crontab -
    echo "✅ Added @reboot entry"
else
    echo "✅ @reboot entry exists"
fi

# 4. Create supervisor config (alternative to systemd)
echo ""
echo "4️⃣ Creating supervisor configuration..."
mkdir -p /home/mwwoodworth/.config/supervisor

cat > /home/mwwoodworth/.config/supervisor/brainops.conf << 'EOF'
[program:mcp-database]
command=python3 server.py
directory=/home/mwwoodworth/code/mcp-servers/database-mcp
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-database.err.log
stdout_logfile=/var/log/mcp-database.out.log

[program:mcp-crm]
command=python3 server.py
directory=/home/mwwoodworth/code/mcp-servers/crm-mcp
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-crm.err.log
stdout_logfile=/var/log/mcp-crm.out.log

[program:mcp-erp]
command=python3 server.py
directory=/home/mwwoodworth/code/mcp-servers/erp-mcp
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-erp.err.log
stdout_logfile=/var/log/mcp-erp.out.log

[program:ai-agent-orchestrator]
command=python3 agent.py
directory=/home/mwwoodworth/code/ai-agents/orchestrator-agent
autostart=true
autorestart=true
stderr_logfile=/var/log/ai-orchestrator.err.log
stdout_logfile=/var/log/ai-orchestrator.out.log

[group:brainops]
programs=mcp-database,mcp-crm,mcp-erp,ai-agent-orchestrator
EOF

echo "✅ Supervisor config created"

# 5. Make all scripts executable
echo ""
echo "5️⃣ Making all scripts executable..."
chmod +x /home/mwwoodworth/code/start_all_services.sh
chmod +x /home/mwwoodworth/code/start_mcp_*.py 2>/dev/null
chmod +x /home/mwwoodworth/code/start_agent_*.py 2>/dev/null
echo "✅ Scripts are executable"

# 6. Start everything now
echo ""
echo "6️⃣ Starting all services now..."
/home/mwwoodworth/code/start_all_services.sh

# 7. Verify services are running
echo ""
echo "7️⃣ Verifying services..."
sleep 3

running_mcp=$(ss -tulpn 2>/dev/null | grep -E ":(500[1-6])" | wc -l)
running_agents=$(ss -tulpn 2>/dev/null | grep -E ":(600[1-6])" | wc -l)

echo "MCP Servers running: $running_mcp/6"
echo "AI Agents running: $running_agents/6"

echo ""
echo "========================================================"
echo "✅ PERMANENT OPERATION SETUP COMPLETE!"
echo ""
echo "Services will automatically start:"
echo "  • On system boot (@reboot cron)"
echo "  • On user login (bashrc)"
echo "  • Every 5 minutes (cron job)"
echo "  • If any crash (supervisor - if installed)"
echo ""
echo "No manual startup required!"
echo "========================================================"