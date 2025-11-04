#!/bin/bash

# CENTERPOINT CONTINUOUS SYNC - Runs until we get ALL data
# Target: 1-2 million data points

echo "🚀 STARTING CENTERPOINT CONTINUOUS SYNC"
echo "Target: 1-2 million data points"
echo "Mode: PRODUCTION DATA ONLY"
echo ""

# Run in a loop with longer timeout
while true; do
    echo "$(date): Starting sync batch..."
    
    # Run with 5 minute timeout
    cd /home/mwwoodworth/code/weathercraft-erp
    DATABASE_URL='postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require' \
        timeout 300 npx tsx scripts/COMPLETE_CENTERPOINT_SYNC_V2.ts
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ Sync completed successfully"
        break
    elif [ $EXIT_CODE -eq 124 ]; then
        echo "⏱️ Sync timed out after 5 minutes, continuing..."
        sleep 5
    else
        echo "❌ Sync failed with exit code $EXIT_CODE"
        sleep 10
    fi
    
    # Update progress in Task OS
    python3 /home/mwwoodworth/code/UPDATE_TASK_OS_SYNC_PROGRESS.py
    
    # Check if we've reached our target
    TOTAL_SYNCED=$(psql -h aws-0-us-east-2.pooler.supabase.com -U postgres.yomagoqdmxszqtdwuhab -d postgres \
        -t -c "SELECT COUNT(*) FROM customers WHERE external_id LIKE 'CP-%'" 2>/dev/null | tr -d ' ')
    
    echo "📊 Total customers synced so far: $TOTAL_SYNCED"
    
    if [ "$TOTAL_SYNCED" -ge 1000000 ]; then
        echo "🎯 Reached 1 million+ data points!"
        break
    fi
done

echo ""
echo "✅ CENTERPOINT CONTINUOUS SYNC COMPLETE"
python3 /home/mwwoodworth/code/UPDATE_TASK_OS_SYNC_PROGRESS.py