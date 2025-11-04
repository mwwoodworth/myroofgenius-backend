#!/bin/bash

# System startup script - ensures all services start on reboot
echo "[$(date)] System startup initiated" >> /tmp/startup.log

# Wait for network
sleep 10

# Start all services
/home/mwwoodworth/code/services-controller.sh start all >> /tmp/startup.log 2>&1

echo "[$(date)] All services started" >> /tmp/startup.log
