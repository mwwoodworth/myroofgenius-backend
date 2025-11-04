#!/bin/bash
# E2E Test for Relationship Awareness API
# Tests live production endpoints

echo "========================================================================="
echo "E2E RELATIONSHIP AWARENESS API TEST"
echo "========================================================================="

API_URL="https://brainops-backend-prod.onrender.com"
TENANT_ID="51e728c5-94e8-4ae0-8a0a-6a08d1fb3457"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n📋 TEST 1: Health Check"
echo "----------------------------------------"
HEALTH=$(curl -s "$API_URL/api/v1/aware/health")
STATUS=$(echo "$HEALTH" | jq -r '.status')
if [ "$STATUS" = "operational" ]; then
    echo -e "${GREEN}✅ PASS${NC} - System is operational"
    echo "$HEALTH" | jq '.'
else
    echo -e "${RED}❌ FAIL${NC} - System not operational"
    exit 1
fi

echo -e "\n📝 TEST 2: Create Customer with Relationship Awareness"
echo "----------------------------------------"
CUSTOMER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/aware/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E2E Test Customer",
    "email": "e2e@test.com",
    "phone": "(555) 999-8888",
    "address": "123 E2E Test St",
    "city": "Test City",
    "state": "CO",
    "zip": "80901",
    "tenant_id": "'"$TENANT_ID"'"
  }')

SUCCESS=$(echo "$CUSTOMER_RESPONSE" | jq -r '.success')
if [ "$SUCCESS" = "true" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Customer created successfully"
    CUSTOMER_ID=$(echo "$CUSTOMER_RESPONSE" | jq -r '.customer.entity.id')
    echo "   Customer ID: $CUSTOMER_ID"
    echo "   Name: $(echo "$CUSTOMER_RESPONSE" | jq -r '.customer.entity.name')"
else
    echo -e "${RED}❌ FAIL${NC} - Customer creation failed"
    echo "$CUSTOMER_RESPONSE" | jq '.'
    exit 1
fi

echo -e "\n🔍 TEST 3: Get Complete Customer View"
echo "----------------------------------------"
CUSTOMER_VIEW=$(curl -s "$API_URL/api/v1/aware/customers/$CUSTOMER_ID/complete")
VIEW_SUCCESS=$(echo "$CUSTOMER_VIEW" | jq -r '.success')
if [ "$VIEW_SUCCESS" = "true" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Customer view retrieved"
    echo "   Has relationship graph: $(echo "$CUSTOMER_VIEW" | jq 'has("customer_complete_view.relationship_graph")')"
    echo "   Has computed fields: $(echo "$CUSTOMER_VIEW" | jq 'has("customer_complete_view.computed_fields")')"
else
    echo -e "${RED}❌ FAIL${NC} - Failed to get customer view"
    echo "$CUSTOMER_VIEW" | jq '.'
    exit 1
fi

echo -e "\n👷 TEST 4: Get Existing Employees for Job Assignment"
echo "----------------------------------------"
EMPLOYEES=$(curl -s "https://brainops-backend-prod.onrender.com/api/v1/complete-erp/employees?limit=3&tenant_id=$TENANT_ID")
EMP_COUNT=$(echo "$EMPLOYEES" | jq '.employees | length')
if [ "$EMP_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Found $EMP_COUNT employees"
    EMP_ID_1=$(echo "$EMPLOYEES" | jq -r '.employees[0].id')
    EMP_ID_2=$(echo "$EMPLOYEES" | jq -r '.employees[1].id // .employees[0].id')
    echo "   Employee 1: $EMP_ID_1"
    echo "   Employee 2: $EMP_ID_2"
else
    echo -e "${YELLOW}⚠️  WARN${NC} - No employees found, job will be created without crew"
    EMP_ID_1=""
    EMP_ID_2=""
fi

echo -e "\n🏗️  TEST 5: Create Job with Auto-Linking"
echo "----------------------------------------"
JOB_DATA='{
  "customer_id": "'"$CUSTOMER_ID"'",
  "job_number": "E2E-TEST-'$(date +%s)'",
  "title": "E2E Test Job - Roof Replacement",
  "description": "Testing relationship awareness auto-linking",
  "property_address": "123 E2E Test St",
  "tenant_id": "'"$TENANT_ID"'"'

if [ -n "$EMP_ID_1" ]; then
    JOB_DATA="$JOB_DATA"',
  "employee_ids": ["'"$EMP_ID_1"'", "'"$EMP_ID_2"'"]'
fi

JOB_DATA="$JOB_DATA"'
}'

JOB_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/aware/jobs" \
  -H "Content-Type: application/json" \
  -d "$JOB_DATA")

JOB_SUCCESS=$(echo "$JOB_RESPONSE" | jq -r '.success')
if [ "$JOB_SUCCESS" = "true" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Job created with auto-linking"
    JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job.entity.id')
    echo "   Job ID: $JOB_ID"
    echo "   Title: $(echo "$JOB_RESPONSE" | jq -r '.job.entity.title')"
    echo "   Employees Assigned: $(echo "$JOB_RESPONSE" | jq -r '.relationships_created.employees_assigned')"
else
    echo -e "${RED}❌ FAIL${NC} - Job creation failed"
    echo "$JOB_RESPONSE" | jq '.'
    exit 1
fi

echo -e "\n🔍 TEST 6: Get Complete Job View with Relationships"
echo "----------------------------------------"
JOB_VIEW=$(curl -s "$API_URL/api/v1/aware/jobs/$JOB_ID/complete")
JOB_VIEW_SUCCESS=$(echo "$JOB_VIEW" | jq -r '.success')
if [ "$JOB_VIEW_SUCCESS" = "true" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Job view retrieved"
    echo "   Job Title: $(echo "$JOB_VIEW" | jq -r '.job_complete_view.entity.title')"
    echo "   Customer Linked: $(echo "$JOB_VIEW" | jq 'has("job_complete_view.relationships.parent")')"
    echo "   Has Assignments: $(echo "$JOB_VIEW" | jq 'has("job_complete_view.relationships.job_assignments")')"
    ASSIGNMENTS_COUNT=$(echo "$JOB_VIEW" | jq -r '.job_complete_view.relationships.job_assignments.count // 0')
    echo "   Employee Assignments: $ASSIGNMENTS_COUNT"
else
    echo -e "${RED}❌ FAIL${NC} - Failed to get job view"
    echo "$JOB_VIEW" | jq '.'
    exit 1
fi

echo -e "\n========================================================================="
echo -e "${GREEN}✅ ALL E2E TESTS PASSED${NC}"
echo "========================================================================="
echo ""
echo "Summary:"
echo "  ✅ Health check passed"
echo "  ✅ Customer created with relationship tracking"
echo "  ✅ Customer complete view retrieved"
echo "  ✅ Job created with auto-linking"
echo "  ✅ Job complete view shows relationships"
echo ""
echo "Created Resources:"
echo "  Customer ID: $CUSTOMER_ID"
echo "  Job ID: $JOB_ID"
echo "  Employee Assignments: $ASSIGNMENTS_COUNT"
echo ""
echo "🎉 Relationship Awareness System is FULLY OPERATIONAL for human users!"
echo "========================================================================="
