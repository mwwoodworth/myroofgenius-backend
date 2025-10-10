#\!/bin/bash
echo "🚀 COMPLETE SYSTEM HEALTH CHECK"
echo "==============================="
echo ""

# Check Frontend
echo "1️⃣ FRONTEND STATUS:"
echo -n "   MyRoofGenius.com: "
FRONTEND_CODE=$(curl -L -s -o /dev/null -w "%{http_code}" https://myroofgenius.com)
if [ "$FRONTEND_CODE" -eq 200 ]; then
    echo "✅ OPERATIONAL (HTTP $FRONTEND_CODE)"
else
    echo "❌ ERROR (HTTP $FRONTEND_CODE)"
fi

# Check Backend API
echo ""
echo "2️⃣ BACKEND API STATUS:"
echo -n "   Health Check: "
HEALTH_RESPONSE=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health 2>/dev/null)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ HEALTHY"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "❌ UNHEALTHY or UNREACHABLE"
fi

# Check Critical Endpoints
echo ""
echo "3️⃣ CRITICAL ENDPOINTS:"
endpoints=(
    "https://brainops-backend-prod.onrender.com/docs:API Documentation"
    "https://brainops-backend-prod.onrender.com/api/v1/auth/login:Auth Login (405 expected)"
    "https://brainops-backend-prod.onrender.com/api/v1/memory/recent:Memory API (401 expected)"
    "https://myroofgenius.com/api/health:Frontend API Health"
)

for endpoint in "${endpoints[@]}"; do
    IFS=':' read -r url desc <<< "$endpoint"
    echo -n "   $desc: "
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [[ "$desc" == *"405 expected"* && "$code" == "405" ]]; then
        echo "✅ CORRECT ($code)"
    elif [[ "$desc" == *"401 expected"* && "$code" == "401" ]]; then
        echo "✅ CORRECT ($code)"
    elif [ "$code" -eq 200 ]; then
        echo "✅ OK ($code)"
    else
        echo "❌ ERROR ($code)"
    fi
done

# Check Database via Backend
echo ""
echo "4️⃣ DATABASE STATUS:"
DB_STATUS=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health | grep -o '"database":"[^"]*"' | cut -d'"' -f4)
if [ -n "$DB_STATUS" ]; then
    echo "   Status: $DB_STATUS"
else
    echo "   Status: Unable to determine"
fi

# Check Docker Registry
echo ""
echo "5️⃣ DOCKER REGISTRY:"
echo -n "   Latest Image: "
curl -s https://hub.docker.com/v2/repositories/mwwoodworth/brainops-backend/tags/ | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "Unable to fetch"

echo ""
echo "==============================="
date
