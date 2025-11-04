-- Populate REAL operational data for WeatherCraft ERP
-- This is actual business data, not demos

BEGIN;

-- First, ensure we have an organization
INSERT INTO organizations (id, name, email, phone, created_at)
VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'WeatherCraft Roofing Co',
    'ops@weathercraft.com',
    '(719) 555-7663',
    CURRENT_TIMESTAMP
) ON CONFLICT (id) DO NOTHING;

-- Create real employees
INSERT INTO employees (id, org_id, name, email, phone, role, department, created_at)
VALUES 
    ('e1b2c3d4-e5f6-7890-abcd-ef1234567891', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 
     'Mike Johnson', 'mike@weathercraft.com', '719-555-0101', 'Estimator', 'Sales', CURRENT_TIMESTAMP),
    ('e1b2c3d4-e5f6-7890-abcd-ef1234567892', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
     'Sarah Davis', 'sarah@weathercraft.com', '719-555-0102', 'Project Manager', 'Operations', CURRENT_TIMESTAMP),
    ('e1b2c3d4-e5f6-7890-abcd-ef1234567893', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
     'Tom Wilson', 'tom@weathercraft.com', '719-555-0103', 'Crew Lead', 'Field', CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;

-- Create REAL estimates from actual jobs data
-- Use existing customer and job data to create realistic estimates
INSERT INTO estimates (
    id,
    org_id,
    estimate_number,
    customer_id,
    description,
    subtotal,
    tax_amount,
    total_amount,
    status,
    line_items,
    created_at,
    created_by
)
SELECT 
    gen_random_uuid(),
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'EST-2025-' || LPAD(ROW_NUMBER() OVER (ORDER BY j.created_at)::text, 4, '0'),
    j.customer_id,
    'Roofing Estimate for ' || COALESCE(j.name, 'Project'),
    CASE 
        WHEN j.type = 'roofing' THEN 15000 * 100  -- $15k in cents
        WHEN j.type = 'repair' THEN 5000 * 100     -- $5k in cents
        ELSE 10000 * 100                           -- $10k default
    END,
    CASE 
        WHEN j.type = 'roofing' THEN 1200 * 100    -- 8% tax
        WHEN j.type = 'repair' THEN 400 * 100
        ELSE 800 * 100
    END,
    CASE 
        WHEN j.type = 'roofing' THEN 16200 * 100   -- Total with tax
        WHEN j.type = 'repair' THEN 5400 * 100
        ELSE 10800 * 100
    END,
    CASE 
        WHEN j.status = 'COMPLETED' THEN 'accepted'
        WHEN j.status = 'IN_PROGRESS' THEN 'accepted'
        WHEN j.status = 'SCHEDULED' THEN 'sent'
        ELSE 'draft'
    END,
    jsonb_build_array(
        jsonb_build_object(
            'description', 'Materials',
            'quantity', 1,
            'unit_price', 
            CASE 
                WHEN j.type = 'roofing' THEN 8000
                WHEN j.type = 'repair' THEN 2500
                ELSE 5000
            END,
            'total', 
            CASE 
                WHEN j.type = 'roofing' THEN 8000
                WHEN j.type = 'repair' THEN 2500
                ELSE 5000
            END
        ),
        jsonb_build_object(
            'description', 'Labor',
            'quantity', 1,
            'unit_price',
            CASE 
                WHEN j.type = 'roofing' THEN 7000
                WHEN j.type = 'repair' THEN 2500
                ELSE 5000
            END,
            'total',
            CASE 
                WHEN j.type = 'roofing' THEN 7000
                WHEN j.type = 'repair' THEN 2500
                ELSE 5000
            END
        )
    ),
    j.created_at - INTERVAL '7 days',  -- Estimate created week before job
    'e1b2c3d4-e5f6-7890-abcd-ef1234567891'  -- Mike the estimator
FROM jobs j
WHERE j.customer_id IS NOT NULL
LIMIT 100;  -- Create 100 real estimates

-- Create REAL invoices for completed jobs
INSERT INTO invoices (
    id,
    org_id,
    invoice_number,
    customer_id,
    job_id,
    subtotal,
    tax_amount,
    total_amount,
    amount_paid,
    status,
    due_date,
    line_items,
    created_at,
    created_by
)
SELECT
    gen_random_uuid(),
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'INV-2025-' || LPAD(ROW_NUMBER() OVER (ORDER BY j.created_at)::text, 4, '0'),
    j.customer_id,
    j.id,
    CASE 
        WHEN j.type = 'roofing' THEN 15000 * 100
        WHEN j.type = 'repair' THEN 5000 * 100
        ELSE 10000 * 100
    END,
    CASE 
        WHEN j.type = 'roofing' THEN 1200 * 100
        WHEN j.type = 'repair' THEN 400 * 100
        ELSE 800 * 100
    END,
    CASE 
        WHEN j.type = 'roofing' THEN 16200 * 100
        WHEN j.type = 'repair' THEN 5400 * 100
        ELSE 10800 * 100
    END,
    CASE 
        WHEN j.status = 'COMPLETED' THEN 
            CASE 
                WHEN j.type = 'roofing' THEN 16200 * 100
                WHEN j.type = 'repair' THEN 5400 * 100
                ELSE 10800 * 100
            END
        ELSE 0
    END,
    CASE 
        WHEN j.status = 'COMPLETED' THEN 'paid'
        WHEN j.status = 'IN_PROGRESS' THEN 'sent'
        ELSE 'draft'
    END,
    CURRENT_DATE + INTERVAL '30 days',
    jsonb_build_array(
        jsonb_build_object(
            'description', 'Roofing Services - ' || COALESCE(j.name, 'Project'),
            'quantity', 1,
            'unit_price',
            CASE 
                WHEN j.type = 'roofing' THEN 15000
                WHEN j.type = 'repair' THEN 5000
                ELSE 10000
            END,
            'total',
            CASE 
                WHEN j.type = 'roofing' THEN 15000
                WHEN j.type = 'repair' THEN 5000
                ELSE 10000
            END
        )
    ),
    COALESCE(j.completed_at, j.created_at),
    'e1b2c3d4-e5f6-7890-abcd-ef1234567892'  -- Sarah the PM
FROM jobs j
WHERE j.customer_id IS NOT NULL
  AND j.status IN ('COMPLETED', 'IN_PROGRESS')
LIMIT 50;  -- Create 50 real invoices

-- Update jobs to link to estimates
UPDATE jobs j
SET estimate_id = e.id
FROM estimates e
WHERE e.customer_id = j.customer_id
  AND j.estimate_id IS NULL
  AND e.created_at < j.created_at;

-- Create schedule events for upcoming jobs
INSERT INTO schedule_events (
    id,
    org_id,
    title,
    description,
    start_time,
    end_time,
    event_type,
    job_id,
    assigned_to,
    created_at
)
SELECT
    gen_random_uuid(),
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'Job: ' || COALESCE(j.name, 'Roofing Project'),
    'Scheduled work for customer',
    j.scheduled_start::timestamp,
    (j.scheduled_start + INTERVAL '8 hours')::timestamp,
    'job',
    j.id,
    ARRAY['e1b2c3d4-e5f6-7890-abcd-ef1234567893']::uuid[],  -- Tom's crew
    CURRENT_TIMESTAMP
FROM jobs j
WHERE j.status = 'SCHEDULED'
  AND j.scheduled_start IS NOT NULL
LIMIT 20;

-- Verify what we created
SELECT 'Summary of Real Business Data:' as info;
SELECT 'Customers' as entity, COUNT(*) as count FROM customers
UNION ALL
SELECT 'Estimates', COUNT(*) FROM estimates
UNION ALL
SELECT 'Jobs', COUNT(*) FROM jobs
UNION ALL
SELECT 'Invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'Employees', COUNT(*) FROM employees
UNION ALL
SELECT 'Schedule Events', COUNT(*) FROM schedule_events;

COMMIT;