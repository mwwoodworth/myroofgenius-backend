#!/bin/bash

# BrainOps Master System Monitor
# Continuously monitors all production systems

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="https://brainops-backend-prod.onrender.com"
FRONTEND_URL="https://www.myroofgenius.com"
WEATHERCRAFT_URL="https://weathercraft-app.vercel.app"
AUREA_URL="https://aurea-orchestrator-api.onrender.com"

# Check interval (seconds)
CHECK_INTERVAL=${1:-60}

echo "======================================"
echo "  BrainOps System Monitor v1.0"
echo "======================================"
echo "Checking every ${CHECK_INTERVAL} seconds..."
echo ""

check_system() {
    local name=$1
    local url=$2
    local endpoint=${3:-""}
    
    local full_url="${url}${endpoint}"
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$full_url" 2>/dev/null || echo "000")
    
    if [[ "$http_code" == "200" ]] || [[ "$http_code" == "307" ]] || [[ "$http_code" == "308" ]]; then
        echo -e "${GREEN}✓${NC} $name: ${GREEN}OPERATIONAL${NC} (HTTP $http_code)"
        return 0
    elif [[ "$http_code" == "000" ]]; then
        echo -e "${RED}✗${NC} $name: ${RED}TIMEOUT${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠${NC} $name: ${YELLOW}DEGRADED${NC} (HTTP $http_code)"
        return 1
    fi
}

check_api_details() {
    local response=$(curl -s --connect-timeout 5 "${BACKEND_URL}/api/v1/health" 2>/dev/null || echo "{}")
    
    if [[ -n "$response" ]] && [[ "$response" != "{}" ]]; then
        local version=$(echo "$response" | grep -o '"version":"[^"]*' | cut -d'"' -f4 || echo "unknown")
        local routes=$(echo "$response" | grep -o '"routes_loaded":[0-9]*' | cut -d':' -f2 || echo "0")
        local endpoints=$(echo "$response" | grep -o '"total_endpoints":[0-9]*' | cut -d':' -f2 || echo "0")
        
        echo "  └─ Version: $version | Routes: $routes | Endpoints: $endpoints"
    fi
}

monitor_loop() {
    while true; do
        clear
        echo "======================================"
        echo "  BrainOps System Status"
        echo "  $(date '+%Y-%m-%d %H:%M:%S UTC')"
        echo "======================================"
        echo ""
        
        # Check Backend API
        if check_system "Backend API" "$BACKEND_URL" "/api/v1/health"; then
            check_api_details
        fi
        echo ""
        
        # Check Frontend
        check_system "MyRoofGenius" "$FRONTEND_URL" ""
        echo ""
        
        # Check WeatherCraft
        check_system "WeatherCraft" "$WEATHERCRAFT_URL" ""
        echo ""
        
        # Check AUREA (expected to fail for now)
        check_system "AUREA Orchestrator" "$AUREA_URL" "/health"
        echo ""
        
        # Database check via API
        echo "Database Status:"
        local db_status=$(curl -s "${BACKEND_URL}/api/v1/health" | grep -o '"database":"[^"]*' | cut -d'"' -f4 || echo "unknown")
        if [[ "$db_status" == "connected" ]]; then
            echo -e "  └─ ${GREEN}✓${NC} PostgreSQL: ${GREEN}CONNECTED${NC}"
        else
            echo -e "  └─ ${RED}✗${NC} PostgreSQL: ${RED}DISCONNECTED${NC}"
        fi
        echo ""
        
        # Summary
        echo "======================================"
        echo "  Press Ctrl+C to exit"
        echo "  Next check in ${CHECK_INTERVAL} seconds..."
        echo "======================================"
        
        sleep $CHECK_INTERVAL
    done
}

# Trap Ctrl+C
trap 'echo ""; echo "Monitor stopped."; exit 0' INT

# Run monitor
monitor_loop