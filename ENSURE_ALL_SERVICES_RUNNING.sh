#!/bin/bash
# Ensure all MCP servers and critical services are always running
# This script should be run on system startup and periodically via cron

echo "🚀 BRAINOPS SERVICE MONITOR - Ensuring all systems operational"
echo "=================================================="
echo "Timestamp: $(date)"
echo ""

# Function to check and start a service
check_and_start() {
    local service_name=$1
    local check_command=$2
    local start_command=$3
    local log_file=$4
    
    echo -n "Checking $service_name... "
    
    if eval "$check_command" > /dev/null 2>&1; then
        echo "✅ Running"
    else
        echo "❌ Not running - Starting now..."
        eval "$start_command" > "$log_file" 2>&1 &
        sleep 2
        if eval "$check_command" > /dev/null 2>&1; then
            echo "   ✅ Started successfully"
        else
            echo "   ❌ Failed to start - Check $log_file"
        fi
    fi
}

# 1. Check MCP Servers
echo "1️⃣ MCP SERVERS"
echo "---------------"

# Database MCP (port 5001)
check_and_start "Database MCP" \
    "lsof -i:5001" \
    "cd /home/mwwoodworth/code/mcp-servers/database-mcp && nohup python3 server.py" \
    "/tmp/database-mcp.log"

# CRM MCP (port 5002)
check_and_start "CRM MCP" \
    "lsof -i:5002" \
    "cd /home/mwwoodworth/code/mcp-servers/crm-mcp && nohup python3 server.py" \
    "/tmp/crm-mcp.log"

# ERP MCP (port 5003)
check_and_start "ERP MCP" \
    "lsof -i:5003" \
    "cd /home/mwwoodworth/code/mcp-servers/erp-mcp && nohup python3 server.py" \
    "/tmp/erp-mcp.log"

# AI Orchestrator MCP (port 5004)
check_and_start "AI Orchestrator MCP" \
    "lsof -i:5004" \
    "cd /home/mwwoodworth/code/mcp-servers/ai-orchestrator-mcp && nohup python3 server.py" \
    "/tmp/ai-orchestrator-mcp.log"

# Monitoring MCP (port 5005)
check_and_start "Monitoring MCP" \
    "lsof -i:5005" \
    "cd /home/mwwoodworth/code/mcp-servers/monitoring-mcp && nohup python3 server.py" \
    "/tmp/monitoring-mcp.log"

# Automation MCP (port 5006)
check_and_start "Automation MCP" \
    "lsof -i:5006" \
    "cd /home/mwwoodworth/code/mcp-servers/automation-mcp && nohup python3 server.py" \
    "/tmp/automation-mcp.log"

echo ""

# 2. Check BrainOps MCP Server
echo "2️⃣ BRAINOPS MCP SERVER"
echo "----------------------"

check_and_start "BrainOps MCP" \
    "pgrep -f 'brainops_mcp_server/server.py'" \
    "cd /home/mwwoodworth/brainops && source venv/bin/activate && nohup python3 tools/mcp/brainops_mcp_server/server.py" \
    "/tmp/brainops-mcp.log"

echo ""

# 3. Check Backend API Health
echo "3️⃣ BACKEND API"
echo "--------------"
echo -n "Checking backend API... "
if curl -s https://brainops-backend-prod.onrender.com/api/v1/health | grep -q "healthy"; then
    echo "✅ Healthy"
else
    echo "⚠️  Issues detected - May need redeployment"
fi

echo ""

# 4. Check Database Connection
echo "4️⃣ DATABASE"
echo "-----------"
echo -n "Checking database... "
export DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
if psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ Connected"
else
    echo "⚠️  Connection issues"
fi

echo ""

# 5. Setup Cron Job if not exists
echo "5️⃣ CRON MONITORING"
echo "-----------------"
if ! crontab -l 2>/dev/null | grep -q "ENSURE_ALL_SERVICES_RUNNING.sh"; then
    echo "Setting up cron job for continuous monitoring..."
    (crontab -l 2>/dev/null; echo "*/5 * * * * /home/mwwoodworth/code/ENSURE_ALL_SERVICES_RUNNING.sh > /tmp/service-monitor.log 2>&1") | crontab -
    echo "✅ Cron job created (runs every 5 minutes)"
else
    echo "✅ Cron job already exists"
fi

echo ""

# 6. Create startup script
echo "6️⃣ STARTUP SCRIPT"
echo "----------------"
STARTUP_SCRIPT="/home/mwwoodworth/.bashrc"
if ! grep -q "ENSURE_ALL_SERVICES_RUNNING.sh" "$STARTUP_SCRIPT" 2>/dev/null; then
    echo "# Auto-start BrainOps services" >> "$STARTUP_SCRIPT"
    echo "/home/mwwoodworth/code/ENSURE_ALL_SERVICES_RUNNING.sh > /tmp/startup-services.log 2>&1 &" >> "$STARTUP_SCRIPT"
    echo "✅ Added to .bashrc for startup"
else
    echo "✅ Already in startup script"
fi

echo ""

# 7. Summary
echo "📊 SUMMARY"
echo "----------"
MCP_COUNT=$(ps aux | grep -E "mcp.*server\.py" | grep -v grep | wc -l)
echo "MCP Servers Running: $MCP_COUNT/7"
echo "Backend API: $(curl -s https://brainops-backend-prod.onrender.com/api/v1/health | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "Unknown")"
echo "Log files: /tmp/*-mcp.log"
echo ""
echo "✅ Service monitoring complete!"
echo "=================================================="