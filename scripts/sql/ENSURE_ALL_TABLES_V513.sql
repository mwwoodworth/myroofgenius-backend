-- Ensure all tables exist for v5.13 revenue system
-- Run this to guarantee database is ready for production

-- Revenue tracking tables (if not exist)
CREATE TABLE IF NOT EXISTS ai_estimates (
    id SERIAL PRIMARY KEY,
    estimate_id VARCHAR(50) UNIQUE,
    customer_email VARCHAR(255),
    property_address TEXT,
    total_cost_cents BIGINT,
    material_cost_cents BIGINT,
    labor_cost_cents BIGINT,
    timeline_days INTEGER,
    confidence_score DECIMAL(3,2),
    details JSONB,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roof_analyses (
    id SERIAL PRIMARY KEY,
    customer_email VARCHAR(255),
    photo_data TEXT,
    ai_analysis JSONB,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    source VARCHAR(100),
    score INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'new',
    tags JSONB,
    notes TEXT,
    last_contacted TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS revenue_tracking (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    revenue_cents BIGINT DEFAULT 0,
    new_customers INTEGER DEFAULT 0,
    active_subscriptions INTEGER DEFAULT 0,
    churn_rate DECIMAL(5,4),
    ltv_cents BIGINT,
    cac_cents BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS checkout_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE,
    customer_email VARCHAR(255),
    amount_cents BIGINT,
    status VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ab_tests (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100),
    page_id VARCHAR(100),
    variant VARCHAR(10),
    conversions INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shopping_carts (
    id SERIAL PRIMARY KEY,
    cart_id VARCHAR(100) UNIQUE,
    customer_email VARCHAR(255),
    items JSONB,
    total_cents BIGINT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    cart_id VARCHAR(100),
    product_id VARCHAR(100),
    quantity INTEGER,
    price_cents BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customer_ltv (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) UNIQUE,
    total_revenue_cents BIGINT DEFAULT 0,
    order_count INTEGER DEFAULT 0,
    avg_order_value_cents BIGINT,
    first_purchase DATE,
    last_purchase DATE,
    predicted_ltv_cents BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_revenue_date ON revenue_tracking(date);
CREATE INDEX IF NOT EXISTS idx_checkout_email ON checkout_sessions(customer_email);
CREATE INDEX IF NOT EXISTS idx_ab_test ON ab_tests(test_id, variant);
CREATE INDEX IF NOT EXISTS idx_cart_customer ON shopping_carts(customer_email);
CREATE INDEX IF NOT EXISTS idx_ad_perf_campaign ON ad_performance(campaign_id, date);
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer ON subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON subscriptions(customer_email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Status report
SELECT 'Revenue System Tables Created/Verified' as status, NOW() as timestamp;