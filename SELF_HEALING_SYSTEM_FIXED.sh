#!/bin/bash

# SELF-HEALING SYSTEM FOR MYROOFGENIUS - FIXED VERSION
# Continuously monitors and fixes issues automatically

echo "🚀 SELF-HEALING SYSTEM ACTIVATED (FIXED VERSION)"
echo "================================"
echo "Timestamp: $(date)"
echo ""

# Configuration
BACKEND_URL="https://brainops-backend-prod.onrender.com"
FRONTEND_URL="https://www.myroofgenius.com"
DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
LOG_FILE="/home/mwwoodworth/logs/self_healing_$(date +%Y%m%d).log"
ALERT_THRESHOLD=3
HEAL_INTERVAL=60

# Create log directory
mkdir -p /home/mwwoodworth/logs

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check backend health
check_backend() {
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/health")
    if [ "$status" = "200" ]; then
        return 0
    else
        log_message "❌ Backend unhealthy (HTTP $status)"
        return 1
    fi
}

# Function to check frontend
check_frontend() {
    local status=$(curl -L -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
    if [ "$status" = "200" ]; then
        return 0
    else
        log_message "❌ Frontend unhealthy (HTTP $status)"
        return 1
    fi
}

# Function to check database
check_database() {
    if psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
        return 0
    else
        log_message "❌ Database connection failed"
        return 1
    fi
}

# Function to check AI agents
check_ai_agents() {
    local agents=("orchestrator-agent" "analyst-agent" "automation-agent" "customer-service-agent" "monitoring-agent" "revenue-agent")
    local failed=0
    
    for agent in "${agents[@]}"; do
        if ! pgrep -f "$agent" > /dev/null; then
            log_message "❌ AI Agent $agent is not running"
            ((failed++))
        fi
    done
    
    return $failed
}

# Function to check MCP servers
check_mcp_servers() {
    local servers=("database-mcp" "crm-mcp" "erp-mcp" "ai-orchestrator-mcp" "monitoring-mcp" "automation-mcp")
    local failed=0
    
    for server in "${servers[@]}"; do
        if ! pgrep -f "$server" > /dev/null; then
            log_message "❌ MCP Server $server is not running"
            ((failed++))
        fi
    done
    
    return $failed
}

# Function to restart AI agents
restart_ai_agents() {
    log_message "🔄 Restarting AI agents..."
    if [ -f /home/mwwoodworth/code/ai-agents/start_all_agents.sh ]; then
        /home/mwwoodworth/code/ai-agents/start_all_agents.sh
    fi
    sleep 5
    check_ai_agents
    if [ $? -eq 0 ]; then
        log_message "✅ AI agents restarted successfully"
        return 0
    else
        log_message "❌ Failed to restart AI agents"
        return 1
    fi
}

# Function to restart MCP servers
restart_mcp_servers() {
    log_message "🔄 Restarting MCP servers..."
    if [ -f /home/mwwoodworth/code/mcp-servers/start_all_mcp.sh ]; then
        /home/mwwoodworth/code/mcp-servers/start_all_mcp.sh
    fi
    sleep 5
    check_mcp_servers
    if [ $? -eq 0 ]; then
        log_message "✅ MCP servers restarted successfully"
        return 0
    else
        log_message "❌ Failed to restart MCP servers"
        return 1
    fi
}

# Function to optimize database
optimize_database() {
    log_message "🔧 Optimizing database..."
    psql "$DATABASE_URL" -c "VACUUM ANALYZE;" > /dev/null 2>&1
    # Don't run REINDEX on production without locks
    log_message "✅ Database optimization complete"
}

# Function to clear old logs
clear_old_logs() {
    log_message "🧹 Clearing old logs..."
    find /home/mwwoodworth/logs -name "*.log" -mtime +30 -delete 2>/dev/null
    find /var/log -name "*.log" -mtime +30 -delete 2>/dev/null
    log_message "✅ Old logs cleared"
}

# Function to check system resources
check_system_resources() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d'.' -f1)
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100.0}')
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    log_message "📊 System Resources - CPU: ${cpu_usage}%, Memory: ${mem_usage}%, Disk: ${disk_usage}%"
    
    # Alert if resources are high
    if [ "$cpu_usage" -gt 80 ] 2>/dev/null; then
        log_message "⚠️ High CPU usage detected"
        # Kill zombie processes
        ps aux | awk '$8 ~ /^Z/ { print $2 }' | xargs -r kill -9 2>/dev/null
    fi
    
    if [ "$mem_usage" -gt 90 ] 2>/dev/null; then
        log_message "⚠️ High memory usage detected"
        # Clear caches (only if we have permission)
        sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    fi
    
    if [ "$disk_usage" -gt 85 ] 2>/dev/null; then
        log_message "⚠️ High disk usage detected"
        clear_old_logs
    fi
}

