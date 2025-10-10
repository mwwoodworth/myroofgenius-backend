# Revenue System Endpoints Documentation

## Important: Endpoint Structure Clarification
The revenue system endpoints follow a specific structure that differs from typical REST conventions. This document serves as the authoritative reference for all revenue endpoints.

## Complete Endpoint List (v5.14)

### 1. Test Revenue Module
**Base Path**: `/api/v1/test-revenue`
- `GET /api/v1/test-revenue/` - System status and test endpoint

### 2. AI Estimation Module  
**Base Path**: `/api/v1/ai-estimation`
- `POST /api/v1/ai-estimation/competitor-analysis` - Analyze competitors in area
- `POST /api/v1/ai-estimation/generate-estimate` - Generate AI-powered estimate
- `POST /api/v1/ai-estimation/photo-analysis` - Analyze roof photos

### 3. Stripe Revenue Module
**Base Path**: `/api/v1/stripe-revenue`
- `POST /api/v1/stripe-revenue/create-checkout-session` - Create Stripe checkout
- `POST /api/v1/stripe-revenue/create-subscription` - Create subscription
- `POST /api/v1/stripe-revenue/webhook` - Handle Stripe webhooks
- `GET /api/v1/stripe-revenue/dashboard-metrics` - Get revenue metrics
- `POST /api/v1/stripe-revenue/cancel-subscription` - Cancel subscription

### 4. Customer Pipeline Module
**Base Path**: `/api/v1/customer-pipeline`
- `POST /api/v1/customer-pipeline/capture-lead` - Capture new lead
- `POST /api/v1/customer-pipeline/nurture-sequence/{lead_id}` - Start nurture sequence
- `GET /api/v1/customer-pipeline/lead-analytics` - Get lead analytics
- `POST /api/v1/customer-pipeline/upsell-opportunity/{customer_id}` - Create upsell

### 5. Landing Pages Module
**Base Path**: `/api/v1/landing-pages`
- `GET /api/v1/landing-pages/estimate-now` - Estimate landing page (HTML)
- `GET /api/v1/landing-pages/ai-analyzer` - AI analyzer landing page (HTML)
- `POST /api/v1/landing-pages/capture` - Capture lead from landing page
- `GET /api/v1/landing-pages/templates` - Get landing page templates

### 6. Google Ads Automation Module
**Base Path**: `/api/v1/google-ads`
- `POST /api/v1/google-ads/campaigns` - Create campaign
- `GET /api/v1/google-ads/campaigns` - List campaigns
- `POST /api/v1/google-ads/keywords/{campaign_id}` - Add keywords
- `GET /api/v1/google-ads/performance/{campaign_id}` - Get performance

### 7. Revenue Dashboard Module
**Base Path**: `/api/v1/revenue-dashboard`
- `GET /api/v1/revenue-dashboard/dashboard-metrics` - Get dashboard metrics
- `GET /api/v1/revenue-dashboard/live-feed` - Get live revenue feed
- `GET /api/v1/revenue-dashboard/hourly-performance` - Hourly performance
- `GET /api/v1/revenue-dashboard/real-time` - Real-time metrics

## Known Issues

### Database Schema Issues
Some endpoints return database errors due to missing columns:
- `revenue_tracking` table missing `amount_cents` column
- Some tables referenced in code don't exist yet

### Authentication
Currently, these endpoints don't require authentication (for testing). Production deployment should add auth middleware.

## Testing Endpoints

### Quick Test Commands
```bash
# Test revenue status
curl https://brainops-backend-prod.onrender.com/api/v1/test-revenue/

# Test AI estimation (requires JSON body)
curl -X POST https://brainops-backend-prod.onrender.com/api/v1/ai-estimation/competitor-analysis \
  -H "Content-Type: application/json" \
  -d '{"zip_code": "80202", "service_type": "roofing"}'

# Test Stripe metrics
curl https://brainops-backend-prod.onrender.com/api/v1/stripe-revenue/dashboard-metrics

# Test customer pipeline
curl https://brainops-backend-prod.onrender.com/api/v1/customer-pipeline/lead-analytics
```

## Monitoring Script Update
The `render_monitor.py` script has been updated to test the correct endpoints. Previous versions tested non-existent paths like `/api/v1/stripe-revenue/products` which don't exist.

## Next Steps
1. Fix database schema issues (add missing columns)
2. Add authentication to all revenue endpoints
3. Configure Stripe webhook secret
4. Set up SendGrid API key for email sending
5. Implement Google Ads API integration

## Version History
- v5.13: Initial deployment with route conflicts
- v5.14: Fixed route prefixes, all endpoints accessible

Last Updated: 2025-08-18