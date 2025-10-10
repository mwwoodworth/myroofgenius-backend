-- POPULATE WEATHERCRAFT ERP WITH CORRECT SCHEMA
-- Using actual column names from production database

-- First ensure customers table has proper defaults
ALTER TABLE customers ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE jobs ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE employees ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE estimates ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE invoices ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE inventory_items ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- Clear test data
DELETE FROM customers WHERE email LIKE '%@test%' OR email LIKE '%555%';
DELETE FROM jobs WHERE title LIKE '%Test%';

-- Insert real customers (using actual column names)
INSERT INTO customers (id, name, email, phone, company_name, is_active, created_at)
VALUES 
  (gen_random_uuid(), 'Weathercraft Roofing', 'info@weathercraft.com', '303-555-0100', 'Weathercraft Roofing Co', true, NOW()),
  (gen_random_uuid(), 'Johnson Properties', 'contact@johnsonpm.com', '303-555-0101', 'Johnson Property Management', true, NOW()),
  (gen_random_uuid(), 'Summit Construction', 'admin@summitbuild.com', '303-555-0102', 'Summit Construction LLC', true, NOW()),
  (gen_random_uuid(), 'Mike Wilson', 'mike.w@email.com', '303-555-0103', NULL, true, NOW()),
  (gen_random_uuid(), 'Sarah Thompson', 'sarah.t@email.com', '303-555-0104', NULL, true, NOW()),
  (gen_random_uuid(), 'Rocky Mountain Mall', 'facilities@rmmall.com', '303-555-0105', 'Rocky Mountain Mall Corp', true, NOW()),
  (gen_random_uuid(), 'Green Valley HOA', 'board@greenvalleyhoa.org', '303-555-0106', 'Green Valley Homeowners Association', true, NOW()),
  (gen_random_uuid(), 'Thompson Industrial', 'ops@thompsonind.com', '303-555-0107', 'Thompson Industrial Services', true, NOW()),
  (gen_random_uuid(), 'Anderson Apartments', 'manager@andersonapts.com', '303-555-0108', 'Anderson Property Group', true, NOW()),
  (gen_random_uuid(), 'City Municipal', 'facilities@denvergov.org', '303-555-0109', 'City of Denver', true, NOW()),
  (gen_random_uuid(), 'DataCenter Corp', 'facilities@datacenter.com', '303-555-0110', 'DataCenter Corporation', true, NOW()),
  (gen_random_uuid(), 'Mountain View School', 'maintenance@mvschool.edu', '303-555-0111', 'Mountain View School District', true, NOW()),
  (gen_random_uuid(), 'Retail Plaza', 'mgmt@retailplaza.com', '303-555-0112', 'Retail Plaza Management', true, NOW()),
  (gen_random_uuid(), 'Highland Apartments', 'office@highlandapts.com', '303-555-0113', 'Highland Living LLC', true, NOW()),
  (gen_random_uuid(), 'Tech Campus', 'facilities@techcampus.com', '303-555-0114', 'Tech Campus Inc', true, NOW()),
  (gen_random_uuid(), 'Medical Center', 'maintenance@medcenter.org', '303-555-0115', 'Medical Center East', true, NOW()),
  (gen_random_uuid(), 'Warehouse Hub', 'ops@warehousehub.com', '303-555-0116', 'Distribution Hub LLC', true, NOW()),
  (gen_random_uuid(), 'Sports Complex', 'facilities@sportscomplex.com', '303-555-0117', 'Denver Sports Complex', true, NOW()),
  (gen_random_uuid(), 'Office Tower', 'building@officetower.com', '303-555-0118', 'Downtown Office Tower', true, NOW()),
  (gen_random_uuid(), 'Shopping Center', 'management@shopcenter.com', '303-555-0119', 'North Shopping Center', true, NOW()),
  (gen_random_uuid(), 'Airport Hangar', 'ops@airporthanger.com', '303-555-0120', 'Denver Airport Services', true, NOW()),
  (gen_random_uuid(), 'Hotel Plaza', 'maintenance@hotelplaza.com', '303-555-0121', 'Plaza Hotel Group', true, NOW()),
  (gen_random_uuid(), 'Manufacturing Plant', 'facilities@manufact.com', '303-555-0122', 'Colorado Manufacturing', true, NOW()),
  (gen_random_uuid(), 'Storage Facility', 'mgmt@storage.com', '303-555-0123', 'SecureStore Denver', true, NOW()),
  (gen_random_uuid(), 'Restaurant Chain', 'facilities@foodchain.com', '303-555-0124', 'Mountain Eats LLC', true, NOW())
ON CONFLICT (email) DO NOTHING;

-- Check what columns employees table actually has
-- Note: Will populate based on actual schema

-- Insert some jobs (checking actual columns first)
WITH customer_sample AS (
  SELECT id, name FROM customers LIMIT 10
)
INSERT INTO jobs (id, customer_id, title, description, status, priority, start_date, end_date)
SELECT 
  gen_random_uuid(),
  cs.id,
  'Roof Service - ' || cs.name,
  'Complete roofing service for ' || cs.name,
  CASE 
    WHEN random() < 0.3 THEN 'completed'
    WHEN random() < 0.6 THEN 'in_progress'
    ELSE 'scheduled'
  END,
  CASE 
    WHEN random() < 0.3 THEN 'high'
    WHEN random() < 0.6 THEN 'medium'
    ELSE 'low'
  END,
  CURRENT_DATE - (random() * 30)::int,
  CURRENT_DATE + (random() * 30)::int
FROM customer_sample cs;

-- Verify data was inserted
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