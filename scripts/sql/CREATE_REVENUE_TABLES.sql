-- MyRoofGenius Revenue System Database Tables
-- Version 4.49 - Production Ready

-- Subscriptions table for Stripe
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_email VARCHAR(255) NOT NULL,
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    tier VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    trial_end TIMESTAMP,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI quotes table
CREATE TABLE IF NOT EXISTS ai_quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id VARCHAR(100) UNIQUE NOT NULL,
    customer_email VARCHAR(255),
    property_address TEXT,
    square_feet INTEGER,
    roof_area_sqft INTEGER,
    damage_assessment VARCHAR(100),
    total_cost DECIMAL(10, 2),
    ai_confidence DECIMAL(3, 2),
    valid_days INTEGER DEFAULT 30,
    analysis_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Support conversations table
CREATE TABLE IF NOT EXISTS support_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(100) UNIQUE NOT NULL,
    customer_email VARCHAR(255),
    intent VARCHAR(100),
    messages JSONB,
    resolved BOOLEAN DEFAULT false,
    resolution_time_seconds INTEGER,
    satisfaction_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Revenue metrics table
CREATE TABLE IF NOT EXISTS revenue_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE DEFAULT CURRENT_DATE,
    mrr DECIMAL(10, 2),
    arr DECIMAL(10, 2),
    total_customers INTEGER,
    new_customers INTEGER,
    churned_customers INTEGER,
    churn_rate DECIMAL(5, 4),
    ltv DECIMAL(10, 2),
    cac DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Onboarding sequences table
CREATE TABLE IF NOT EXISTS onboarding_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_email VARCHAR(255) NOT NULL,
    sequence_step INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'active',
    completed_steps JSONB,
    scheduled_actions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON subscriptions(customer_email);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_ai_quotes_email ON ai_quotes(customer_email);
CREATE INDEX IF NOT EXISTS idx_support_conversations_email ON support_conversations(customer_email);
CREATE INDEX IF NOT EXISTS idx_revenue_metrics_date ON revenue_metrics(metric_date);

-- Grant permissions
GRANT ALL ON subscriptions TO postgres, anon, authenticated, service_role;
GRANT ALL ON ai_quotes TO postgres, anon, authenticated, service_role;
GRANT ALL ON support_conversations TO postgres, anon, authenticated, service_role;
GRANT ALL ON revenue_metrics TO postgres, anon, authenticated, service_role;
GRANT ALL ON onboarding_sequences TO postgres, anon, authenticated, service_role;

-- Success message
SELECT 'Revenue tables created successfully!' as status;
