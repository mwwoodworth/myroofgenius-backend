#!/bin/bash
# CenterPoint Sync Service Manager

case "$1" in
    start)
        if [ -f /tmp/centerpoint_sync.pid ]; then
            PID=$(cat /tmp/centerpoint_sync.pid)
            if ps -p $PID > /dev/null; then
                echo "Service already running with PID $PID"
                exit 1
            fi
        fi
        nohup python3 /home/mwwoodworth/code/CENTERPOINT_24_7_SYNC_SERVICE.py > /tmp/centerpoint_sync_output.log 2>&1 &
        echo $! > /tmp/centerpoint_sync.pid
        echo "Started CenterPoint sync service"
        ;;
    stop)
        if [ -f /tmp/centerpoint_sync.pid ]; then
            kill $(cat /tmp/centerpoint_sync.pid)
            rm /tmp/centerpoint_sync.pid
            echo "Stopped CenterPoint sync service"
        else
            echo "Service not running"
        fi
        ;;
    status)
        if [ -f /tmp/centerpoint_sync.pid ]; then
            PID=$(cat /tmp/centerpoint_sync.pid)
            if ps -p $PID > /dev/null; then
                echo "Service running with PID $PID"
                tail -10 /tmp/centerpoint_sync.log
            else
                echo "Service not running (stale PID file)"
            fi
        else
            echo "Service not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
