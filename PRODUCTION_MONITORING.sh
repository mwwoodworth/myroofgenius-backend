#!/bin/bash
#
# PRODUCTION MONITORING SCRIPT
# Tests all core business endpoints in production
# Run this before/after any deployment to verify system health
#

TOKEN="${SUPABASE_JWT_TOKEN:-<JWT_REDACTED>}"
BASE="https://brainops-backend-prod.onrender.com"

PASS=0
FAIL=0
ERROR=0

test_endpoint() {
  local ep=$1
  local label=$2

  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE$ep" --max-time 10 2>/dev/null)

  printf "  %-55s" "$label:"
  if [ "$HTTP" = "200" ]; then
    echo "✅ 200"
    ((PASS++))
    return 0
  elif [ "$HTTP" = "500" ] || [ "$HTTP" = "502" ] || [ "$HTTP" = "503" ]; then
    echo "❌ $HTTP - SERVER ERROR"
    ((ERROR++))
    return 1
  else
    echo "⚠️  $HTTP"
    ((FAIL++))
    return 2
  fi
}

echo "═══════════════════════════════════════════════════════════════"
echo "PRODUCTION HEALTH CHECK - $(date)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Get version
VERSION=$(curl -s "$BASE/health" 2>/dev/null | jq -r '.version // "unknown"')
echo "Version: $VERSION"
echo ""

echo "🔹 CRITICAL BUSINESS ENDPOINTS"
echo "────────────────────────────────────────────────"
test_endpoint "/api/v1/complete-erp/customers" "Customers Management"
test_endpoint "/api/v1/complete-erp/jobs" "Jobs Management"
test_endpoint "/api/v1/complete-erp/estimates" "Estimates Management"
test_endpoint "/api/v1/complete-erp/invoices" "Invoices Management"
test_endpoint "/api/v1/complete-erp/inventory/items" "Inventory Items"
test_endpoint "/api/v1/complete-erp/schedules" "Scheduling"
test_endpoint "/api/v1/complete-erp/reports/dashboard" "Reports Dashboard"
test_endpoint "/api/v1/complete-erp/ar-aging" "AR Aging Report"
echo ""

echo "🔹 CRM ENDPOINTS"
echo "────────────────────────────────────────────────"
test_endpoint "/api/v1/crm/customers" "CRM Customers"
test_endpoint "/api/v1/crm/jobs" "CRM Jobs"
test_endpoint "/api/v1/crm/estimates" "CRM Estimates"
test_endpoint "/api/v1/crm/invoices" "CRM Invoices"
echo ""

echo "🔹 AI & MONITORING"
echo "────────────────────────────────────────────────"
test_endpoint "/api/v1/ai/system-health" "AI System Health"
test_endpoint "/api/v1/complete-erp/monitoring/health" "System Monitoring"
test_endpoint "/api/v1/complete-erp/monitoring/operational-status" "Operational Status"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "SUMMARY:"
echo "  ✅ Working: $PASS"
echo "  ❌ Errors:  $ERROR"
echo "  ⚠️  Other:   $FAIL"
TOTAL=$((PASS + ERROR + FAIL))
if [ $TOTAL -gt 0 ]; then
  SUCCESS_RATE=$((PASS * 100 / TOTAL))
  echo "  Success Rate: $SUCCESS_RATE%"
fi
echo "═══════════════════════════════════════════════════════════════"

if [ $ERROR -gt 0 ]; then
  echo ""
  echo "🚨 CRITICAL: $ERROR core endpoints failing!"
  echo "   System requires immediate attention."
  exit 1
elif [ $PASS -ge 12 ]; then
  echo ""
  echo "✅ SYSTEM OPERATIONAL"
  exit 0
else
  echo ""
  echo "⚠️  WARNING: Limited functionality"
  exit 2
fi
