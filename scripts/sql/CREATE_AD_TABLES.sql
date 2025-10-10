-- Create ad campaign tables for Google Ads automation

CREATE TABLE IF NOT EXISTS ad_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50) UNIQUE,
    platform VARCHAR(20),
    name VARCHAR(255),
    budget_daily_cents INTEGER,
    target_cpa_cents INTEGER,
    keywords JSONB,
    locations JSONB,
    ad_schedule JSONB,
    status VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ad_performance (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50),
    date DATE,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    spend_cents INTEGER DEFAULT 0,
    cpc_cents INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ad_perf_campaign ON ad_performance(campaign_id, date);

-- Also create subscriptions table if missing
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    customer_id VARCHAR(255),
    customer_email VARCHAR(255),
    price_id VARCHAR(255),
    status VARCHAR(50),
    trial_end TIMESTAMP,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    metadata JSONB,
    canceled_at TIMESTAMP,
    cancellation_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_customer ON subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON subscriptions(customer_email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);