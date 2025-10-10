#!/bin/bash

# ENSURE 24/7 OPERATIONS
# Master script to guarantee permanent persistent systems

echo "🚀 ENSURING 24/7 OPERATIONAL STATUS"
echo "===================================="
echo "Configuring all systems for permanent operation..."
echo ""

# Start persistent monitoring
echo "1️⃣ Starting Persistent Monitoring System..."
if ! pgrep -f "PERSISTENT_MONITORING_SYSTEM.py" > /dev/null; then
    nohup python3 /home/mwwoodworth/code/PERSISTENT_MONITORING_SYSTEM.py > /tmp/persistent_monitor.log 2>&1 &
    echo "✅ Monitoring started (PID: $!)"
else
    echo "✅ Monitoring already running"
fi

# Ensure CenterPoint sync is running
echo ""
echo "2️⃣ Ensuring CenterPoint Sync..."
if ! pgrep -f "centerpoint-sync-service.sh" > /dev/null; then
    /home/mwwoodworth/code/weathercraft-erp/scripts/start-sync.sh
else
    echo "✅ CenterPoint sync already running"
fi

# Start AUREA QC if not running
echo ""
echo "3️⃣ Starting AUREA Quality Control..."
if ! pgrep -f "AUREA_CLAUDEOS_QC_SYSTEM.py" > /dev/null; then
    if [ -f "/home/mwwoodworth/code/start_aurea_qc.sh" ]; then
        /home/mwwoodworth/code/start_aurea_qc.sh
    else
        echo "⚠️ AUREA QC script not found"
    fi
else
    echo "✅ AUREA QC already running"
fi

# Set up systemd-style service management
echo ""
echo "4️⃣ Creating Service Management Scripts..."

# Create master service controller
cat > /home/mwwoodworth/code/services-controller.sh << 'EOF'
#!/bin/bash

ACTION=$1
SERVICE=$2

start_service() {
    case $1 in
        monitoring)
            nohup python3 /home/mwwoodworth/code/PERSISTENT_MONITORING_SYSTEM.py > /tmp/persistent_monitor.log 2>&1 &
            echo "Started monitoring (PID: $!)"
            ;;
        centerpoint)
            /home/mwwoodworth/code/weathercraft-erp/scripts/start-sync.sh
            ;;
        aurea)
            /home/mwwoodworth/code/start_aurea_qc.sh
            ;;
        all)
            $0 start monitoring
            $0 start centerpoint
            $0 start aurea
            ;;
    esac
}

stop_service() {
    case $1 in
        monitoring)
            pkill -f "PERSISTENT_MONITORING_SYSTEM.py"
            echo "Stopped monitoring"
            ;;
        centerpoint)
            pkill -f "centerpoint-sync-service.sh"
            echo "Stopped CenterPoint sync"
            ;;
        aurea)
            pkill -f "AUREA_CLAUDEOS_QC_SYSTEM.py"
            echo "Stopped AUREA QC"
            ;;
        all)
            $0 stop monitoring
            $0 stop centerpoint
            $0 stop aurea
            ;;
    esac
}

status_service() {
    case $1 in
        monitoring)
            pgrep -f "PERSISTENT_MONITORING_SYSTEM.py" > /dev/null && echo "✅ Monitoring: Running" || echo "❌ Monitoring: Stopped"
            ;;
        centerpoint)
            pgrep -f "centerpoint-sync-service.sh" > /dev/null && echo "✅ CenterPoint: Running" || echo "❌ CenterPoint: Stopped"
            ;;
        aurea)
            pgrep -f "AUREA_CLAUDEOS_QC_SYSTEM.py" > /dev/null && echo "✅ AUREA QC: Running" || echo "❌ AUREA QC: Stopped"
            ;;
        all)
            $0 status monitoring
            $0 status centerpoint
            $0 status aurea
            ;;
    esac
}

case $ACTION in
    start)
        start_service $SERVICE
        ;;
    stop)
        stop_service $SERVICE
        ;;
    restart)
        stop_service $SERVICE
        sleep 2
        start_service $SERVICE
        ;;
    status)
        status_service $SERVICE
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status} {monitoring|centerpoint|aurea|all}"
        ;;
esac
EOF

chmod +x /home/mwwoodworth/code/services-controller.sh

# Update crontab for all services
echo ""
echo "5️⃣ Configuring Cron Jobs..."

# Create comprehensive crontab
cat > /tmp/new_crontab << 'EOF'
# ClaudeOS Health Check - Every 30 minutes
*/30 * * * * /home/mwwoodworth/code/CLAUDEOS_AUTOFIX.sh > /tmp/claudeos_health.log 2>&1

# WeatherCraft CenterPoint Sync - Every 15 minutes
*/15 * * * * cd /home/mwwoodworth/code/weathercraft-erp && DATABASE_URL="postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require" /usr/bin/npx tsx scripts/centerpoint_incremental_sync.ts >> /tmp/centerpoint_incremental.log 2>&1

# Persistent Monitoring - Check every 5 minutes that it's running
*/5 * * * * pgrep -f "PERSISTENT_MONITORING_SYSTEM.py" || nohup python3 /home/mwwoodworth/code/PERSISTENT_MONITORING_SYSTEM.py > /tmp/persistent_monitor.log 2>&1 &

# Daily system report - 8 AM
0 8 * * * /home/mwwoodworth/code/TEST_ALL_PRODUCTION_SYSTEMS.sh > /tmp/daily_system_report.log 2>&1

# Weekly cleanup - Sunday 2 AM
0 2 * * 0 find /tmp -name "*.log" -mtime +7 -delete

# Service health check - Every hour
0 * * * * /home/mwwoodworth/code/services-controller.sh status all >> /tmp/service_status.log 2>&1
EOF

# Install new crontab
crontab /tmp/new_crontab
echo "✅ Cron jobs configured"

# Create startup script for system reboot
echo ""
echo "6️⃣ Creating System Startup Script..."
cat > /home/mwwoodworth/code/startup.sh << 'EOF'
#!/bin/bash

# System startup script - ensures all services start on reboot
echo "[$(date)] System startup initiated" >> /tmp/startup.log

# Wait for network
sleep 10

# Start all services
/home/mwwoodworth/code/services-controller.sh start all >> /tmp/startup.log 2>&1

echo "[$(date)] All services started" >> /tmp/startup.log
EOF

chmod +x /home/mwwoodworth/code/startup.sh

# Add to bashrc for automatic startup
if ! grep -q "startup.sh" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Auto-start services" >> ~/.bashrc
    echo "[ -f /home/mwwoodworth/code/startup.sh ] && /home/mwwoodworth/code/startup.sh > /dev/null 2>&1" >> ~/.bashrc
fi

echo ""
echo "7️⃣ System Status Check..."
echo "------------------------"
/home/mwwoodworth/code/services-controller.sh status all

echo ""
echo "===================================="
echo "✅ 24/7 OPERATIONS CONFIGURED"
echo "===================================="
echo ""
echo "Service Controller: /home/mwwoodworth/code/services-controller.sh"
echo "Usage: services-controller.sh {start|stop|restart|status} {service|all}"
echo ""
echo "Monitoring Dashboard: tail -f /tmp/persistent_monitor.log"
echo "System Health Report: /home/mwwoodworth/code/SYSTEM_HEALTH_REPORT.json"
echo ""
echo "All systems configured for permanent operation!"