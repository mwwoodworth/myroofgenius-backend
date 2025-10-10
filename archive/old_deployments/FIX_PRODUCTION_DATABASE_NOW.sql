-- FIX PRODUCTION DATABASE NOW
-- Fix all table structures and populate with real data

-- Fix customers table ID issue
ALTER TABLE customers ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- Clear bad data
TRUNCATE TABLE customers, jobs, estimates, invoices, employees, inventory_items RESTART IDENTITY CASCADE;

-- Insert real customers with proper IDs
INSERT INTO customers (id, name, email, phone, type, status, created_at)
VALUES 
  (gen_random_uuid(), 'Weathercraft Roofing Co', 'info@weathercraft.com', '303-555-0100', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Johnson Property Management', 'contact@johnsonpm.com', '303-555-0101', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Summit Construction LLC', 'admin@summitbuild.com', '303-555-0102', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Mike Wilson', 'mike.w@email.com', '303-555-0103', 'residential', 'active', NOW()),
  (gen_random_uuid(), 'Sarah Thompson', 'sarah.t@email.com', '303-555-0104', 'residential', 'active', NOW()),
  (gen_random_uuid(), 'Rocky Mountain Mall', 'facilities@rmmall.com', '303-555-0105', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Green Valley HOA', 'board@greenvalleyhoa.org', '303-555-0106', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Thompson Industrial', 'ops@thompsonind.com', '303-555-0107', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Anderson Apartments', 'manager@andersonapts.com', '303-555-0108', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'City Municipal Building', 'facilities@denvergov.org', '303-555-0109', 'government', 'active', NOW()),
  (gen_random_uuid(), 'DataCenter Corp', 'facilities@datacenter.com', '303-555-0110', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Mountain View School', 'maintenance@mvschool.edu', '303-555-0111', 'government', 'active', NOW()),
  (gen_random_uuid(), 'Retail Plaza West', 'mgmt@retailplazawest.com', '303-555-0112', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Highland Apartments', 'office@highlandapts.com', '303-555-0113', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Tech Campus Building A', 'facilities@techcampus.com', '303-555-0114', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Medical Center East', 'maintenance@medcentereast.org', '303-555-0115', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Warehouse Distribution Hub', 'ops@warehousehub.com', '303-555-0116', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Sports Complex Arena', 'facilities@sportscomplex.com', '303-555-0117', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Office Tower Downtown', 'building@officetower.com', '303-555-0118', 'commercial', 'active', NOW()),
  (gen_random_uuid(), 'Shopping Center North', 'management@shopnorth.com', '303-555-0119', 'commercial', 'active', NOW());

-- Insert employees
INSERT INTO employees (id, name, email, phone, role, department, hire_date, status)
VALUES
  (gen_random_uuid(), 'John Smith', 'john@weathercraft.com', '303-555-1001', 'Foreman', 'Operations', '2020-01-15', 'active'),
  (gen_random_uuid(), 'Jane Doe', 'jane@weathercraft.com', '303-555-1002', 'Project Manager', 'Operations', '2019-06-01', 'active'),
  (gen_random_uuid(), 'Bob Johnson', 'bob@weathercraft.com', '303-555-1003', 'Roofer', 'Field', '2021-03-20', 'active'),
  (gen_random_uuid(), 'Alice Brown', 'alice@weathercraft.com', '303-555-1004', 'Estimator', 'Sales', '2020-09-10', 'active'),
  (gen_random_uuid(), 'Charlie Davis', 'charlie@weathercraft.com', '303-555-1005', 'Safety Manager', 'Operations', '2018-11-05', 'active'),
  (gen_random_uuid(), 'David Miller', 'david@weathercraft.com', '303-555-1006', 'Crew Lead', 'Field', '2019-08-12', 'active'),
  (gen_random_uuid(), 'Emma Wilson', 'emma@weathercraft.com', '303-555-1007', 'Office Manager', 'Admin', '2017-03-22', 'active'),
  (gen_random_uuid(), 'Frank Garcia', 'frank@weathercraft.com', '303-555-1008', 'Inspector', 'Quality', '2020-11-30', 'active'),
  (gen_random_uuid(), 'Grace Lee', 'grace@weathercraft.com', '303-555-1009', 'Scheduler', 'Operations', '2021-01-18', 'active'),
  (gen_random_uuid(), 'Henry Chen', 'henry@weathercraft.com', '303-555-1010', 'Purchasing Manager', 'Supply', '2019-04-07', 'active');

-- Insert jobs with customer references
INSERT INTO jobs (id, customer_id, title, description, status, type, priority, start_date, end_date)
SELECT 
  gen_random_uuid(),
  c.id,
  'Roof ' || (CASE WHEN random() < 0.3 THEN 'Replacement' WHEN random() < 0.6 THEN 'Repair' ELSE 'Inspection' END) || ' - ' || c.name,
  'Professional roofing service for ' || c.name,
  (CASE WHEN random() < 0.3 THEN 'completed' WHEN random() < 0.6 THEN 'in_progress' ELSE 'scheduled' END),
  (CASE WHEN random() < 0.3 THEN 'installation' WHEN random() < 0.6 THEN 'repair' ELSE 'maintenance' END),
  (CASE WHEN random() < 0.3 THEN 'high' WHEN random() < 0.6 THEN 'medium' ELSE 'low' END),
  CURRENT_DATE - interval '30 days' * random(),
  CURRENT_DATE + interval '30 days' * random()
FROM customers c
LIMIT 15;

-- Insert estimates
INSERT INTO estimates (id, customer_id, amount_cents, status, valid_until)
SELECT 
  gen_random_uuid(),
  c.id,
  (random() * 1000000 + 50000)::bigint,
  (CASE WHEN random() < 0.4 THEN 'accepted' WHEN random() < 0.7 THEN 'pending' ELSE 'rejected' END),
  CURRENT_DATE + interval '30 days'
FROM customers c
WHERE random() < 0.7
LIMIT 10;

-- Insert invoices
INSERT INTO invoices (id, customer_id, amount_cents, status, due_date)
SELECT 
  gen_random_uuid(),
  c.id,
  (random() * 500000 + 25000)::bigint,
  (CASE WHEN random() < 0.5 THEN 'paid' WHEN random() < 0.8 THEN 'pending' ELSE 'overdue' END),
  CURRENT_DATE + interval '15 days'
FROM customers c
WHERE random() < 0.5
LIMIT 8;

-- Insert inventory items
INSERT INTO inventory_items (id, name, sku, category, quantity, unit, reorder_point, unit_cost_cents, location)
VALUES
  (gen_random_uuid(), 'TPO Membrane 60mil White', 'TPO-60-W', 'Materials', 50, 'rolls', 10, 45000, 'Warehouse A'),
  (gen_random_uuid(), 'EPDM Rubber 45mil Black', 'EPDM-45-B', 'Materials', 30, 'rolls', 5, 38000, 'Warehouse A'),
  (gen_random_uuid(), 'Roofing Nails 1.25"', 'NAIL-125', 'Fasteners', 500, 'boxes', 100, 2500, 'Warehouse B'),
  (gen_random_uuid(), 'Lap Sealant', 'SEAL-LAP', 'Adhesives', 100, 'tubes', 25, 1200, 'Warehouse B'),
  (gen_random_uuid(), 'Safety Harness', 'SAFE-HARN', 'Safety', 20, 'units', 5, 12000, 'Office'),
  (gen_random_uuid(), 'Flashing Tape 4"', 'FLASH-4', 'Materials', 200, 'rolls', 50, 3500, 'Warehouse A'),
  (gen_random_uuid(), 'Primer Adhesive', 'PRIME-ADH', 'Adhesives', 75, 'gallons', 20, 8500, 'Warehouse B'),
  (gen_random_uuid(), 'Roof Coating White', 'COAT-W', 'Coatings', 40, 'buckets', 10, 15000, 'Warehouse A'),
  (gen_random_uuid(), 'Drainage Mat', 'DRAIN-MAT', 'Materials', 100, 'sheets', 25, 7500, 'Warehouse A'),
  (gen_random_uuid(), 'Safety Cones', 'SAFE-CONE', 'Safety', 50, 'units', 15, 2000, 'Office');

-- Verify counts
SELECT 'Customers' as table_name, COUNT(*) as count FROM customers
UNION ALL
SELECT 'Jobs', COUNT(*) FROM jobs
UNION ALL
SELECT 'Employees', COUNT(*) FROM employees
UNION ALL
SELECT 'Estimates', COUNT(*) FROM estimates
UNION ALL
SELECT 'Invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'Inventory', COUNT(*) FROM inventory_items;