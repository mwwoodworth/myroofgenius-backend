-- Fix All Revenue System Database Issues
-- Version: v5.15
-- Date: 2025-08-18

-- 1. Fix revenue_tracking table
ALTER TABLE revenue_tracking 
ADD COLUMN IF NOT EXISTS amount_cents BIGINT DEFAULT 0;

ALTER TABLE revenue_tracking
ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255);

ALTER TABLE revenue_tracking
ADD COLUMN IF NOT EXISTS stripe_payment_id VARCHAR(255);

ALTER TABLE revenue_tracking
ADD COLUMN IF NOT EXISTS subscription_id VARCHAR(255);

ALTER TABLE revenue_tracking
ADD COLUMN IF NOT EXISTS date DATE DEFAULT CURRENT_DATE;

ALTER TABLE revenue_tracking
ADD COLUMN IF NOT EXISTS source VARCHAR(50);

-- 2. Create checkout_sessions table if missing
CREATE TABLE IF NOT EXISTS checkout_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    price_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    amount_total BIGINT
);

-- 3. Create or fix subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    customer_id VARCHAR(255),
    customer_email VARCHAR(255),
    price_id VARCHAR(255),
    plan_name VARCHAR(255),
    price_cents BIGINT,
    status VARCHAR(50),
    trial_end TIMESTAMP,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    canceled_at TIMESTAMP,
    cancellation_reason TEXT
);

-- 4. Create google_ads_campaigns table
CREATE TABLE IF NOT EXISTS google_ads_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(255) UNIQUE,
    name VARCHAR(255) NOT NULL,
    budget_cents BIGINT,
    status VARCHAR(50) DEFAULT 'draft',
    target_location VARCHAR(255),
    keywords TEXT[],
    ad_copy JSONB,
    performance_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 5. Create lead_analytics table
CREATE TABLE IF NOT EXISTS lead_analytics (
    id SERIAL PRIMARY KEY,
    lead_id VARCHAR(255),
    source VARCHAR(100),
    conversion_rate DECIMAL(5,2),
    engagement_score INTEGER,
    nurture_stage VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Create landing_page_analytics table
CREATE TABLE IF NOT EXISTS landing_page_analytics (
    id SERIAL PRIMARY KEY,
    page_name VARCHAR(255),
    variant VARCHAR(50),
    views INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,2),
    date DATE DEFAULT CURRENT_DATE
);

-- 7. Ensure leads table has all required columns
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 8. Add any missing columns to existing tables
ALTER TABLE leads
ADD COLUMN IF NOT EXISTS engagement_score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_activity TIMESTAMP,
ADD COLUMN IF NOT EXISTS nurture_sequence_id VARCHAR(255);

-- 9. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_revenue_tracking_date ON revenue_tracking(date);
CREATE INDEX IF NOT EXISTS idx_revenue_tracking_customer ON revenue_tracking(customer_email);
CREATE INDEX IF NOT EXISTS idx_checkout_sessions_status ON checkout_sessions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);

-- 10. Insert some test data to verify
INSERT INTO revenue_tracking (amount_cents, customer_email, source, date)
VALUES (9999, 'test@example.com', 'test', CURRENT_DATE)
ON CONFLICT DO NOTHING;

-- Verify tables exist
SELECT 'revenue_tracking' as table_name, COUNT(*) as count FROM revenue_tracking
UNION ALL
SELECT 'checkout_sessions', COUNT(*) FROM checkout_sessions
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'google_ads_campaigns', COUNT(*) FROM google_ads_campaigns
UNION ALL
SELECT 'leads', COUNT(*) FROM leads;