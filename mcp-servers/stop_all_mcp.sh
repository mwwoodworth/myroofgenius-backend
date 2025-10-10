#!/bin/bash
# Stop all MCP servers

echo "Stopping MCP servers..."

# Kill all server processes by reading PID files
for pidfile in /home/mwwoodworth/code/mcp-servers/*/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping process $PID from $pidfile"
            kill $PID
        fi
        rm -f "$pidfile"
    fi
done

# Also kill any orphaned python3 server.py processes
pkill -f "python3.*server.py"

echo "All MCP servers stopped!"