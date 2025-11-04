-- Fix Stripe tables schema

-- Check and add missing columns
DO $$ 
BEGIN
    -- Fix stripe_subscriptions table
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_subscriptions' AND column_name = 'customer_email') THEN
        ALTER TABLE stripe_subscriptions ADD COLUMN customer_email VARCHAR(255);
    END IF;
    
    -- Fix payments table  
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'payments' AND column_name = 'customer_email') THEN
        ALTER TABLE payments ADD COLUMN customer_email VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'payments' AND column_name = 'amount_cents') THEN
        ALTER TABLE payments ADD COLUMN amount_cents INTEGER;
    END IF;
    
    -- Fix stripe_customers table
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_customers' AND column_name = 'stripe_id') THEN
        ALTER TABLE stripe_customers ADD COLUMN stripe_id VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_customers' AND column_name = 'name') THEN
        ALTER TABLE stripe_customers ADD COLUMN name VARCHAR(255);
    END IF;
    
    -- Fix checkout_sessions
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'checkout_sessions' AND column_name = 'customer_email') THEN
        ALTER TABLE checkout_sessions ADD COLUMN customer_email VARCHAR(255);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'checkout_sessions' AND column_name = 'price_id') THEN
        ALTER TABLE checkout_sessions ADD COLUMN price_id VARCHAR(255);
    END IF;
    
    -- Fix stripe_webhooks
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_webhooks' AND column_name = 'event_id') THEN
        ALTER TABLE stripe_webhooks ADD COLUMN event_id VARCHAR(255) UNIQUE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_webhooks' AND column_name = 'event_type') THEN
        ALTER TABLE stripe_webhooks ADD COLUMN event_type VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_webhooks' AND column_name = 'payload') THEN
        ALTER TABLE stripe_webhooks ADD COLUMN payload JSONB;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'stripe_webhooks' AND column_name = 'processed') THEN
        ALTER TABLE stripe_webhooks ADD COLUMN processed BOOLEAN DEFAULT false;
    END IF;
END $$;

-- Create indexes that were missing
CREATE INDEX IF NOT EXISTS idx_stripe_subscriptions_email ON stripe_subscriptions(customer_email);
CREATE INDEX IF NOT EXISTS idx_payments_email ON payments(customer_email);

-- Add unique constraint for automation rules name
ALTER TABLE stripe_automation_rules ADD CONSTRAINT unique_rule_name UNIQUE (name);

-- Update automation rules (with proper ON CONFLICT)
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
       {"type": "apply_coupon", "coupon_id": "COMEBACK50"}]', true),
       
    ('Invoice Upcoming Notification', 'invoice_upcoming', '{}',
     '[{"type": "send_email", "template": "invoice_upcoming"}]', true),
     
    ('Dispute Alert', 'dispute_created', '{}',
     '[{"type": "create_task", "title": "Handle Dispute", "priority": "urgent"},
       {"type": "send_email", "template": "dispute_alert"}]', true),
       
    ('Refund Processed', 'refund_created', '{}',
     '[{"type": "send_email", "template": "refund_confirmation"},
       {"type": "update_database", "table": "customers", "updates": {"refund_issued": true}}]', true)
ON CONFLICT (name) DO UPDATE
SET trigger = EXCLUDED.trigger,
    conditions = EXCLUDED.conditions,
    actions = EXCLUDED.actions,
    enabled = EXCLUDED.enabled,
    updated_at = CURRENT_TIMESTAMP;