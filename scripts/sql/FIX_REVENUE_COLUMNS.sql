-- Fix revenue column mismatches
-- The code expects amount_cents but database has total_amount

-- Add amount_cents column to invoices if it doesn't exist
ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS amount_cents BIGINT;

-- Copy data from total_amount to amount_cents
UPDATE invoices 
SET amount_cents = total_amount 
WHERE amount_cents IS NULL;

-- Add other missing columns for revenue tracking
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS sent_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP WITHOUT TIME ZONE;

-- Update paid_at for paid invoices
UPDATE invoices
SET paid_at = paid_date::timestamp
WHERE status = 'paid' AND paid_at IS NULL AND paid_date IS NOT NULL;

-- Add total_amount_cents for compatibility
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS total_amount_cents BIGINT;

UPDATE invoices
SET total_amount_cents = total_amount
WHERE total_amount_cents IS NULL;

-- Add revenue_transactions table if missing
CREATE TABLE IF NOT EXISTS revenue_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_session_id VARCHAR(255),
    user_id UUID,
    customer_id UUID,
    amount_cents BIGINT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add subscriptions table if missing  
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    customer_id UUID, 
    stripe_subscription_id VARCHAR(255),
    product_id UUID,
    status VARCHAR(50) DEFAULT 'active',
    amount_cents BIGINT NOT NULL,
    billing_interval VARCHAR(20) DEFAULT 'monthly',
    current_period_start TIMESTAMP WITHOUT TIME ZONE,
    current_period_end TIMESTAMP WITHOUT TIME ZONE,
    cancel_at TIMESTAMP WITHOUT TIME ZONE,
    canceled_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add products table if missing
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price_cents BIGINT NOT NULL,
    stripe_product_id VARCHAR(255),
    stripe_price_id VARCHAR(255),
    category VARCHAR(100),
    features JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert some sample products if table is empty
INSERT INTO products (name, description, price_cents, category)
SELECT 'Basic Plan', 'Essential features for small teams', 9900, 'subscription'
WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1)
UNION ALL
SELECT 'Pro Plan', 'Advanced features for growing businesses', 29900, 'subscription'  
WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1)
UNION ALL
SELECT 'Enterprise Plan', 'Full suite for large organizations', 99900, 'subscription'
WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1);

-- Verify the fix
SELECT 
    'Invoices' as table_name,
    COUNT(*) as row_count,
    COUNT(amount_cents) as amount_cents_count,
    COUNT(total_amount_cents) as total_amount_cents_count
FROM invoices
UNION ALL
SELECT 
    'Revenue Transactions',
    COUNT(*),
    COUNT(amount_cents),
    0
FROM revenue_transactions
UNION ALL
SELECT 
    'Subscriptions',
    COUNT(*),
    COUNT(amount_cents),
    0
FROM subscriptions;