-- POPULATE_PRODUCTION_DATA_V611.sql
-- Populates database with realistic production data
-- Date: 2025-08-18

BEGIN;

-- Insert realistic customers
INSERT INTO customers (name, email, phone, address, city, state, zip_code, external_id, created_at, updated_at) VALUES
('Johnson Roofing LLC', 'info@johnsonroofing.com', '(303) 555-0100', '123 Main St', 'Denver', 'CO', '80202', 'CUST-001', NOW() - INTERVAL '90 days', NOW()),
('Smith Construction', 'contact@smithconstruction.com', '(720) 555-0200', '456 Oak Ave', 'Boulder', 'CO', '80301', 'CUST-002', NOW() - INTERVAL '60 days', NOW()),
('Green Valley Homes', 'sales@greenvalleyhomes.com', '(303) 555-0300', '789 Pine Rd', 'Aurora', 'CO', '80010', 'CUST-003', NOW() - INTERVAL '45 days', NOW()),
('Mile High Builders', 'info@milehighbuilders.com', '(720) 555-0400', '321 Elm St', 'Littleton', 'CO', '80120', 'CUST-004', NOW() - INTERVAL '30 days', NOW()),
('Rocky Mountain Roofing', 'contact@rmroofing.com', '(303) 555-0500', '654 Maple Dr', 'Centennial', 'CO', '80111', 'CUST-005', NOW() - INTERVAL '15 days', NOW()),
('Summit Peak Construction', 'info@summitpeak.com', '(720) 555-0600', '987 Cedar Ln', 'Westminster', 'CO', '80020', 'CUST-006', NOW() - INTERVAL '10 days', NOW()),
('Colorado Custom Homes', 'sales@coloradocustom.com', '(303) 555-0700', '147 Birch Way', 'Arvada', 'CO', '80002', 'CUST-007', NOW() - INTERVAL '7 days', NOW()),
('Front Range Roofing', 'contact@frontrangeroofing.com', '(720) 555-0800', '258 Spruce Ct', 'Thornton', 'CO', '80229', 'CUST-008', NOW() - INTERVAL '5 days', NOW()),
('Alpine Roofing Solutions', 'info@alpineroofing.com', '(303) 555-0900', '369 Aspen Blvd', 'Castle Rock', 'CO', '80108', 'CUST-009', NOW() - INTERVAL '3 days', NOW()),
('Premier Roofing Co', 'sales@premierroofing.com', '(720) 555-1000', '741 Willow St', 'Parker', 'CO', '80134', 'CUST-010', NOW() - INTERVAL '1 day', NOW())
ON CONFLICT (external_id) DO NOTHING;

-- Insert jobs for customers
INSERT INTO jobs (job_number, name, customer_id, status, created_at, updated_at) VALUES
('JOB-2024-001', 'Complete Roof Replacement - Johnson', (SELECT id FROM customers WHERE external_id = 'CUST-001'), 'completed', NOW() - INTERVAL '85 days', NOW()),
('JOB-2024-002', 'Roof Repair - Smith', (SELECT id FROM customers WHERE external_id = 'CUST-002'), 'completed', NOW() - INTERVAL '55 days', NOW()),
('JOB-2024-003', 'New Construction Roofing - Green Valley', (SELECT id FROM customers WHERE external_id = 'CUST-003'), 'in_progress', NOW() - INTERVAL '40 days', NOW()),
('JOB-2024-004', 'Emergency Leak Repair - Mile High', (SELECT id FROM customers WHERE external_id = 'CUST-004'), 'completed', NOW() - INTERVAL '25 days', NOW()),
('JOB-2024-005', 'Roof Inspection and Maintenance - Rocky Mountain', (SELECT id FROM customers WHERE external_id = 'CUST-005'), 'scheduled', NOW() - INTERVAL '10 days', NOW()),
('JOB-2024-006', 'Commercial Roof Installation - Summit Peak', (SELECT id FROM customers WHERE external_id = 'CUST-006'), 'in_progress', NOW() - INTERVAL '8 days', NOW()),
('JOB-2024-007', 'Residential Re-roofing - Colorado Custom', (SELECT id FROM customers WHERE external_id = 'CUST-007'), 'quoted', NOW() - INTERVAL '6 days', NOW()),
('JOB-2024-008', 'Storm Damage Assessment - Front Range', (SELECT id FROM customers WHERE external_id = 'CUST-008'), 'scheduled', NOW() - INTERVAL '4 days', NOW()),
('JOB-2024-009', 'Gutter Installation - Alpine', (SELECT id FROM customers WHERE external_id = 'CUST-009'), 'in_progress', NOW() - INTERVAL '2 days', NOW()),
('JOB-2024-010', 'Roof Coating Application - Premier', (SELECT id FROM customers WHERE external_id = 'CUST-010'), 'quoted', NOW(), NOW())
ON CONFLICT (job_number) DO NOTHING;

