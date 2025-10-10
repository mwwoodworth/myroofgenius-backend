#!/bin/bash
# Monitor v9.16 Deployment Status
# Deploy ID: dep-d2j66075r7bs73eg1m60

echo "🚀 MONITORING BACKEND v9.16 DEPLOYMENT"
echo "======================================"
echo "Deploy ID: dep-d2j66075r7bs73eg1m60"
echo "Started: $(date)"
echo ""

# Monitor for up to 10 minutes
for i in {1..20}; do
    echo "Check $i/20 ($(date +%H:%M:%S))..."
    
    # Get current version
    response=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health 2>&1)
    
    if echo "$response" | grep -q '"version":"9.16"'; then
        echo ""
        echo "✅ SUCCESS! v9.16 is LIVE!"
        echo "======================================"
        echo "$response" | python3 -m json.tool
        
        # Store success in persistent memory
        python3 -c "
import psycopg2
import json
from datetime import datetime, UTC

DATABASE_URL = 'postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require'

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

deployment_success = {
    'version': 'v9.16',
    'deploy_id': 'dep-d2j66075r7bs73eg1m60',
    'status': 'live',
    'timestamp': datetime.now(UTC).isoformat(),
    'health_response': json.loads('$response')
}

cur.execute('''
    INSERT INTO neural_os_knowledge 
    (component_name, component_type, agent_name, knowledge_type, 
     knowledge_data, confidence_score, review_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (component_name, knowledge_type, agent_name)
    DO UPDATE SET 
        knowledge_data = EXCLUDED.knowledge_data,
        updated_at = CURRENT_TIMESTAMP
''', (
    'Backend v9.16 Live',
    'deployment',
    'DevOps Engineer',
    'deployment_success',
    json.dumps(deployment_success),
    1.0,
    'v916_live'
))

conn.commit()
conn.close()
print('✅ Deployment success stored in persistent memory!')
"
        
        exit 0
    else
        # Extract current version
        current_version=$(echo "$response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        echo "  Current version: $current_version (waiting for v9.16...)"
    fi
    
    # Wait 30 seconds before next check
    sleep 30
done

echo ""
echo "⚠️ Deployment did not complete within 10 minutes"
echo "Last response:"
curl -s https://brainops-backend-prod.onrender.com/api/v1/health | python3 -m json.tool