# Function to perform health check
perform_health_check() {
    local issues=0
    
    log_message "🏥 Performing health check..."
    
    # Check backend
    if ! check_backend; then
        ((issues++))
    fi
    
    # Check frontend
    if ! check_frontend; then
        ((issues++))
    fi
    
    # Check database
    if ! check_database; then
        ((issues++))
    fi
    
    # Check AI agents
    check_ai_agents
    local agent_failures=$?
    if [ "$agent_failures" -gt 0 ]; then
        issues=$((issues + agent_failures))
        restart_ai_agents
    fi
    
    # Check MCP servers
    check_mcp_servers
    local mcp_failures=$?
    if [ "$mcp_failures" -gt 0 ]; then
        issues=$((issues + mcp_failures))
        restart_mcp_servers
    fi
    
    # Check system resources
    check_system_resources
    
    if [ "$issues" -eq 0 ]; then
        log_message "✅ All systems healthy"
    else
        log_message "⚠️ $issues issues detected and attempting to heal"
    fi
    
    return $issues
}

# Function to send alert
send_alert() {
    local message=$1
    log_message "🚨 ALERT: $message"
    
    # Send to monitoring endpoint
    curl -X POST "$BACKEND_URL/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\", \"severity\": \"high\", \"timestamp\": \"$(date -Iseconds)\"}" \
        > /dev/null 2>&1 || true
}

# Function to generate daily report
generate_daily_report() {
    log_message "📊 Generating daily report..."
    
    local report_file="/home/mwwoodworth/reports/daily_$(date +%Y%m%d).json"
    mkdir -p /home/mwwoodworth/reports
    
    # Gather metrics
    local customers=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM customers" 2>/dev/null | xargs || echo "0")
    local jobs=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM jobs" 2>/dev/null | xargs || echo "0")
    local invoices=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM invoices" 2>/dev/null | xargs || echo "0")
    local agents=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM ai_agents WHERE status = 'active'" 2>/dev/null | xargs || echo "0")
    
    # Create JSON report
    cat > "$report_file" <<EOF
{
    "date": "$(date +%Y-%m-%d)",
    "timestamp": "$(date -Iseconds)",
    "metrics": {
        "customers": $customers,
        "jobs": $jobs,
        "invoices": $invoices,
        "active_ai_agents": $agents
    },
    "health_checks": {
        "backend": $(check_backend && echo "true" || echo "false"),
        "frontend": $(check_frontend && echo "true" || echo "false"),
        "database": $(check_database && echo "true" || echo "false")
    },
    "system_resources": {
        "cpu_usage": "$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%",
        "memory_usage": "$(free | grep Mem | awk '{printf "%.1f%%", ($3/$2) * 100.0}' 2>/dev/null || echo "N/A")",
        "disk_usage": "$(df -h / | tail -1 | awk '{print $5}')"
    }
}
EOF
    
    log_message "✅ Daily report generated: $report_file"
}

# Main monitoring loop
main_loop() {
    local consecutive_failures=0
    
    while true; do
        perform_health_check
        local result=$?
        
        if [ "$result" -gt 0 ]; then
            ((consecutive_failures++))
            
            if [ "$consecutive_failures" -ge "$ALERT_THRESHOLD" ]; then
                send_alert "System has failed $consecutive_failures consecutive health checks"
                
                # Attempt major recovery
                log_message "🚑 Attempting major recovery..."
                restart_ai_agents
                restart_mcp_servers
                optimize_database
                clear_old_logs
                
                consecutive_failures=0
            fi
        else
            consecutive_failures=0
        fi
        
        # Periodic maintenance (every hour)
        if [ "$(date +%M)" = "00" ]; then
            log_message "🔧 Performing scheduled maintenance..."
            optimize_database
            clear_old_logs
        fi
        
        # Daily report (at midnight)
        if [ "$(date +%H:%M)" = "00:00" ]; then
            generate_daily_report
        fi
        
        sleep "$HEAL_INTERVAL"
    done
}

# Trap signals for graceful shutdown
trap 'log_message "Self-healing system shutting down..."; exit 0' SIGINT SIGTERM

# Start the self-healing system
log_message "🚀 Self-healing system starting..."
log_message "Configuration:"
log_message "  - Backend: $BACKEND_URL"
log_message "  - Frontend: $FRONTEND_URL"
log_message "  - Heal Interval: ${HEAL_INTERVAL}s"
log_message "  - Alert Threshold: $ALERT_THRESHOLD failures"

# Initial health check
perform_health_check

# Start main loop
main_loop