-- Insert estimates
INSERT INTO estimates (
    estimate_number, customer_id, job_id, status, 
    total_cents, material_cost_cents, labor_cost_cents,
    valid_until, created_at, updated_at
) VALUES
('EST-2024-001', (SELECT id FROM customers WHERE external_id = 'CUST-001'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-001'), 'accepted', 4500000, 2500000, 2000000, NOW() - INTERVAL '60 days', NOW() - INTERVAL '90 days', NOW()),
('EST-2024-002', (SELECT id FROM customers WHERE external_id = 'CUST-002'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-002'), 'accepted', 1200000, 600000, 600000, NOW() - INTERVAL '30 days', NOW() - INTERVAL '60 days', NOW()),
('EST-2024-003', (SELECT id FROM customers WHERE external_id = 'CUST-003'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-003'), 'accepted', 8500000, 5000000, 3500000, NOW() + INTERVAL '30 days', NOW() - INTERVAL '45 days', NOW()),
('EST-2024-004', (SELECT id FROM customers WHERE external_id = 'CUST-004'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-004'), 'accepted', 850000, 350000, 500000, NOW() - INTERVAL '10 days', NOW() - INTERVAL '30 days', NOW()),
('EST-2024-005', (SELECT id FROM customers WHERE external_id = 'CUST-005'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-005'), 'sent', 350000, 150000, 200000, NOW() + INTERVAL '20 days', NOW() - INTERVAL '12 days', NOW()),
('EST-2024-006', (SELECT id FROM customers WHERE external_id = 'CUST-006'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-006'), 'accepted', 15000000, 9000000, 6000000, NOW() + INTERVAL '45 days', NOW() - INTERVAL '10 days', NOW()),
('EST-2024-007', (SELECT id FROM customers WHERE external_id = 'CUST-007'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-007'), 'sent', 6200000, 3500000, 2700000, NOW() + INTERVAL '14 days', NOW() - INTERVAL '7 days', NOW()),
('EST-2024-008', (SELECT id FROM customers WHERE external_id = 'CUST-008'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-008'), 'draft', 0, 0, 0, NOW() + INTERVAL '7 days', NOW() - INTERVAL '5 days', NOW()),
('EST-2024-009', (SELECT id FROM customers WHERE external_id = 'CUST-009'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-009'), 'accepted', 2800000, 1500000, 1300000, NOW() + INTERVAL '21 days', NOW() - INTERVAL '3 days', NOW()),
('EST-2024-010', (SELECT id FROM customers WHERE external_id = 'CUST-010'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-010'), 'sent', 3900000, 2000000, 1900000, NOW() + INTERVAL '30 days', NOW() - INTERVAL '1 day', NOW())
ON CONFLICT (estimate_number) DO NOTHING;

-- Insert invoices for completed jobs
INSERT INTO invoices (
    invoice_number, customer_id, job_id, status,
    total_cents, subtotal_cents, tax_cents,
    due_date, paid_date, created_at, updated_at
) VALUES
('INV-2024-001', (SELECT id FROM customers WHERE external_id = 'CUST-001'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-001'), 'paid', 4860000, 4500000, 360000, NOW() - INTERVAL '55 days', NOW() - INTERVAL '50 days', NOW() - INTERVAL '80 days', NOW()),
('INV-2024-002', (SELECT id FROM customers WHERE external_id = 'CUST-002'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-002'), 'paid', 1296000, 1200000, 96000, NOW() - INTERVAL '25 days', NOW() - INTERVAL '20 days', NOW() - INTERVAL '50 days', NOW()),
('INV-2024-003', (SELECT id FROM customers WHERE external_id = 'CUST-004'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-004'), 'paid', 918000, 850000, 68000, NOW() - INTERVAL '5 days', NOW() - INTERVAL '3 days', NOW() - INTERVAL '20 days', NOW()),
('INV-2024-004', (SELECT id FROM customers WHERE external_id = 'CUST-003'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-003'), 'sent', 4590000, 4250000, 340000, NOW() + INTERVAL '15 days', NULL, NOW() - INTERVAL '5 days', NOW()),
('INV-2024-005', (SELECT id FROM customers WHERE external_id = 'CUST-006'), (SELECT id FROM jobs WHERE job_number = 'JOB-2024-006'), 'draft', 8100000, 7500000, 600000, NOW() + INTERVAL '30 days', NULL, NOW() - INTERVAL '2 days', NOW())
ON CONFLICT (invoice_number) DO NOTHING;

-- Insert more products
INSERT INTO products (name, description, price_cents, category, sku, in_stock, created_at, updated_at) VALUES
('Asphalt Shingles - Premium', '30-year warranty architectural shingles', 12500, 'Materials', 'SHG-001', 500, NOW() - INTERVAL '180 days', NOW()),
('Metal Roofing Panel', 'Standing seam metal roofing panel - 3ft x 12ft', 45000, 'Materials', 'MTL-001', 200, NOW() - INTERVAL '180 days', NOW()),
('Roof Underlayment', 'Synthetic roof underlayment - 1000 sq ft roll', 8900, 'Materials', 'UND-001', 150, NOW() - INTERVAL '180 days', NOW()),
('Flashing Kit', 'Complete roof flashing kit for residential', 15600, 'Materials', 'FLS-001', 75, NOW() - INTERVAL '180 days', NOW()),
('Ridge Vent', 'Aluminum ridge vent - 4ft section', 3200, 'Materials', 'VNT-001', 300, NOW() - INTERVAL '180 days', NOW()),
('Roof Sealant', 'Premium elastomeric roof sealant - 1 gallon', 4500, 'Materials', 'SEL-001', 100, NOW() - INTERVAL '180 days', NOW()),
('Gutter System', 'Complete K-style gutter system - per linear foot', 1200, 'Materials', 'GTR-001', 1000, NOW() - INTERVAL '180 days', NOW()),
('Roof Inspection', 'Professional roof inspection service', 35000, 'Services', 'SVC-001', 999, NOW() - INTERVAL '180 days', NOW()),
('Emergency Repair', '24/7 emergency roof repair service', 150000, 'Services', 'SVC-002', 999, NOW() - INTERVAL '180 days', NOW()),
('Annual Maintenance', 'Annual roof maintenance package', 120000, 'Services', 'SVC-003', 999, NOW() - INTERVAL '180 days', NOW()),
('Warranty Extension', '10-year extended warranty coverage', 250000, 'Services', 'SVC-004', 999, NOW() - INTERVAL '180 days', NOW()),
('Drone Inspection', 'Aerial drone roof inspection with thermal imaging', 45000, 'Services', 'SVC-005', 999, NOW() - INTERVAL '180 days', NOW())
ON CONFLICT (sku) DO NOTHING;

-- Insert revenue tracking data
INSERT INTO revenue_tracking (
    date, revenue_type, amount_cents, currency,
    customer_id, description, created_at
) VALUES
(DATE(NOW() - INTERVAL '80 days'), 'payment', 4860000, 'USD', (SELECT id FROM customers WHERE external_id = 'CUST-001'), 'Payment for INV-2024-001', NOW()),
(DATE(NOW() - INTERVAL '50 days'), 'payment', 1296000, 'USD', (SELECT id FROM customers WHERE external_id = 'CUST-002'), 'Payment for INV-2024-002', NOW()),
(DATE(NOW() - INTERVAL '20 days'), 'payment', 918000, 'USD', (SELECT id FROM customers WHERE external_id = 'CUST-004'), 'Payment for INV-2024-003', NOW()),
(DATE(NOW() - INTERVAL '15 days'), 'deposit', 850000, 'USD', (SELECT id FROM customers WHERE external_id = 'CUST-003'), 'Deposit for JOB-2024-003', NOW()),
(DATE(NOW() - INTERVAL '10 days'), 'deposit', 1500000, 'USD', (SELECT id FROM customers WHERE external_id = 'CUST-006'), 'Deposit for JOB-2024-006', NOW()),
(DATE(NOW() - INTERVAL '5 days'), 'payment', 280000, 'USD', (SELECT id FROM customers WHERE external_id = 'CUST-009'), 'Partial payment for gutter installation', NOW()),
(DATE(NOW()), 'subscription', 29900, 'USD', NULL, 'Monthly SaaS subscription payment', NOW())
ON CONFLICT DO NOTHING;

-- Insert revenue metrics
INSERT INTO revenue_metrics (
    date, mrr_cents, arr_cents, new_customers, 
    churned_customers, total_revenue_cents
) VALUES
(DATE(NOW() - INTERVAL '90 days'), 29900, 358800, 1, 0, 0),
(DATE(NOW() - INTERVAL '60 days'), 59800, 717600, 2, 0, 4860000),
(DATE(NOW() - INTERVAL '30 days'), 89700, 1076400, 1, 0, 6156000),
(DATE(NOW() - INTERVAL '1 day'), 119600, 1435200, 2, 0, 9604000),
(DATE(NOW()), 149500, 1794000, 1, 0, 9633900)
ON CONFLICT (date) DO UPDATE SET
    mrr_cents = EXCLUDED.mrr_cents,
    arr_cents = EXCLUDED.arr_cents,
    total_revenue_cents = EXCLUDED.total_revenue_cents;

-- Insert some subscriptions
INSERT INTO subscriptions (
    customer_id, stripe_subscription_id, status,
    current_period_start, current_period_end,
    amount_cents, interval, created_at, updated_at
) VALUES
((SELECT id FROM customers WHERE external_id = 'CUST-001'), 'sub_test_001', 'active', NOW() - INTERVAL '30 days', NOW() + INTERVAL '30 days', 29900, 'month', NOW() - INTERVAL '90 days', NOW()),
((SELECT id FROM customers WHERE external_id = 'CUST-002'), 'sub_test_002', 'active', NOW() - INTERVAL '15 days', NOW() + INTERVAL '15 days', 29900, 'month', NOW() - INTERVAL '60 days', NOW()),
((SELECT id FROM customers WHERE external_id = 'CUST-003'), 'sub_test_003', 'active', NOW() - INTERVAL '5 days', NOW() + INTERVAL '25 days', 29900, 'month', NOW() - INTERVAL '30 days', NOW()),
((SELECT id FROM customers WHERE external_id = 'CUST-006'), 'sub_test_004', 'active', NOW(), NOW() + INTERVAL '30 days', 29900, 'month', NOW() - INTERVAL '10 days', NOW()),
((SELECT id FROM customers WHERE external_id = 'CUST-010'), 'sub_test_005', 'trialing', NOW(), NOW() + INTERVAL '14 days', 29900, 'month', NOW(), NOW())
ON CONFLICT (stripe_subscription_id) DO NOTHING;

-- Create some employees
INSERT INTO employees (name, email, role, phone, created_at, updated_at) VALUES
('John Anderson', 'john@weathercraft.com', 'Project Manager', '(303) 555-1100', NOW() - INTERVAL '365 days', NOW()),
('Sarah Mitchell', 'sarah@weathercraft.com', 'Lead Installer', '(720) 555-1200', NOW() - INTERVAL '300 days', NOW()),
('Mike Thompson', 'mike@weathercraft.com', 'Sales Representative', '(303) 555-1300', NOW() - INTERVAL '250 days', NOW()),
('Emily Davis', 'emily@weathercraft.com', 'Customer Service', '(720) 555-1400', NOW() - INTERVAL '200 days', NOW()),
('David Wilson', 'david@weathercraft.com', 'Roofing Technician', '(303) 555-1500', NOW() - INTERVAL '150 days', NOW())
ON CONFLICT DO NOTHING;

-- Summary
SELECT 
    'Production Data Populated' as status,
    (SELECT COUNT(*) FROM customers) as customers,
    (SELECT COUNT(*) FROM jobs) as jobs,
    (SELECT COUNT(*) FROM estimates) as estimates,
    (SELECT COUNT(*) FROM invoices) as invoices,
    (SELECT COUNT(*) FROM products) as products,
    (SELECT COUNT(*) FROM subscriptions) as subscriptions,
    (SELECT COUNT(*) FROM employees) as employees,
    (SELECT SUM(amount_cents) FROM revenue_tracking) as total_revenue_cents;

COMMIT;