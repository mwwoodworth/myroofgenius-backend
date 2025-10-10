# Stripe Webhook Configuration Guide

## Production Webhook Endpoint
```
https://brainops-backend-prod.onrender.com/api/v1/revenue/webhook/stripe
```

## Setup Instructions

### 1. Login to Stripe Dashboard
- Go to https://dashboard.stripe.com
- Navigate to Developers → Webhooks

### 2. Add Endpoint
- Click "Add endpoint"
- Enter the URL above
- Select events to listen for:
  - `checkout.session.completed`
  - `payment_intent.succeeded`
  - `invoice.paid`
  - `subscription.created`
  - `subscription.updated`
  - `subscription.deleted`

### 3. Get Webhook Secret
- After creating the endpoint, click on it
- Reveal the "Signing secret" (starts with `whsec_`)
- Copy this value

### 4. Add to Environment Variables
Add the webhook secret to the database:
```sql
INSERT INTO env_master (key, value, description, category, is_sensitive)
VALUES (
    'STRIPE_WEBHOOK_SECRET',
    'whsec_REDACTED_SECRET_HERE',
    'Stripe webhook endpoint signing secret',
    'stripe',
    true
);
```

## Testing the Webhook

### Using Stripe CLI
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward events to local endpoint (for testing)
stripe listen --forward-to https://brainops-backend-prod.onrender.com/api/v1/revenue/webhook/stripe

# Trigger test event
stripe trigger checkout.session.completed
```

### Manual Test
```python
import requests

webhook_data = {
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "id": "cs_test_123",
            "amount_total": 350000,
            "customer_email": "test@example.com"
        }
    }
}

response = requests.post(
    "https://brainops-backend-prod.onrender.com/api/v1/revenue/webhook/stripe",
    json=webhook_data
)

print(response.json())
```

## Current Status
- ✅ Webhook endpoint active at `/api/v1/revenue/webhook/stripe`
- ✅ Handler processing events successfully
- ⚠️ Webhook secret not configured (signature verification disabled)
- ✅ Mock responses working for testing

## Events Handled
1. **checkout.session.completed** - Payment successful
2. **payment_intent.succeeded** - Direct payment completed
3. **invoice.paid** - Invoice payment received
4. **subscription.created** - New subscription started

## Next Steps
1. Configure webhook in Stripe dashboard
2. Add webhook secret to env_master table
3. Enable signature verification in code
4. Test with real payments

## Support
For issues, check:
- Stripe Dashboard → Developers → Logs
- Backend logs at https://brainops-backend-prod.onrender.com/logs
- Test endpoint: https://brainops-backend-prod.onrender.com/api/v1/revenue/status