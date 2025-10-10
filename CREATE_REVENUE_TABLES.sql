-- Create subscription tiers table
CREATE TABLE IF NOT EXISTS subscription_tiers (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price_cents INTEGER NOT NULL,
    features JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create lead magnets table
CREATE TABLE IF NOT EXISTS lead_magnets (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    value VARCHAR(50),
    cta VARCHAR(255),
    conversion_rate DECIMAL(5,2),
    downloads INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create email campaigns table
CREATE TABLE IF NOT EXISTS email_campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50),
    sequence JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    sends INTEGER DEFAULT 0,
    opens INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create affiliate partners table
CREATE TABLE IF NOT EXISTS affiliate_partners (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'bronze',
    commission_rate DECIMAL(5,2) DEFAULT 0.20,
    referrals INTEGER DEFAULT 0,
    earnings_cents INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create revenue metrics table
CREATE TABLE IF NOT EXISTS revenue_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    mrr_cents INTEGER DEFAULT 0,
    new_customers INTEGER DEFAULT 0,
    churned_customers INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5,4),
    avg_order_value_cents INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

-- Create urgency campaigns table
CREATE TABLE IF NOT EXISTS urgency_campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    discount DECIMAL(5,2),
    message TEXT,
    duration_hours INTEGER,
    trigger VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_revenue_metrics_date ON revenue_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_affiliate_partners_tier ON affiliate_partners(tier);
CREATE INDEX IF NOT EXISTS idx_email_campaigns_type ON email_campaigns(type);

-- Insert default data
INSERT INTO subscription_tiers (id, name, price_cents, features, is_active)
VALUES 
    ('free', 'Free Trial', 0, '["1 AI analysis", "Basic tools", "7-day trial"]', true),
    ('starter', 'Starter', 2900, '["5 AI analyses/month", "Basic estimation", "Email support"]', true),
    ('professional', 'Professional', 9700, '["50 AI analyses/month", "Advanced tools", "Priority support", "Team features"]', true),
    ('enterprise', 'Enterprise', 29700, '["Unlimited analyses", "Custom AI training", "Dedicated support", "White-label"]', true)
ON CONFLICT (id) DO NOTHING;