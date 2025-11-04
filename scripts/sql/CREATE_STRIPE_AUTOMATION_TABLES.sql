-- Comprehensive Stripe Automation Database Schema
-- Production-ready tables for complete payment automation

-- Create stripe_automation_rules table if not exists
CREATE TABLE IF NOT EXISTS stripe_automation_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    trigger VARCHAR(100) NOT NULL,
    conditions JSONB DEFAULT '{}',
    actions JSONB DEFAULT '[]',
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create automated_emails table
CREATE TABLE IF NOT EXISTS automated_emails (
    id SERIAL PRIMARY KEY,
    recipient VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    template VARCHAR(100),
    trigger_event VARCHAR(100),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'sent',
    metadata JSONB DEFAULT '{}'
);

-- Create stripe_prices table for price management
CREATE TABLE IF NOT EXISTS stripe_prices (
    id SERIAL PRIMARY KEY,
    stripe_price_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_product_id VARCHAR(255),
    active BOOLEAN DEFAULT true,
    currency VARCHAR(3) DEFAULT 'usd',
    unit_amount INTEGER,
    recurring JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create refunds table
CREATE TABLE IF NOT EXISTS refunds (
    id SERIAL PRIMARY KEY,
    stripe_refund_id VARCHAR(255) UNIQUE,
    payment_intent_id VARCHAR(255),
    amount_cents INTEGER,
    reason VARCHAR(100),
    status VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Create tasks table for automation task creation
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(50) DEFAULT 'medium',
    assigned_to VARCHAR(255),
    due_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_stripe_automation_rules_trigger ON stripe_automation_rules(trigger);
CREATE INDEX IF NOT EXISTS idx_stripe_automation_rules_enabled ON stripe_automation_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_automated_emails_recipient ON automated_emails(recipient);
CREATE INDEX IF NOT EXISTS idx_automated_emails_trigger ON automated_emails(trigger_event);
CREATE INDEX IF NOT EXISTS idx_stripe_customers_email ON stripe_customers(email);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_customer ON stripe_subscriptions(customer_email);
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_status ON stripe_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_checkout_sessions_status ON checkout_sessions(status);
CREATE INDEX IF NOT EXISTS idx_revenue_tracking_date ON revenue_tracking(date);
CREATE INDEX IF NOT EXISTS idx_payments_customer ON payments(customer_email);
CREATE INDEX IF NOT EXISTS idx_stripe_webhooks_event_type ON stripe_webhooks(event_type);
CREATE INDEX IF NOT EXISTS idx_stripe_webhooks_processed ON stripe_webhooks(processed);

-- Add missing columns to existing tables if they don't exist
DO $$ 
BEGIN
    -- Add columns to stripe_customers if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_customers' AND column_name = 'phone') THEN
        ALTER TABLE stripe_customers ADD COLUMN phone VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_customers' AND column_name = 'updated_at') THEN
        ALTER TABLE stripe_customers ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    -- Add columns to stripe_subscriptions if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_subscriptions' AND column_name = 'current_period_start') THEN
        ALTER TABLE stripe_subscriptions ADD COLUMN current_period_start TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_subscriptions' AND column_name = 'current_period_end') THEN
        ALTER TABLE stripe_subscriptions ADD COLUMN current_period_end TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_subscriptions' AND column_name = 'canceled_at') THEN
        ALTER TABLE stripe_subscriptions ADD COLUMN canceled_at TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_subscriptions' AND column_name = 'cancellation_reason') THEN
        ALTER TABLE stripe_subscriptions ADD COLUMN cancellation_reason TEXT;
    END IF;
    
    -- Add columns to checkout_sessions if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'checkout_sessions' AND column_name = 'quantity') THEN
        ALTER TABLE checkout_sessions ADD COLUMN quantity INTEGER DEFAULT 1;
    END IF;
    
    -- Add columns to revenue_tracking if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'revenue_tracking' AND column_name = 'subscription_id') THEN
        ALTER TABLE revenue_tracking ADD COLUMN subscription_id VARCHAR(255);
    END IF;
    
    -- Add columns to payments if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'payments' AND column_name = 'stripe_payment_intent_id') THEN
        ALTER TABLE payments ADD COLUMN stripe_payment_intent_id VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'payments' AND column_name = 'currency') THEN
        ALTER TABLE payments ADD COLUMN currency VARCHAR(3) DEFAULT 'usd';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'payments' AND column_name = 'description') THEN
        ALTER TABLE payments ADD COLUMN description TEXT;
    END IF;
    
    -- Add columns to stripe_webhooks if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_webhooks' AND column_name = 'processed_at') THEN
        ALTER TABLE stripe_webhooks ADD COLUMN processed_at TIMESTAMP;
    END IF;
END $$;

-- Create default automation rules
INSERT INTO stripe_automation_rules (name, trigger, conditions, actions, enabled)
VALUES 
    ('Send Welcome Email', 'customer_created', '{}', 
     '[{"type": "send_email", "template": "welcome"}]', true),
    
    ('Payment Success Notification', 'payment_success', '{}',
     '[{"type": "send_email", "template": "payment_success"}, 
       {"type": "update_database", "table": "customers", "updates": {"last_payment": "NOW()"}}]', true),
    
    ('Trial Ending Reminder', 'trial_ending', '{}',
     '[{"type": "send_email", "template": "trial_ending"},
       {"type": "apply_coupon", "coupon_id": "TRIAL20"}]', true),
    
    ('Failed Payment Recovery', 'payment_failed', '{}',
     '[{"type": "send_email", "template": "payment_failed"},
       {"type": "create_task", "title": "Follow up on failed payment", "priority": "high"}]', true),
    
    ('Subscription Cancellation Retention', 'subscription_canceled', '{}',
     '[{"type": "send_email", "template": "win_back"},
       {"type": "apply_coupon", "coupon_id": "COMEBACK50"}]', true)
ON CONFLICT (name) DO NOTHING;

-- Create sample Stripe prices
INSERT INTO stripe_prices (stripe_price_id, stripe_product_id, active, unit_amount, recurring, metadata)
VALUES
    ('price_1Q5Po1RxscTmSupaBNKQxGYf', 'prod_starter', true, 4999, 
     '{"interval": "month", "interval_count": 1}', '{"tier": "starter"}'),
    
    ('price_1Q5Po1RxscTmSupaC2LRyHZg', 'prod_professional', true, 9999,
     '{"interval": "month", "interval_count": 1}', '{"tier": "professional"}'),
    
    ('price_1Q5Po1RxscTmSupaD3MSzJAh', 'prod_enterprise', true, 29999,
     '{"interval": "month", "interval_count": 1}', '{"tier": "enterprise"}')
ON CONFLICT (stripe_price_id) DO UPDATE
SET active = EXCLUDED.active,
    unit_amount = EXCLUDED.unit_amount,
    updated_at = CURRENT_TIMESTAMP;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;