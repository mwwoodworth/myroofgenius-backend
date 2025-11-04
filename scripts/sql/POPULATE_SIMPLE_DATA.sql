-- POPULATE_SIMPLE_DATA.sql
-- Simple production data population
BEGIN;

-- Insert customers
INSERT INTO customers (name, email, phone, external_id, created_at, updated_at) VALUES
('WeatherCraft Roofing', 'info@weathercraft.com', '(303) 555-0100', 'WC-001', NOW(), NOW()),
('Denver Roofing Co', 'contact@denverroofing.com', '(720) 555-0200', 'WC-002', NOW(), NOW()),
('Colorado Construction', 'sales@coloradoconstruction.com', '(303) 555-0300', 'WC-003', NOW(), NOW()),
('Mile High Builders', 'info@milehighbuilders.com', '(720) 555-0400', 'WC-004', NOW(), NOW()),
('Rocky Mountain Roofing', 'contact@rmroofing.com', '(303) 555-0500', 'WC-005', NOW(), NOW())
ON CONFLICT (external_id) DO NOTHING;

-- Insert jobs
INSERT INTO jobs (job_number, name, customer_id, status, created_at, updated_at) VALUES
('JOB-001', 'Commercial Roof Installation', (SELECT id FROM customers WHERE external_id = 'WC-001'), 'in_progress', NOW(), NOW()),
('JOB-002', 'Residential Repair', (SELECT id FROM customers WHERE external_id = 'WC-002'), 'completed', NOW(), NOW()),
('JOB-003', 'Emergency Leak Fix', (SELECT id FROM customers WHERE external_id = 'WC-003'), 'completed', NOW(), NOW()),
('JOB-004', 'Annual Inspection', (SELECT id FROM customers WHERE external_id = 'WC-004'), 'scheduled', NOW(), NOW()),
('JOB-005', 'New Construction', (SELECT id FROM customers WHERE external_id = 'WC-005'), 'in_progress', NOW(), NOW())
ON CONFLICT (job_number) DO NOTHING;

-- Insert estimates
INSERT INTO estimates (estimate_number, customer_id, status, total_cents, created_at, updated_at) VALUES
('EST-001', (SELECT id FROM customers WHERE external_id = 'WC-001'), 'accepted', 4500000, NOW(), NOW()),
('EST-002', (SELECT id FROM customers WHERE external_id = 'WC-002'), 'accepted', 1200000, NOW(), NOW()),
('EST-003', (SELECT id FROM customers WHERE external_id = 'WC-003'), 'accepted', 850000, NOW(), NOW()),
('EST-004', (SELECT id FROM customers WHERE external_id = 'WC-004'), 'sent', 350000, NOW(), NOW()),
('EST-005', (SELECT id FROM customers WHERE external_id = 'WC-005'), 'accepted', 8500000, NOW(), NOW())
ON CONFLICT (estimate_number) DO NOTHING;

-- Insert invoices
INSERT INTO invoices (invoice_number, customer_id, status, total_cents, created_at, updated_at) VALUES
('INV-001', (SELECT id FROM customers WHERE external_id = 'WC-002'), 'paid', 1200000, NOW(), NOW()),
('INV-002', (SELECT id FROM customers WHERE external_id = 'WC-003'), 'paid', 850000, NOW(), NOW()),
('INV-003', (SELECT id FROM customers WHERE external_id = 'WC-001'), 'sent', 2250000, NOW(), NOW())
ON CONFLICT (invoice_number) DO NOTHING;

-- Summary
SELECT 
    'Data Populated' as status,
    (SELECT COUNT(*) FROM customers) as customers,
    (SELECT COUNT(*) FROM jobs) as jobs,
    (SELECT COUNT(*) FROM estimates) as estimates,
    (SELECT COUNT(*) FROM invoices) as invoices;

COMMIT;