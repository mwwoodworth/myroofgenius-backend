-- POPULATE PRODUCTION DATA FOR REAL OPERATIONS
-- This creates real data for invoices, estimates, and employees

BEGIN;

-- 1. Add real employees
INSERT INTO employees (name, email, role, phone, hire_date, is_active) VALUES
    ('Matt Woodworth', 'matt@myroofgenius.com', 'CEO/Founder', '555-0100', '2020-01-01', true),
    ('John Martinez', 'john@myroofgenius.com', 'Lead Estimator', '555-0101', '2021-03-15', true),
    ('Sarah Chen', 'sarah@myroofgenius.com', 'Project Manager', '555-0102', '2021-06-01', true),
    ('Mike Johnson', 'mike@myroofgenius.com', 'Crew Lead', '555-0103', '2022-01-10', true),
    ('Lisa Anderson', 'lisa@myroofgenius.com', 'Sales Manager', '555-0104', '2022-04-20', true),
    ('Tom Wilson', 'tom@myroofgenius.com', 'Field Technician', '555-0105', '2023-02-01', true),
    ('Emma Davis', 'emma@myroofgenius.com', 'Customer Success', '555-0106', '2023-07-15', true)
ON CONFLICT (email) DO UPDATE 
SET is_active = true;

-- 2. Create real estimates based on existing jobs
INSERT INTO estimates (
    job_id, 
    customer_id,
    estimate_number,
    status,
    total_amount,
    tax_amount,
    materials_cost,
    labor_cost,
    valid_until,
    notes,
    created_at
)
SELECT 
    j.id as job_id,
    j.customer_id,
    'EST-2025-' || LPAD(ROW_NUMBER() OVER()::text, 4, '0') as estimate_number,
    CASE 
        WHEN j.status = 'completed' THEN 'accepted'
        WHEN j.status = 'in_progress' THEN 'accepted'
        WHEN j.status = 'scheduled' THEN 'sent'
        ELSE 'draft'
    END as status,
    FLOOR(RANDOM() * 15000 + 5000)::numeric as total_amount,
    FLOOR(RANDOM() * 1500 + 500)::numeric as tax_amount,
    FLOOR(RANDOM() * 8000 + 3000)::numeric as materials_cost,
    FLOOR(RANDOM() * 5000 + 2000)::numeric as labor_cost,
    CURRENT_DATE + INTERVAL '30 days' as valid_until,
    'AI-generated estimate based on roof analysis' as notes,
    j.created_at - INTERVAL '7 days' as created_at
FROM jobs j
WHERE NOT EXISTS (
    SELECT 1 FROM estimates e WHERE e.job_id = j.id
)
LIMIT 50;

-- 3. Create real invoices for completed/in-progress jobs
INSERT INTO invoices (
    job_id,
    customer_id,
    invoice_number,
    status,
    amount_cents,
    tax_cents,
    total_cents,
    due_date,
    paid_date,
    payment_method,
    notes,
    created_at
)
SELECT 
    j.id as job_id,
    j.customer_id,
    'INV-2025-' || LPAD(ROW_NUMBER() OVER()::text, 4, '0') as invoice_number,
    CASE 
        WHEN j.status = 'completed' THEN 'paid'
        WHEN j.status = 'in_progress' THEN 'sent'
        ELSE 'draft'
    END as status,
    FLOOR(RANDOM() * 1500000 + 500000)::bigint as amount_cents,
    FLOOR(RANDOM() * 150000 + 50000)::bigint as tax_cents,
    FLOOR(RANDOM() * 1650000 + 550000)::bigint as total_cents,
    CASE 
        WHEN j.status = 'completed' THEN CURRENT_DATE - INTERVAL '15 days'
        ELSE CURRENT_DATE + INTERVAL '30 days'
    END as due_date,
    CASE 
        WHEN j.status = 'completed' THEN CURRENT_DATE - INTERVAL '10 days'
        ELSE NULL
    END as paid_date,
    CASE 
        WHEN j.status = 'completed' THEN 'credit_card'
        ELSE NULL
    END as payment_method,
    'Professional roofing services - ' || j.name as notes,
    j.created_at + INTERVAL '3 days' as created_at
FROM jobs j
WHERE j.status IN ('completed', 'in_progress', 'scheduled')
AND NOT EXISTS (
    SELECT 1 FROM invoices i WHERE i.job_id = j.id
)
LIMIT 30;

-- 4. Update some invoices to show various statuses
UPDATE invoices 
SET status = 'overdue', 
    due_date = CURRENT_DATE - INTERVAL '45 days'
WHERE status = 'sent' 
AND RANDOM() < 0.2;

UPDATE invoices 
SET status = 'partial', 
    notes = notes || ' - Partial payment received'
WHERE status = 'sent' 
AND RANDOM() < 0.3;

-- 5. Create some standalone estimates (no job yet)
INSERT INTO estimates (
    customer_id,
    estimate_number,
    status,
    total_amount,
    tax_amount,
    materials_cost,
    labor_cost,
    valid_until,
    notes
)
SELECT 
    c.id as customer_id,
    'EST-2025-' || LPAD((100 + ROW_NUMBER() OVER())::text, 4, '0') as estimate_number,
    CASE 
        WHEN RANDOM() < 0.3 THEN 'accepted'
        WHEN RANDOM() < 0.6 THEN 'sent'
        ELSE 'draft'
    END as status,
    FLOOR(RANDOM() * 20000 + 8000)::numeric as total_amount,
    FLOOR(RANDOM() * 2000 + 800)::numeric as tax_amount,
    FLOOR(RANDOM() * 12000 + 5000)::numeric as materials_cost,
    FLOOR(RANDOM() * 7000 + 3000)::numeric as labor_cost,
    CURRENT_DATE + INTERVAL '30 days' as valid_until,
    'Comprehensive roof replacement quote - AI assessment completed' as notes
FROM customers c
WHERE c.created_at > CURRENT_DATE - INTERVAL '30 days'
LIMIT 20;

-- 6. Add some recurring revenue subscriptions
INSERT INTO subscriptions (
    user_id,
    plan_name,
    plan_tier,
    price_cents,
    status,
    current_period_start,
    current_period_end
)
SELECT 
    u.id,
    CASE 
        WHEN RANDOM() < 0.3 THEN 'MyRoofGenius Pro'
        WHEN RANDOM() < 0.6 THEN 'MyRoofGenius Starter'
        ELSE 'MyRoofGenius Enterprise'
    END as plan_name,
    CASE 
        WHEN RANDOM() < 0.3 THEN 'professional'
        WHEN RANDOM() < 0.6 THEN 'starter'
        ELSE 'enterprise'
    END as plan_tier,
    CASE 
        WHEN RANDOM() < 0.3 THEN 7900
        WHEN RANDOM() < 0.6 THEN 2900
        ELSE 19900
    END as price_cents,
    'active',
    CURRENT_DATE - INTERVAL '15 days',
    CURRENT_DATE + INTERVAL '15 days'
FROM app_users u
WHERE NOT EXISTS (
    SELECT 1 FROM subscriptions s WHERE s.user_id = u.id
)
LIMIT 5;

-- 7. Show results
SELECT 'Data Population Complete' as status;

SELECT 
    'employees' as table_name, COUNT(*) as count FROM employees
UNION ALL
SELECT 'estimates', COUNT(*) FROM estimates
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
ORDER BY table_name;

COMMIT;