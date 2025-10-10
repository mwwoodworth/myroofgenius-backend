-- POPULATE LIVE PRODUCTION DATABASE NOW
-- Direct inserts to ensure data exists

BEGIN;

-- 1. Add real employees (fix duplicate key issues)
INSERT INTO employees (name, email, role, phone, hire_date, is_active) VALUES
    ('Matt Woodworth', 'matt@myroofgenius.com', 'CEO/Founder', '555-0100', '2020-01-01', true),
    ('John Martinez', 'john.martinez@myroofgenius.com', 'Lead Estimator', '555-0101', '2021-03-15', true),
    ('Sarah Chen', 'sarah.chen@myroofgenius.com', 'Project Manager', '555-0102', '2021-06-01', true),
    ('Mike Johnson', 'mike.johnson@myroofgenius.com', 'Crew Lead', '555-0103', '2022-01-10', true),
    ('Lisa Anderson', 'lisa.anderson@myroofgenius.com', 'Sales Manager', '555-0104', '2022-04-20', true)
ON CONFLICT (email) DO UPDATE 
SET is_active = true,
    updated_at = CURRENT_TIMESTAMP;

-- 2. Create real estimates
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
    'EST-2025-' || LPAD((ROW_NUMBER() OVER())::text, 4, '0') as estimate_number,
    'sent' as status,
    15000.00 as total_amount,
    1200.00 as tax_amount,
    8000.00 as materials_cost,
    5800.00 as labor_cost,
    CURRENT_DATE + INTERVAL '30 days' as valid_until,
    'Professional roofing services estimate' as notes
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM estimates e WHERE e.customer_id = c.id
)
LIMIT 3;

-- 3. Create real invoices for existing jobs
INSERT INTO invoices (
    job_id,
    customer_id,
    invoice_number,
    status,
    amount_cents,
    tax_cents,
    total_cents,
    due_date,
    notes
)
SELECT 
    j.id as job_id,
    j.customer_id,
    'INV-2025-' || LPAD((ROW_NUMBER() OVER())::text, 4, '0') as invoice_number,
    'sent' as status,
    1500000 as amount_cents,  -- $15,000
    120000 as tax_cents,       -- $1,200
    1620000 as total_cents,    -- $16,200
    CURRENT_DATE + INTERVAL '30 days' as due_date,
    'Professional roofing services - ' || j.name as notes
FROM jobs j
WHERE NOT EXISTS (
    SELECT 1 FROM invoices i WHERE i.job_id = j.id
)
LIMIT 3;

-- 4. Add active subscriptions
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
    'MyRoofGenius Pro' as plan_name,
    'professional' as plan_tier,
    7900 as price_cents,  -- $79/month
    'active',
    CURRENT_DATE - INTERVAL '15 days',
    CURRENT_DATE + INTERVAL '15 days'
FROM app_users u
WHERE email IN ('admin@brainops.com', 'test@brainops.com')
AND NOT EXISTS (
    SELECT 1 FROM subscriptions s WHERE s.user_id = u.id
);

-- 5. Add more realistic products with proper pricing
UPDATE products 
SET price_cents = CASE
    WHEN name LIKE '%Inspection%' THEN 29900  -- $299
    WHEN name LIKE '%Maintenance%' THEN 99900  -- $999
    WHEN name LIKE '%Emergency%' THEN 149900  -- $1499
    WHEN name LIKE '%Shingles%' THEN 8999     -- $89.99
    WHEN name LIKE '%Nailer%' THEN 39999      -- $399.99
    ELSE 9900  -- $99 default
END
WHERE price_cents = 0 OR price_cents IS NULL;

-- 6. Show results
SELECT 'Data Population Complete' as status;

SELECT 
    'employees' as table_name, COUNT(*) as count FROM employees
UNION ALL
SELECT 'estimates', COUNT(*) FROM estimates
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'products with price', COUNT(*) FROM products WHERE price_cents > 0
ORDER BY table_name;

COMMIT;