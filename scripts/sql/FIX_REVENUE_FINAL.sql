-- Final fix for revenue system columns
-- Ensure all expected columns exist

-- Fix invoices table
ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS amount_cents BIGINT;

UPDATE invoices 
SET amount_cents = total_amount 
WHERE amount_cents IS NULL;

ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS sent_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP WITHOUT TIME ZONE,
ADD COLUMN IF NOT EXISTS total_amount_cents BIGINT;

UPDATE invoices
SET total_amount_cents = total_amount
WHERE total_amount_cents IS NULL;

-- Check current state
SELECT 
    'Invoices' as table_name,
    COUNT(*) as total_rows,
    SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END)/100 as revenue_usd
FROM invoices;