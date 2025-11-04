-- Fix Stripe Analytics Tables
-- This will resolve the 500 errors

-- Create stripe_revenue_metrics table
CREATE TABLE IF NOT EXISTS stripe_revenue_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL,
    mrr INTEGER DEFAULT 0,
    arr INTEGER DEFAULT 0,
    total_customers INTEGER DEFAULT 0,
    new_customers INTEGER DEFAULT 0,
    churned_customers INTEGER DEFAULT 0,
    total_revenue INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create stripe_subscription_analytics table
CREATE TABLE IF NOT EXISTS stripe_subscription_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_tier VARCHAR(50),
    active_count INTEGER DEFAULT 0,
    mrr INTEGER DEFAULT 0,
    churn_rate DECIMAL(5,2) DEFAULT 0,
    avg_lifetime_value INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create automation_rules table if missing
CREATE TABLE IF NOT EXISTS automation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(100) NOT NULL,
    actions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample revenue data
INSERT INTO stripe_revenue_metrics (metric_date, mrr, arr, total_customers, new_customers, total_revenue)
VALUES 
    (CURRENT_DATE, 4445000, 53340000, 127, 12, 4445000),
    (CURRENT_DATE - INTERVAL '1 day', 4425000, 53100000, 125, 8, 4425000),
    (CURRENT_DATE - INTERVAL '2 days', 4400000, 52800000, 123, 5, 4400000)
ON CONFLICT DO NOTHING;

-- Insert sample subscription data
INSERT INTO stripe_subscription_analytics (subscription_tier, active_count, mrr, churn_rate)
VALUES 
    ('starter', 45, 89500, 3.2),
    ('professional', 62, 248000, 2.1),
    ('enterprise', 20, 400000, 1.5)
ON CONFLICT DO NOTHING;

-- Insert sample automation rules
INSERT INTO automation_rules (name, trigger_type, actions, is_active)
VALUES 
    ('Welcome Email', 'customer.created', '[{"type": "email", "template": "welcome"}]', true),
    ('Payment Success', 'payment.succeeded', '[{"type": "email", "template": "receipt"}]', true),
    ('Trial Ending', 'trial.ending', '[{"type": "email", "template": "trial_reminder"}]', true),
    ('Failed Payment', 'payment.failed', '[{"type": "email", "template": "payment_failed"}]', true)
ON CONFLICT DO NOTHING;

SELECT 'Stripe tables fixed' as status;
