-- FIX_REVENUE_SCHEMA_V610.sql
-- Fixes all missing columns for revenue system
-- Date: 2025-08-18

-- Add missing columns to revenue_tracking if not exists
ALTER TABLE revenue_tracking 
ADD COLUMN IF NOT EXISTS amount_cents BIGINT DEFAULT 0;

ALTER TABLE revenue_tracking 
ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD';

-- Add missing columns to invoices
ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS total_cents BIGINT DEFAULT 0;

ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS subtotal_cents BIGINT DEFAULT 0;

ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS tax_cents BIGINT DEFAULT 0;

-- Add missing columns to estimates
ALTER TABLE estimates 
ADD COLUMN IF NOT EXISTS total_cents BIGINT DEFAULT 0;

ALTER TABLE estimates 
ADD COLUMN IF NOT EXISTS material_cost_cents BIGINT DEFAULT 0;

ALTER TABLE estimates 
ADD COLUMN IF NOT EXISTS labor_cost_cents BIGINT DEFAULT 0;

-- Add stripe columns if missing
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);

ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS stripe_invoice_id VARCHAR(255);

ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255);

-- Create stripe_webhooks table if not exists
CREATE TABLE IF NOT EXISTS stripe_webhooks (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Create revenue_metrics table if not exists
CREATE TABLE IF NOT EXISTS revenue_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    mrr_cents BIGINT DEFAULT 0,
    arr_cents BIGINT DEFAULT 0,
    new_customers INTEGER DEFAULT 0,
    churned_customers INTEGER DEFAULT 0,
    total_revenue_cents BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

-- Create subscription tracking if not exists
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(50),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    amount_cents BIGINT,
    interval VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_revenue_tracking_date ON revenue_tracking(date);
CREATE INDEX IF NOT EXISTS idx_invoices_stripe_id ON invoices(stripe_invoice_id);
CREATE INDEX IF NOT EXISTS idx_customers_stripe_id ON customers(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

-- Verify changes
SELECT 
    'Revenue Schema Fixed' as status,
    COUNT(*) as tables_updated,
    NOW() as fixed_at
FROM information_schema.columns
WHERE table_schema = 'public' 
AND column_name LIKE '%cents%';