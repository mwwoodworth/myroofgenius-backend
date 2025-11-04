-- Complete Revenue System Tables
-- All tables needed for real revenue generation

-- Ad campaigns table
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

CREATE INDEX IF NOT EXISTS idx_ad_campaigns_status ON ad_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_ad_campaigns_platform ON ad_campaigns(platform);

-- Ad performance tracking
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

-- Enhanced revenue tracking
ALTER TABLE revenue_tracking ADD COLUMN IF NOT EXISTS campaign_id VARCHAR(50);
ALTER TABLE revenue_tracking ADD COLUMN IF NOT EXISTS utm_source VARCHAR(100);
ALTER TABLE revenue_tracking ADD COLUMN IF NOT EXISTS utm_medium VARCHAR(100);
ALTER TABLE revenue_tracking ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR(100);

-- Landing page performance
CREATE TABLE IF NOT EXISTS landing_page_views (
    id SERIAL PRIMARY KEY,
    page_url VARCHAR(255),
    visitor_id VARCHAR(100),
    variant VARCHAR(10),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    referrer TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_landing_views_page ON landing_page_views(page_url, created_at);
CREATE INDEX IF NOT EXISTS idx_landing_views_visitor ON landing_page_views(visitor_id);

-- Conversion events for tracking
CREATE TABLE IF NOT EXISTS conversion_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    customer_email VARCHAR(255),
    source VARCHAR(100),
    value_cents INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversion_type ON conversion_events(event_type);
CREATE INDEX IF NOT EXISTS idx_conversion_date ON conversion_events(created_at);

-- Email campaign performance
CREATE TABLE IF NOT EXISTS email_campaigns (
    id SERIAL PRIMARY KEY,
    campaign_id VARCHAR(50) UNIQUE,
    name VARCHAR(255),
    subject VARCHAR(255),
    template VARCHAR(100),
    segment VARCHAR(50),
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    conversion_count INTEGER DEFAULT 0,
    unsubscribe_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_email_campaign_sent ON email_campaigns(sent_at);

-- Referral program
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_email VARCHAR(255),
    referred_email VARCHAR(255),
    referral_code VARCHAR(50) UNIQUE,
    status VARCHAR(20) DEFAULT 'pending',
    reward_cents INTEGER DEFAULT 25000, -- $250 default
    paid_out BOOLEAN DEFAULT false,
    converted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_referral_code ON referrals(referral_code);
CREATE INDEX IF NOT EXISTS idx_referral_referrer ON referrals(referrer_email);

-- Partner/Affiliate tracking
CREATE TABLE IF NOT EXISTS partners (
    id SERIAL PRIMARY KEY,
    partner_id VARCHAR(50) UNIQUE,
    name VARCHAR(255),
    email VARCHAR(255),
    tier VARCHAR(20), -- tier1, tier2, tier3
    commission_rate DECIMAL(5,2), -- percentage
    total_referrals INTEGER DEFAULT 0,
    total_revenue_cents INTEGER DEFAULT 0,
    total_commission_cents INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partner_status ON partners(status);
CREATE INDEX IF NOT EXISTS idx_partner_tier ON partners(tier);

-- Weather event triggers
CREATE TABLE IF NOT EXISTS weather_triggers (
    id SERIAL PRIMARY KEY,
    location VARCHAR(255),
    event_type VARCHAR(50), -- hail, storm, hurricane, tornado
    severity VARCHAR(20), -- low, medium, high, extreme
    campaign_id VARCHAR(50),
    triggered_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_triggers(location, triggered_at);

-- Revenue goals tracking
CREATE TABLE IF NOT EXISTS revenue_goals (
    id SERIAL PRIMARY KEY,
    period_start DATE,
    period_end DATE,
    target_cents INTEGER,
    actual_cents INTEGER DEFAULT 0,
    lead_target INTEGER,
    lead_actual INTEGER DEFAULT 0,
    conversion_target DECIMAL(5,2),
    conversion_actual DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_revenue_goals_period ON revenue_goals(period_start, period_end);

-- Create or update the revenue dashboard materialized view
DROP MATERIALIZED VIEW IF EXISTS revenue_dashboard CASCADE;
CREATE MATERIALIZED VIEW revenue_dashboard AS
SELECT 
    DATE_TRUNC('day', created_at) as day,
    COUNT(DISTINCT customer_email) as unique_customers,
    SUM(amount_cents) / 100.0 as daily_revenue,
    COUNT(*) as transaction_count,
    AVG(amount_cents) / 100.0 as avg_transaction_value,
    STRING_AGG(DISTINCT source, ', ') as revenue_sources
FROM revenue_tracking
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day DESC;

CREATE INDEX IF NOT EXISTS idx_revenue_dashboard_day ON revenue_dashboard(day);

-- Function to calculate current week revenue progress
CREATE OR REPLACE FUNCTION get_revenue_progress()
RETURNS TABLE (
    week_number INTEGER,
    target_amount DECIMAL(10,2),
    current_amount DECIMAL(10,2),
    progress_percentage DECIMAL(5,2),
    days_remaining INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH current_week AS (
        SELECT 
            EXTRACT(WEEK FROM NOW() - '2025-08-18'::DATE)::INTEGER + 1 as week_num,
            CASE 
                WHEN EXTRACT(WEEK FROM NOW() - '2025-08-18'::DATE) + 1 = 1 THEN 2500
                WHEN EXTRACT(WEEK FROM NOW() - '2025-08-18'::DATE) + 1 = 2 THEN 7500
                WHEN EXTRACT(WEEK FROM NOW() - '2025-08-18'::DATE) + 1 <= 4 THEN 25000
                ELSE 25000
            END as target
    )
    SELECT 
        cw.week_num,
        cw.target,
        COALESCE(SUM(rt.amount_cents) / 100.0, 0) as current,
        COALESCE((SUM(rt.amount_cents) / 100.0) / cw.target * 100, 0) as progress,
        (7 - EXTRACT(DOW FROM NOW()))::INTEGER as days_left
    FROM current_week cw
    LEFT JOIN revenue_tracking rt ON rt.created_at >= '2025-08-18'::DATE
    GROUP BY cw.week_num, cw.target;
END;
$$ LANGUAGE plpgsql;

-- Insert initial revenue goals
INSERT INTO revenue_goals (period_start, period_end, target_cents, lead_target, conversion_target)
VALUES 
    ('2025-08-18', '2025-08-24', 250000, 50, 10.0),  -- Week 1: $2,500
    ('2025-08-25', '2025-08-31', 500000, 100, 15.0), -- Week 2: Additional $5,000
    ('2025-09-01', '2025-09-14', 1750000, 350, 14.3) -- Weeks 3-4: Additional $17,500
ON CONFLICT DO NOTHING;

-- Summary of setup
SELECT 
    'Revenue System Ready' as status,
    (SELECT COUNT(*) FROM information_schema.tables 
     WHERE table_name IN ('ad_campaigns', 'ad_performance', 'landing_page_views', 
                          'referrals', 'partners', 'weather_triggers')) as new_tables,
    (SELECT COUNT(*) FROM revenue_goals) as goals_set,
    (SELECT target_cents / 100.0 FROM revenue_goals WHERE period_start = '2025-08-18') as week_1_target;