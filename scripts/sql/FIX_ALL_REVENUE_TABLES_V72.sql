-- FIX ALL REVENUE TABLES FOR PRODUCTION
-- This ensures all tables exist and have correct columns

-- 1. Revenue Tracking Table (core)
CREATE TABLE IF NOT EXISTS revenue_tracking (
    id SERIAL PRIMARY KEY,
    amount_cents BIGINT NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    source VARCHAR(100) NOT NULL,
    customer_id INTEGER,
    transaction_id VARCHAR(255) UNIQUE,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add missing column if table exists but column doesn't
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='revenue_tracking' AND column_name='amount_cents') THEN
        ALTER TABLE revenue_tracking ADD COLUMN amount_cents BIGINT NOT NULL DEFAULT 0;
    END IF;
END $$;

-- 2. Stripe Customers
CREATE TABLE IF NOT EXISTS stripe_customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Stripe Subscriptions
CREATE TABLE IF NOT EXISTS stripe_subscriptions (
    id SERIAL PRIMARY KEY,
    subscription_id VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    amount_cents BIGINT NOT NULL DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    product_id VARCHAR(255),
    price_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Customer Pipeline
CREATE TABLE IF NOT EXISTS customer_pipeline (
    id SERIAL PRIMARY KEY,
    lead_id VARCHAR(100) UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    stage VARCHAR(50) DEFAULT 'new',
    score INTEGER DEFAULT 0,
    estimated_value_cents BIGINT DEFAULT 0,
    source VARCHAR(100),
    assigned_to VARCHAR(255),
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    contacted_at TIMESTAMP WITH TIME ZONE,
    converted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. AI Estimates
CREATE TABLE IF NOT EXISTS ai_estimates (
    id SERIAL PRIMARY KEY,
    estimate_id VARCHAR(100) UNIQUE NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    roof_type VARCHAR(100),
    desired_material VARCHAR(100),
    roof_size_sqft INTEGER,
    total_cost_cents BIGINT NOT NULL DEFAULT 0,
    material_cost_cents BIGINT DEFAULT 0,
    labor_cost_cents BIGINT DEFAULT 0,
    timeline_days INTEGER,
    confidence_score DECIMAL(3,2),
    ai_insights JSONB DEFAULT '[]',
    breakdown JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Landing Page Conversions
CREATE TABLE IF NOT EXISTS landing_page_conversions (
    id SERIAL PRIMARY KEY,
    page_id VARCHAR(100),
    visitor_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    referrer TEXT,
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    conversion_type VARCHAR(50),
    conversion_value_cents BIGINT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Google Ads Campaigns
CREATE TABLE IF NOT EXISTS google_ads_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(100) UNIQUE,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    budget_cents BIGINT DEFAULT 0,
    spent_cents BIGINT DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    conversion_value_cents BIGINT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Revenue Dashboard Metrics
CREATE TABLE IF NOT EXISTS revenue_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value DECIMAL(15,2) DEFAULT 0,
    count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, metric_type)
);

-- 9. Automated Tasks
CREATE TABLE IF NOT EXISTS automated_tasks (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    result JSONB DEFAULT '{}',
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Webhook Events
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE,
    source VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_revenue_tracking_created_at ON revenue_tracking(created_at);
CREATE INDEX IF NOT EXISTS idx_revenue_tracking_customer_id ON revenue_tracking(customer_id);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_customer_id ON stripe_subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_pipeline_stage ON customer_pipeline(stage);
CREATE INDEX IF NOT EXISTS idx_ai_estimates_customer_email ON ai_estimates(customer_email);
CREATE INDEX IF NOT EXISTS idx_automated_tasks_status ON automated_tasks(status);
CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON webhook_events(processed);

-- Insert sample data to verify tables work
INSERT INTO revenue_metrics (date, metric_type, value, count)
VALUES (CURRENT_DATE, 'daily_revenue', 0, 0)
ON CONFLICT (date, metric_type) DO NOTHING;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Success message
SELECT 'SUCCESS: All revenue tables created/fixed' as status,
       COUNT(*) as tables_ready
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'revenue_tracking', 'stripe_customers', 'stripe_subscriptions',
    'customer_pipeline', 'ai_estimates', 'landing_page_conversions',
    'google_ads_campaigns', 'revenue_metrics', 'automated_tasks',
    'webhook_events'
);