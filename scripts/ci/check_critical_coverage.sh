#!/usr/bin/env bash
# CI gate: verify coverage floors for critical modules.
# Run: bash scripts/ci/check_critical_coverage.sh

set -euo pipefail

cd "$(dirname "$0")/../.."

echo "=== Critical Module Coverage Gate ==="

declare -A FLOORS=(
    ["core/brain_store.py"]=70
    ["middleware/authentication.py"]=40
    ["routes/stripe_webhooks.py"]=20
    ["brainops_ai_os/awareness_system.py"]=20
    ["brainops_ai_os/metacognitive_controller.py"]=15
)

FAILED=0

for module in "${!FLOORS[@]}"; do
    floor=${FLOORS[$module]}

    coverage=$(python3 -m pytest \
        --cov="$module" \
        --cov-report=term \
        -q tests/ 2>&1 \
        | grep -E "^${module}" \
        | awk '{print $NF}' \
        | tr -d '%' || echo "0")

    if [ -z "$coverage" ] || [ "$coverage" = "0" ]; then
        echo "FAIL: $module — coverage=0% (floor=${floor}%)"
        FAILED=1
    elif [ "$coverage" -lt "$floor" ]; then
        echo "FAIL: $module — coverage=${coverage}% < floor=${floor}%"
        FAILED=1
    else
        echo "PASS: $module — coverage=${coverage}% >= floor=${floor}%"
    fi
done

echo ""
if [ "$FAILED" -eq 1 ]; then
    echo "COVERAGE GATE FAILED — critical modules below floor"
    exit 1
else
    echo "COVERAGE GATE PASSED"
fi
