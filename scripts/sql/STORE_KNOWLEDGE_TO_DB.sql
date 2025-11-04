-- Store deployment knowledge in production database
-- Document v5.10 deployment and revenue strategy

-- Create deployment knowledge table
CREATE TABLE IF NOT EXISTS deployment_knowledge (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL,
    deployment_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50),
    success_rate DECIMAL(5,2),
    critical_fixes JSONB,
    test_results JSONB,
    revenue_status JSONB,
    next_steps JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document v5.10 deployment
INSERT INTO deployment_knowledge 
(version, status, success_rate, critical_fixes, test_results, revenue_status, next_steps)
VALUES (
    'v5.10',
    'FULLY_OPERATIONAL',
    100.0,
    '{
        "main_py_error": "Removed router code before app initialization",
        "dockerfile_fix": "Fixed COPY order - main_v504.py explicitly copied as main.py",
        "public_routes": "Added /api/v1/products/public and /api/v1/aurea/public",
        "error_resolution": "Attribute app not found fixed by proper file ordering"
    }'::jsonb,
    '{
        "total_tests": 14,
        "successful": 14,
        "failed": 0,
        "endpoints_tested": [
            "/api/v1/health",
            "/api/v1/database/status",
            "/api/v1/marketplace/products",
            "/api/v1/aurea/public/status",
            "/api/v1/automations",
            "/api/v1/agents",
            "/api/v1/payments/create-intent"
        ]
    }'::jsonb,
    '{
        "marketplace_ready": true,
        "payment_processing": "Stripe integrated",
        "public_api_access": true,
        "current_monthly_revenue": 0,
        "potential_sources": [
            "Product marketplace sales",
            "Subscription plans",
            "AI consultation services",
            "Roofing estimates automation"
        ],
        "revenue_targets": {
            "month_1": 5000,
            "month_3": 25000,
            "month_6": 100000
        }
    }'::jsonb,
    '{
        "immediate": [
            "Enable Stripe live mode",
            "Add real products to marketplace",
            "Launch marketing campaign",
            "Set up analytics tracking"
        ],
        "revenue_generation": [
            "Premium AI estimation tools ($49.99/month)",
            "Contractor dashboard ($99.99/month)",
            "Lead generation service ($0.25/lead)",
            "White-label solutions ($499/month)"
        ]
    }'::jsonb
);

-- Create operational procedures table
CREATE TABLE IF NOT EXISTS operational_procedures (
    id SERIAL PRIMARY KEY,
    procedure_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    steps JSONB,
    tools_required JSONB,
    critical_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Document critical procedures
INSERT INTO operational_procedures 
(procedure_name, category, steps, tools_required, critical_notes)
VALUES 
(
    'Emergency Docker Deployment Fix',
    'deployment',
    '[
        "1. Identify build error in Render logs",
        "2. Check main.py for initialization order issues",
        "3. Create emergency Dockerfile with explicit COPY",
        "4. Build with --no-cache flag",
        "5. Test locally with docker run verification",
        "6. Push to Docker Hub with version tag",
        "7. Trigger Render deployment with cache clear"
    ]'::jsonb,
    '["Docker", "Render CLI", "curl for webhook"]'::jsonb,
    'ALWAYS copy main_v504.py as /app/main.py explicitly'
),
(
    'Revenue System Activation',
    'revenue',
    '[
        "1. Verify Stripe API keys in environment",
        "2. Create products in database",
        "3. Set up Stripe products and prices",
        "4. Enable payment intent endpoints",
        "5. Test checkout flow end-to-end",
        "6. Monitor first transactions",
        "7. Set up revenue tracking dashboard"
    ]'::jsonb,
    '["Stripe Dashboard", "Supabase", "Monitoring tools"]'::jsonb,
    'Start with test mode, validate, then switch to live'
),
(
    'Supabase Optimization Strategy',
    'optimization',
    '[
        "1. Use Supabase CLI for migrations instead of manual SQL",
        "2. Enable Row Level Security on all tables",
        "3. Use Realtime subscriptions for live updates",
        "4. Implement Edge Functions for serverless compute",
        "5. Use Storage API for file management",
        "6. Enable pgvector for AI embeddings",
        "7. Set up branching for dev/staging/prod"
    ]'::jsonb,
    '["Supabase CLI", "GitHub Actions", "Edge Runtime"]'::jsonb,
    'Supabase CLI enables local development with automatic migrations'
)
ON CONFLICT (procedure_name) DO UPDATE
SET 
    steps = EXCLUDED.steps,
    tools_required = EXCLUDED.tools_required,
    critical_notes = EXCLUDED.critical_notes,
    updated_at = NOW();

-- Create revenue tracking table
CREATE TABLE IF NOT EXISTS revenue_tracking (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    source VARCHAR(100),
    amount_cents INTEGER,
    customer_count INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create product pricing strategy
CREATE TABLE IF NOT EXISTS pricing_strategy (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255),
    tier VARCHAR(50),
    monthly_price_cents INTEGER,
    features JSONB,
    target_audience TEXT,
    expected_conversions INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert MyRoofGenius pricing tiers
INSERT INTO pricing_strategy 
(product_name, tier, monthly_price_cents, features, target_audience, expected_conversions)
VALUES
(
    'AI Estimator Basic',
    'basic',
    4999,
    '[
        "10 estimates per month",
        "Basic material calculations",
        "PDF export",
        "Email support"
    ]'::jsonb,
    'Small contractors, startups',
    50
),
(
    'AI Estimator Pro',
    'professional',
    9999,
    '[
        "Unlimited estimates",
        "Advanced AI analysis",
        "Photo analysis",
        "Labor calculations",
        "Priority support",
        "Custom branding"
    ]'::jsonb,
    'Established contractors',
    20
),
(
    'Enterprise Suite',
    'enterprise',
    49900,
    '[
        "Everything in Pro",
        "Multi-user access",
        "API access",
        "White-label options",
        "Dedicated support",
        "Custom integrations",
        "Training included"
    ]'::jsonb,
    'Large roofing companies',
    5
);

-- Summary query
SELECT 
    'Deployment Knowledge Stored' as status,
    COUNT(*) as procedures_documented,
    (SELECT COUNT(*) FROM pricing_strategy) as pricing_tiers,
    (SELECT SUM(monthly_price_cents * expected_conversions) / 100 FROM pricing_strategy) as potential_monthly_revenue
FROM operational_procedures;
