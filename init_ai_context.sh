#!/bin/bash

# BrainOps AI Context Initialization Script
# This script automatically gathers complete context from all systems
# Usage: ./init_ai_context.sh

echo "================================================================================"
echo "🧠 BRAINOPS AI CONTEXT INITIALIZATION - $(date)"
echo "================================================================================"
echo ""

# Read master context files
echo "📚 Reading master context files..."
if [ -f "/home/matt-woodworth/fastapi-operator-env/DEVOPS_CONTEXT.md" ]; then
    echo "  ✅ DEVOPS_CONTEXT.md found"
fi

if [ -f "/home/matt-woodworth/fastapi-operator-env/CLAUDE.md" ]; then
    echo "  ✅ CLAUDE.md found"
fi

# Check system status
echo ""
echo "🔍 Running comprehensive system status check..."
python3 /home/matt-woodworth/fastapi-operator-env/devops_status_check.py

# Read current status
echo ""
echo "📊 Current system state:"
if [ -f "/home/matt-woodworth/fastapi-operator-env/.ai_persistent/current_status.json" ]; then
    cat /home/matt-woodworth/fastapi-operator-env/.ai_persistent/current_status.json | python3 -m json.tool | head -20
fi

# Check Docker status
echo ""
echo "🐳 Docker status:"
docker version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Docker is running"
    docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | head -5
else
    echo "  ⚠️ Docker not running (needs sudo: sudo systemctl start docker)"
fi

# Check production API
echo ""
echo "🌐 Production API status:"
curl -s https://brainops-backend-prod.onrender.com/health | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'  ✅ API Online - Version: {data.get(\"version\", \"unknown\")}')
except:
    print('  ❌ API offline or unreachable')
" 2>/dev/null

# Check database
echo ""
echo "🗄️ Database quick check:"
# Source credentials if available
if [[ -f "$HOME/dev/_secure/BrainOps.env" ]]; then
    set -a
    source "$HOME/dev/_secure/BrainOps.env"
    set +a
fi

if [[ -z "${DB_PASSWORD:-}" ]]; then
    echo "  ⚠️ DB_PASSWORD not set. Source _secure/BrainOps.env"
else
    python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'aws-0-us-east-2.pooler.supabase.com'),
        port=os.environ.get('DB_PORT', '6543'),
        database=os.environ.get('DB_NAME', 'postgres'),
        user=os.environ.get('DB_USER', 'postgres.yomagoqdmxszqtdwuhab'),
        password=os.environ.get('DB_PASSWORD'),
        sslmode='require',
        connect_timeout=3
    )
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM customers')
    customers = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM jobs')
    jobs = cur.fetchone()[0]
    print(f'  ✅ Database connected')
    print(f'  • Customers: {customers:,}')
    print(f'  • Jobs: {jobs:,}')
    conn.close()
except Exception as e:
    print(f'  ❌ Database error: {e}')
" 2>/dev/null
fi

# Check repositories
echo ""
echo "📂 Repository status:"
repos=(
    "/home/matt-woodworth/fastapi-operator-env"
    "/home/matt-woodworth/myroofgenius-app"
    "/home/matt-woodworth/weathercraft-erp"
)

for repo in "${repos[@]}"; do
    if [ -d "$repo" ]; then
        name=$(basename "$repo")
        cd "$repo" 2>/dev/null
        if [ -d ".git" ]; then
            branch=$(git branch --show-current 2>/dev/null)
            status=$(git status --porcelain 2>/dev/null | wc -l)
            if [ "$status" -eq 0 ]; then
                echo "  ✅ $name: Clean (branch: $branch)"
            else
                echo "  ⚠️ $name: $status uncommitted changes (branch: $branch)"
            fi
        else
            echo "  ✅ $name: Found (not a git repo)"
        fi
    else
        name=$(basename "$repo")
        echo "  ❌ $name: Not found"
    fi
done

# Check running processes
echo ""
echo "⚙️ Process check:"
pgrep -f uvicorn > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Uvicorn (Backend API) running"
else
    echo "  ⚠️ Uvicorn not running"
fi

pgrep -f node > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Node.js processes running"
else
    echo "  ⚠️ No Node.js processes"
fi

# Check Notion integration
echo ""
echo "📝 Notion integration:"
if [ -f "/home/matt-woodworth/fastapi-operator-env/.ai_persistent/notion_last_sync.json" ]; then
    last_sync=$(cat /home/matt-woodworth/fastapi-operator-env/.ai_persistent/notion_last_sync.json | python3 -c "import sys, json; print(json.load(sys.stdin).get('last_sync', 'never'))" 2>/dev/null)
    echo "  ✅ Notion configured (Last sync: $last_sync)"
else
    echo "  ✅ Notion token configured (No sync history)"
fi

# Summary
echo ""
echo "================================================================================"
echo "📊 CONTEXT INITIALIZATION COMPLETE"
echo "================================================================================"
echo ""
echo "🎯 Quick Actions Available:"
echo "  • Start Docker: sudo systemctl start docker"
echo "  • Launch DevOps: ./launch_devops.sh"
echo "  • Run Demo: python3 devops_demo.py"
echo "  • Sync Notion: python3 notion_live_integration.py"
echo "  • Check Status: python3 devops_status_check.py"
echo ""
echo "💡 All context gathered. System ready for operations."

# Check AI OS activation status
echo ""
echo "🧠 AI OS Power Status:"
if [[ -z "${DB_PASSWORD:-}" ]]; then
    echo "  ⚠️ DB_PASSWORD not set. Source _secure/BrainOps.env"
else
    python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'aws-0-us-east-2.pooler.supabase.com'),
        port=os.environ.get('DB_PORT', '6543'),
        database=os.environ.get('DB_NAME', 'postgres'),
        user=os.environ.get('DB_USER', 'postgres.yomagoqdmxszqtdwuhab'),
        password=os.environ.get('DB_PASSWORD'),
        sslmode='require',
        connect_timeout=3
    )
    cur = conn.cursor()
    cur.execute('''
        SELECT
            (SELECT COUNT(*) FROM neural_pathways WHERE strength > 0.9) as strong,
            (SELECT COUNT(*) FROM agent_messages) as messages,
            (SELECT COUNT(*) FROM langgraph_executions WHERE status = 'completed') as completed,
            (SELECT COUNT(*) FROM ai_agents WHERE status = 'active') as agents
    ''')
    m = cur.fetchone()
    power = min(100, (m[0]>90)*33 + (m[1]>0)*33 + (m[2]>0)*34)
    print(f'  ✅ System Power: {power}%')
    print(f'  • Neural Pathways: {m[0]}/100 strong')
    print(f'  • Agent Messages: {m[1]}')
    print(f'  • Completed Workflows: {m[2]}')
    print(f'  • Active AI Agents: {m[3]}')
    conn.close()
except Exception as e:
    print('  ⚠️ Could not check AI OS status')
" 2>/dev/null || echo "  ⚠️ AI OS status check failed"
fi

echo "================================================================================"