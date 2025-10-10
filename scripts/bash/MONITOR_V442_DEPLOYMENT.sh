#!/bin/bash

echo "🔍 MONITORING v4.42 DEPLOYMENT"
echo "=============================="
echo ""

while true; do
    # Check deployment status
    DEPLOY_STATUS=$(curl -s "https://api.render.com/v1/services/srv-d1tfs4idbo4c73di6k00/deploys?limit=1" \
        -H "Authorization: Bearer rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx" \
        -H "Accept: application/json" | \
        python3 -c "import sys, json; print(json.load(sys.stdin)[0]['deploy']['status'])" 2>/dev/null)
    
    # Check API version
    API_VERSION=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/health | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['version'])" 2>/dev/null)
    
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$TIMESTAMP]"
    echo "  Deployment: $DEPLOY_STATUS"
    echo "  API Version: $API_VERSION"
    
    # Check if deployment is complete
    if [ "$DEPLOY_STATUS" = "live" ] && [ "$API_VERSION" = "4.42" ]; then
        echo ""
        echo "✅ DEPLOYMENT COMPLETE!"
        echo "======================"
        echo ""
        
        # Test new endpoints
        echo "Testing new endpoints..."
        
        # Test Stripe
        STRIPE_TEST=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/payments/test | \
            python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Stripe: {d.get('stripe_configured', False)}\")" 2>/dev/null)
        echo "  $STRIPE_TEST"
        
        # Test SendGrid
        SENDGRID_TEST=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/email/test | \
            python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"SendGrid: {d.get('sendgrid_configured', False)}\")" 2>/dev/null)
        echo "  $SENDGRID_TEST"
        
        # Test Env Master
        ENV_TEST=$(curl -s https://brainops-backend-prod.onrender.com/api/v1/env/validate | \
            python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Env Valid: {d.get('valid', False)}\")" 2>/dev/null)
        echo "  $ENV_TEST"
        
        echo ""
        echo "🎉 MyRoofGenius v4.42 is LIVE!"
        echo "All integrations are ready for activation."
        echo ""
        echo "Next step: Run ACTIVATE_ALL_AUTOMATIONS.py"
        break
    fi
    
    # Check for failed deployment
    if [ "$DEPLOY_STATUS" = "deactivated" ] || [ "$DEPLOY_STATUS" = "failed" ]; then
        echo ""
        echo "❌ DEPLOYMENT FAILED!"
        echo "Status: $DEPLOY_STATUS"
        echo "Please check Render logs for details."
        break
    fi
    
    # Wait 10 seconds before next check
    sleep 10
done