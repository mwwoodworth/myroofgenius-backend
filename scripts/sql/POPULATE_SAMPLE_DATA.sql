-- Populate sample data for production system
-- This will add test data to demonstrate the system is working

-- Insert sample customers
INSERT INTO customers (id, external_id, name, email, phone, address, city, state, zip_code, customer_type)
VALUES 
    (gen_random_uuid(), 'CP-001', 'Denver Roofing Solutions', 'info@denverroofing.com', '303-555-0100', '123 Main St', 'Denver', 'CO', '80202', 'commercial'),
    (gen_random_uuid(), 'CP-002', 'Mountain View Properties', 'contact@mountainview.com', '303-555-0200', '456 Oak Ave', 'Boulder', 'CO', '80301', 'commercial'),
    (gen_random_uuid(), 'CP-003', 'Colorado Springs Mall', 'manager@csmall.com', '719-555-0300', '789 Pine Rd', 'Colorado Springs', 'CO', '80903', 'commercial')
ON CONFLICT (external_id) DO NOTHING;

-- Get customer IDs for relationships
WITH customer_ids AS (
    SELECT id, external_id FROM customers WHERE external_id IN ('CP-001', 'CP-002', 'CP-003')
)
-- Insert sample jobs
INSERT INTO jobs (id, job_number, customer_id, title, description, status, start_date, end_date, total_amount)
SELECT 
    gen_random_uuid(),
    'JOB-2025-' || LPAD((ROW_NUMBER() OVER())::TEXT, 3, '0'),
    c.id,
    CASE 
        WHEN c.external_id = 'CP-001' THEN 'Commercial Roof Replacement'
        WHEN c.external_id = 'CP-002' THEN 'Emergency Leak Repair'
        ELSE 'Annual Maintenance Contract'
    END,
    'Professional roofing services with AI-powered monitoring',
    CASE 
        WHEN c.external_id = 'CP-001' THEN 'in_progress'
        WHEN c.external_id = 'CP-002' THEN 'completed'
        ELSE 'scheduled'
    END,
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE + INTERVAL '30 days',
    CASE 
        WHEN c.external_id = 'CP-001' THEN 450000  -- $4,500.00
        WHEN c.external_id = 'CP-002' THEN 125000  -- $1,250.00
        ELSE 850000  -- $8,500.00
    END
FROM customer_ids c;

-- Insert sample estimates
INSERT INTO estimates (id, estimate_number, customer_id, job_id, total_amount, status, valid_until)
SELECT 
    gen_random_uuid(),
    'EST-2025-' || LPAD((ROW_NUMBER() OVER())::TEXT, 3, '0'),
    j.customer_id,
    j.id,
    j.total_amount,
    'accepted',
    CURRENT_DATE + INTERVAL '90 days'
FROM jobs j
WHERE j.job_number IN ('JOB-2025-001', 'JOB-2025-002', 'JOB-2025-003');

-- Insert sample invoices with revenue data
INSERT INTO invoices (
    id, invoice_number, customer_id, job_id, 
    total_amount, amount_cents, total_amount_cents,
    subtotal, tax_amount, balance_due,
    invoice_date, due_date, status, payment_status,
    line_items
)
SELECT 
    gen_random_uuid(),
    'INV-2025-' || LPAD((ROW_NUMBER() OVER())::TEXT, 3, '0'),
    j.customer_id,
    j.id,
    j.total_amount,
    j.total_amount,  -- amount_cents
    j.total_amount,  -- total_amount_cents
    (j.total_amount * 0.9)::BIGINT,  -- subtotal (90% of total)
    (j.total_amount * 0.1)::BIGINT,  -- tax (10%)
    CASE 
        WHEN j.status = 'completed' THEN 0
        ELSE j.total_amount
    END,
    CURRENT_DATE - INTERVAL '15 days',
    CURRENT_DATE + INTERVAL '15 days',
    CASE 
        WHEN j.status = 'completed' THEN 'paid'
        ELSE 'sent'
    END,
    CASE 
        WHEN j.status = 'completed' THEN 'paid'
        ELSE 'pending'
    END,
    jsonb_build_array(
        jsonb_build_object(
            'description', 'Roofing Services',
            'quantity', 1,
            'unit_price', j.total_amount / 100,
            'total', j.total_amount / 100
        )
    )
FROM jobs j
WHERE j.job_number IN ('JOB-2025-001', 'JOB-2025-002', 'JOB-2025-003');

-- Update paid invoices with payment dates
UPDATE invoices 
SET 
    paid_date = invoice_date + INTERVAL '7 days',
    paid_at = (invoice_date + INTERVAL '7 days')::timestamp,
    paid_amount = total_amount,
    amount_paid = total_amount
WHERE status = 'paid';

-- Insert sample revenue transactions
INSERT INTO revenue_transactions (
    id, customer_id, amount_cents, status, 
    payment_method, description, created_at
)
SELECT 
    gen_random_uuid(),
    i.customer_id,
    i.total_amount,
    'completed',
    'card',
    'Payment for ' || i.invoice_number,
    i.paid_at
FROM invoices i
WHERE i.status = 'paid';

-- Insert sample products
INSERT INTO products (id, name, description, price_cents)
VALUES 
    (gen_random_uuid(), 'Roof Inspection', 'AI-powered roof assessment', 49900),
    (gen_random_uuid(), 'Emergency Repair', '24/7 emergency service', 199900),
    (gen_random_uuid(), 'Annual Maintenance', 'Comprehensive maintenance plan', 299900)
ON CONFLICT DO NOTHING;

-- Insert sample subscriptions (for MRR calculation)
INSERT INTO subscriptions (
    id, customer_id, status, amount_cents, 
    billing_interval, current_period_start, current_period_end
)
SELECT 
    gen_random_uuid(),
    c.id,
    'active',
    29900,  -- $299/month
    'monthly',
    DATE_TRUNC('month', CURRENT_DATE),
    DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
FROM customers c
WHERE c.external_id IN ('CP-001', 'CP-003');

-- Verify the data
SELECT 'Data Population Summary' as report;
SELECT 'Customers' as entity, COUNT(*) as count FROM customers
UNION ALL
SELECT 'Jobs', COUNT(*) FROM jobs
UNION ALL
SELECT 'Estimates', COUNT(*) FROM estimates
UNION ALL
SELECT 'Invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'Paid Invoices', COUNT(*) FROM invoices WHERE status = 'paid'
UNION ALL
SELECT 'Revenue Transactions', COUNT(*) FROM revenue_transactions
UNION ALL
SELECT 'Active Subscriptions', COUNT(*) FROM subscriptions WHERE status = 'active'
UNION ALL
SELECT 'Products', COUNT(*) FROM products;

-- Calculate revenue metrics
SELECT 
    'Revenue Metrics' as report,
    COUNT(DISTINCT i.id) as total_invoices,
    SUM(CASE WHEN i.status = 'paid' THEN i.total_amount ELSE 0 END) / 100.0 as total_revenue_usd,
    COUNT(DISTINCT s.id) as active_subscriptions,
    SUM(s.amount_cents) / 100.0 as mrr_usd
FROM invoices i
CROSS JOIN subscriptions s
WHERE s.status = 'active';