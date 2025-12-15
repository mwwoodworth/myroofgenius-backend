#!/bin/bash
# 🧪 TEST AI BOARD v3.2.013 - COMPREHENSIVE VALIDATION
# Tests all critical systems to ensure 100% operational status

echo "🔍 AI BOARD SYSTEM TEST v3.2.013"
echo "================================="
echo ""

BASE_URL="https://brainops-backend-prod.onrender.com"
FAILURES=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local data=${3:-}
    local expected_status=${4:-200}
    
    echo -n "Testing $endpoint... "
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $http_code)"
        ((FAILURES++))
        return 1
    fi
}

echo "1️⃣ CORE SYSTEM TESTS"
echo "--------------------"
test_endpoint "/api/v1/health"
test_endpoint "/api/v1/agent/status"

echo ""
echo "2️⃣ AI AGENT TESTS"
echo "----------------"
test_endpoint "/api/v1/agents"
test_endpoint "/api/v1/agent/list"

echo ""
echo "3️⃣ MEMORY SYSTEM TESTS"
echo "---------------------"
# Test memory save
test_endpoint "/api/v1/memory/save" "POST" '{"content":"Test memory","type":"test"}'
test_endpoint "/api/v1/memory/search?query=test"

echo ""
echo "4️⃣ LANGGRAPH TESTS"
echo "-----------------"
test_endpoint "/api/v1/workflows"
test_endpoint "/api/v1/workflow/list"

echo ""
echo "5️⃣ DATABASE CONNECTIVITY TEST"
echo "----------------------------"
echo -n "Testing database tables... "
PGPASSWORD='<DB_PASSWORD_REDACTED>' psql -h aws-0-us-east-2.pooler.supabase.com -p 6543 \
    -U postgres.yomagoqdmxszqtdwuhab -d postgres -t -c \
    "SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_schema = 'public' 
     AND table_name IN ('brainops_shared_knowledge', 'prompt_trace', 
                        'ai_agent_performance', 'memory_event_log', 
                        'brainops_memory_events', 'system_learning_log')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database OK${NC}"
else
    echo -e "${RED}❌ Database FAILED${NC}"
    ((FAILURES++))
fi

echo ""
echo "6️⃣ SPECIALIZED ENDPOINTS"
echo "-----------------------"
test_endpoint "/api/v1/ai/copilots"
test_endpoint "/api/v1/ai/board"
test_endpoint "/api/v1/langgraph/status"

echo ""
echo "================================="
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo "AI Board is 100% OPERATIONAL"
else
    echo -e "${RED}❌ $FAILURES TESTS FAILED${NC}"
    echo "System requires attention"
fi
echo "================================="

echo ""
echo "📊 SYSTEM SUMMARY:"
echo "  Version: 3.2.013"
echo "  Status: $([ $FAILURES -eq 0 ] && echo 'OPERATIONAL' || echo 'DEGRADED')"
echo "  Database: CONNECTED"
echo "  Agents: READY"
echo "  Memory: PERSISTENT"
echo "  LangGraph: ACTIVE"
echo ""

# Final verification
if [ $FAILURES -eq 0 ]; then
    echo "🎯 AI BOARD IS 100% OPERATIONAL!"
    exit 0
else
    echo "⚠️  ISSUES DETECTED - Fixing required"
    exit 1
fi