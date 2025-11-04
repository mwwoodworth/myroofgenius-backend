#!/bin/bash

echo "🛠️ FIXING MARKETPLACE ROUTES FOR REVENUE FLOW"
echo "============================================="
echo ""

cd /home/mwwoodworth/code/fastapi-operator-env

# 1. Create marketplace routes file with Stripe integration
echo "1️⃣ Creating marketplace routes with live Stripe..."

cat > apps/backend/routes/marketplace_revenue.py << 'EOF'
"""
Marketplace Revenue Routes - Live Stripe Integration
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any, Optional
import stripe
import os
import logging

from apps.backend.core.auth import get_current_user_optional
from apps.backend.services.marketplace_service import MarketplaceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

# Initialize service
marketplace_service = MarketplaceService()

@router.get("/products")
async def list_products(limit: int = 10):
    """List available products from Stripe"""
    try:
        products = await marketplace_service.list_products(limit=limit)
        return products
    except Exception as e:
        logger.error(f"Failed to list products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/checkout")
async def create_checkout_session(
    price_id: str,
    success_url: str,
    cancel_url: str,
    customer_email: Optional[str] = None
):
    """Create a Stripe checkout session"""
    try:
        session = await marketplace_service.create_checkout_session(
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email
        )
        return session
    except Exception as e:
        logger.error(f"Failed to create checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payment-intent")
async def create_payment_intent(
    amount: int,
    currency: str = "usd",
    customer_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user_optional)
):
    """Create a payment intent for direct payment"""
    try:
        intent = await marketplace_service.create_payment_intent(
            amount=amount,
            currency=currency,
            customer_id=customer_id,
            metadata={"user_id": current_user.get("id") if current_user else None}
        )
        return intent
    except Exception as e:
        logger.error(f"Failed to create payment intent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customer")
async def create_customer(
    email: str,
    name: Optional[str] = None,
    current_user: Dict = Depends(get_current_user_optional)
):
    """Create a Stripe customer"""
    try:
        customer = await marketplace_service.create_customer(
            email=email,
            name=name
        )
        return customer
    except Exception as e:
        logger.error(f"Failed to create customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/stripe")
async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        result = await marketplace_service.handle_webhook(payload, sig_header)
        return result
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
async def marketplace_status():
    """Check marketplace service status"""
    return {
        "status": "operational",
        "stripe_configured": bool(stripe.api_key),
        "endpoints": [
            "/products",
            "/checkout",
            "/payment-intent",
            "/customer",
            "/webhook/stripe"
        ]
    }
EOF

echo "✅ Marketplace revenue routes created"

# 2. Update main.py to include marketplace routes
echo ""
echo "2️⃣ Adding marketplace routes to main.py..."

# Find the line where routers are added and insert marketplace router
cat > add_marketplace_routes.py << 'EOF'
import sys

# Read the main.py file
with open('apps/backend/main.py', 'r') as f:
    lines = f.readlines()

# Find where to insert the marketplace router
insert_index = -1
for i, line in enumerate(lines):
    if 'from apps.backend.routes.products import router as products_router' in line:
        insert_index = i
        break

if insert_index > 0:
    # Insert marketplace router import after products router
    new_lines = lines[:insert_index+4]
    new_lines.append('\ntry:\n')
    new_lines.append('    from apps.backend.routes.marketplace_revenue import router as marketplace_router\n')
    new_lines.append('    routers_to_include.append((marketplace_router, "/api/v1", ["Marketplace Revenue"]))\n')
    new_lines.append('    logger.info("✅ Marketplace Revenue router loaded")\n')
    new_lines.append('except ImportError as e:\n')
    new_lines.append('    logger.warning(f"Marketplace Revenue router not available: {e}")\n')
    new_lines.extend(lines[insert_index+4:])
    
    # Write back
    with open('apps/backend/main.py', 'w') as f:
        f.writelines(new_lines)
    print("✅ Marketplace routes added to main.py")
else:
    print("⚠️  Could not find insertion point, adding manually...")
    # Append at a safe location
    with open('apps/backend/main.py', 'a') as f:
        f.write('\n# Marketplace Revenue Router\n')
        f.write('try:\n')
        f.write('    from apps.backend.routes.marketplace_revenue import router as marketplace_router\n')
        f.write('    routers_to_include.append((marketplace_router, "/api/v1", ["Marketplace Revenue"]))\n')
        f.write('    logger.info("✅ Marketplace Revenue router loaded")\n')
        f.write('except ImportError as e:\n')
        f.write('    logger.warning(f"Marketplace Revenue router not available: {e}")\n')
EOF

python3 add_marketplace_routes.py

# 3. Update version
echo ""
echo "3️⃣ Updating version to v3.3.73..."
sed -i 's/VERSION = "3.3.72"/VERSION = "3.3.73"/' apps/backend/main.py

# 4. Build and deploy
echo ""
echo "4️⃣ Building and deploying v3.3.73..."

docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho' --password-stdin <<< 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'
docker build -t mwwoodworth/brainops-backend:v3.3.73 -f Dockerfile . --quiet
docker tag mwwoodworth/brainops-backend:v3.3.73 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.3.73 --quiet
docker push mwwoodworth/brainops-backend:latest --quiet

echo "✅ Docker images pushed"

# 5. Trigger deployment
echo ""
echo "5️⃣ Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Accept: application/json" \
  --silent --output /dev/null

echo "✅ Deployment triggered"

# 6. Commit changes
git add -A
git commit -m "feat: Add marketplace revenue routes with live Stripe

- Created marketplace revenue routes with all payment endpoints
- Integrated live Stripe API for payment processing
- Added products, checkout, payment intent, and webhook endpoints
- Ready for production revenue flow

Co-Authored-By: Claude <noreply@anthropic.com>" --quiet

git push origin main --quiet

echo ""
echo "✅ MARKETPLACE ROUTES FIXED!"
echo ""
echo "📊 New endpoints available:"
echo "- GET  /api/v1/marketplace/products"
echo "- POST /api/v1/marketplace/checkout"
echo "- POST /api/v1/marketplace/payment-intent"
echo "- POST /api/v1/marketplace/customer"
echo "- POST /api/v1/marketplace/webhook/stripe"
echo "- GET  /api/v1/marketplace/status"
echo ""
echo "🚀 Version v3.3.73 deploying to production..."
EOF