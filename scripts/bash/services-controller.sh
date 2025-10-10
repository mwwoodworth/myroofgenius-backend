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
