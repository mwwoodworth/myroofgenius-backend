-- Populate production sample data with correct schema
-- Adds sample data to demonstrate the working system

-- First, get a valid org_id (or create one)
INSERT INTO organizations (id, name, domain)
VALUES (gen_random_uuid(), 'WeatherCraft Roofing', 'weathercraft.com')
ON CONFLICT DO NOTHING;

-- Insert sample customers with correct columns
WITH org AS (
    SELECT id FROM organizations LIMIT 1
)
INSERT INTO customers (id, external_id, org_id, name, email, phone, address, city, state, zip, customer_type)
SELECT 
    gen_random_uuid(), 
    'CP-' || generate_series,
    org.id,
    'Customer ' || generate_series || ' LLC',
    'customer' || generate_series || '@example.com',
    '303-555-' || LPAD(generate_series::TEXT, 4, '0'),
    generate_series || ' Main Street',
    'Denver',
    'CO', 
    '80' || LPAD((200 + generate_series)::TEXT, 3, '0'),
    'commercial'
FROM generate_series(1, 10), org
ON CONFLICT (external_id) DO NOTHING;

-- Insert jobs for the customers
INSERT INTO jobs (id, job_number, customer_id, title, description, status, start_date, end_date, total_amount)
SELECT 
    gen_random_uuid(),
    'JOB-2025-' || LPAD((ROW_NUMBER() OVER())::TEXT, 4, '0'),
    c.id,
    'Roofing Project for ' || c.name,
    'Professional roofing services with AI monitoring',
    CASE 
        WHEN random() < 0.3 THEN 'completed'
        WHEN random() < 0.6 THEN 'in_progress'
        ELSE 'scheduled'
    END,
    CURRENT_DATE - (random() * 60)::INT,
    CURRENT_DATE + (random() * 30)::INT,
    (50000 + random() * 450000)::BIGINT  -- $500 to $4,500
FROM customers c
WHERE c.external_id LIKE 'CP-%';

-- Insert estimates for jobs
INSERT INTO estimates (id, estimate_number, customer_id, job_id, total_amount, status, valid_until)
SELECT 
    gen_random_uuid(),
    'EST-2025-' || LPAD((ROW_NUMBER() OVER())::TEXT, 4, '0'),
    j.customer_id,
    j.id,
    j.total_amount,
    'accepted',
    CURRENT_DATE + INTERVAL '90 days'
FROM jobs j;

-- Insert invoices with correct columns
INSERT INTO invoices (
    id, invoice_number, customer_id, job_id,
    total_amount, amount_cents, total_amount_cents,
    tax_amount, balance_due,
    invoice_date, due_date, status, payment_status,
    line_items
)
SELECT 
    gen_random_uuid(),
    'INV-2025-' || LPAD((ROW_NUMBER() OVER())::TEXT, 4, '0'),
    j.customer_id,
    j.id,
    j.total_amount,
    j.total_amount,  -- amount_cents
    j.total_amount,  -- total_amount_cents
    (j.total_amount * 0.08)::BIGINT,  -- 8% tax
    CASE 
        WHEN j.status = 'completed' THEN 0
        ELSE j.total_amount
    END,
    CURRENT_DATE - (random() * 30)::INT,
    CURRENT_DATE + (random() * 30)::INT,
    CASE 
        WHEN j.status = 'completed' THEN 'paid'
        WHEN random() < 0.3 THEN 'paid'
        ELSE 'sent'
    END,
    CASE 
        WHEN j.status = 'completed' THEN 'paid'
        WHEN random() < 0.3 THEN 'paid'
        ELSE 'pending'
    END,
    jsonb_build_array(
        jsonb_build_object(
            'description', 'Roofing Services',
            'quantity', 1,
            'unit_price', j.total_amount / 100.0,
            'total', j.total_amount / 100.0
        )
    )
FROM jobs j;

-- Update paid invoices
UPDATE invoices 
SET 
    paid_date = invoice_date + ((random() * 14)::INT || ' days')::INTERVAL,
    paid_at = (invoice_date + ((random() * 14)::INT || ' days')::INTERVAL)::timestamp,
    amount_paid = total_amount,
    balance_due = 0
WHERE status = 'paid';

-- Insert revenue transactions for paid invoices
INSERT INTO revenue_transactions (
    id, customer_id, stripe_session_id, 
    currency, status, payment_method, description
)
SELECT 
    gen_random_uuid(),
    i.customer_id,
    'cs_test_' || substr(md5(random()::text), 1, 24),
    'USD',
    'completed',
    'card',
    'Payment for ' || i.invoice_number
FROM invoices i
WHERE i.status = 'paid';

-- Add subscriptions data with correct columns
INSERT INTO subscriptions (
    id, stripe_subscription_id, 
    status, billing_interval,
    current_period_start, current_period_end
)
SELECT 
    gen_random_uuid(),
    'sub_' || substr(md5(random()::text), 1, 24),
    'active',
    'monthly',
    DATE_TRUNC('month', CURRENT_DATE),
    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
FROM generate_series(1, 5);

-- Summary report
SELECT '=== DATA POPULATION COMPLETE ===' as status;

SELECT entity, count FROM (
    SELECT 'Customers' as entity, COUNT(*)::TEXT as count FROM customers
    UNION ALL
    SELECT 'Jobs', COUNT(*)::TEXT FROM jobs
    UNION ALL
    SELECT 'Estimates', COUNT(*)::TEXT FROM estimates
    UNION ALL
    SELECT 'Invoices', COUNT(*)::TEXT FROM invoices
    UNION ALL
    SELECT 'Paid Invoices', COUNT(*)::TEXT FROM invoices WHERE status = 'paid'
    UNION ALL
    SELECT 'Revenue Transactions', COUNT(*)::TEXT FROM revenue_transactions
    UNION ALL
    SELECT 'Active Subscriptions', COUNT(*)::TEXT FROM subscriptions WHERE status = 'active'
) summary;

-- Calculate revenue
SELECT 
    'Total Revenue' as metric,
    '$' || TO_CHAR(SUM(total_amount) / 100.0, 'FM999,999.00') as value
FROM invoices 
WHERE status = 'paid'
UNION ALL
SELECT 
    'Outstanding',
    '$' || TO_CHAR(SUM(balance_due) / 100.0, 'FM999,999.00')
FROM invoices 
WHERE status != 'paid';