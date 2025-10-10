#!/bin/bash
# Revenue Optimization Daemon

while true; do
    # Check for new leads every 5 minutes
    python3 /home/mwwoodworth/code/AUTONOMOUS_REVENUE_ENGINE.py --daemon
    
    # Sleep for 5 minutes
    sleep 300
done
