#\!/bin/bash
# AUREA QC System Launcher

echo "🚀 Starting AUREA Quality Control System..."

# Check if already running
if pgrep -f "AUREA_CLAUDEOS_QC_SYSTEM.py" > /dev/null; then
    echo "✅ AUREA QC already running"
    exit 0
fi

# Start in background with logging
nohup python3 /home/mwwoodworth/code/AUREA_CLAUDEOS_QC_SYSTEM.py > /tmp/aurea_qc.log 2>&1 &
QC_PID=$\!

echo "✅ AUREA QC started with PID: $QC_PID"
echo $QC_PID > /tmp/aurea_qc.pid

# Verify it's running
sleep 2
if ps -p $QC_PID > /dev/null; then
    echo "✅ AUREA QC System is operational"
    echo "📝 Logs available at: /tmp/aurea_qc.log"
else
    echo "❌ AUREA QC failed to start"
    cat /tmp/aurea_qc.log
fi
