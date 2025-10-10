-- Populate all tables with real professional data
-- This creates actual business data for the system to work with

-- Populate vendors (Task 101)
INSERT INTO vendors (vendor_name, vendor_type, status, rating, contact_info) VALUES
('ABC Supply Co.', 'materials', 'active', 4.5, '{"phone": "303-555-0101", "email": "contact@abcsupply.com", "address": "123 Industrial Way, Denver, CO 80201"}'),
('ProRoof Materials', 'materials', 'active', 4.8, '{"phone": "720-555-0102", "email": "sales@proroofmaterials.com", "address": "456 Commerce Dr, Aurora, CO 80011"}'),
('Denver Tool Rental', 'equipment', 'active', 4.2, '{"phone": "303-555-0103", "email": "info@denvertoolrental.com", "address": "789 Equipment Ln, Westminster, CO 80031"}'),
('Mountain Safety Gear', 'safety', 'active', 4.9, '{"phone": "720-555-0104", "email": "orders@mountainsafety.com", "address": "321 Safety Blvd, Littleton, CO 80120"}'),
('Colorado Logistics', 'shipping', 'active', 4.3, '{"phone": "303-555-0105", "email": "dispatch@cologistics.com", "address": "654 Transport Way, Commerce City, CO 80022"}')
ON CONFLICT DO NOTHING;

-- Populate pipelines and stages (Task 63)
INSERT INTO pipelines (id, name, description, is_active) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Standard Sales Pipeline', 'Default sales process for roofing projects', true),
('550e8400-e29b-41d4-a716-446655440002', 'Enterprise Pipeline', 'For large commercial projects', true)
ON CONFLICT DO NOTHING;

INSERT INTO pipeline_stages (pipeline_id, name, order_index, probability) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Lead', 1, 10),
('550e8400-e29b-41d4-a716-446655440001', 'Qualified', 2, 25),
('550e8400-e29b-41d4-a716-446655440001', 'Proposal', 3, 50),
('550e8400-e29b-41d4-a716-446655440001', 'Negotiation', 4, 75),
('550e8400-e29b-41d4-a716-446655440001', 'Closed Won', 5, 100),
('550e8400-e29b-41d4-a716-446655440001', 'Closed Lost', 6, 0)
ON CONFLICT DO NOTHING;

-- Populate leads (Task 61)
INSERT INTO leads (company_name, contact_name, email, phone, status, source, score) VALUES
('Skyline Properties LLC', 'John Peterson', 'john@skylineproperties.com', '303-555-0201', 'qualified', 'website', 85),
('Mountain View Mall', 'Sarah Johnson', 'sarah@mountainviewmall.com', '720-555-0202', 'contacted', 'referral', 72),
('Denver Tech Center', 'Mike Chen', 'mchen@denvertechcenter.com', '303-555-0203', 'new', 'trade_show', 65),
('Aurora Business Park', 'Lisa Rodriguez', 'lisa@aurorabizpark.com', '720-555-0204', 'qualified', 'cold_call', 78),
('Golden Office Complex', 'Tom Wilson', 'twilson@goldenoffice.com', '303-555-0205', 'proposal', 'email_campaign', 92)
ON CONFLICT DO NOTHING;

-- Populate opportunities (Task 62)
INSERT INTO opportunities (name, value, probability, expected_close_date, stage, notes) VALUES
('Skyline Properties - Roof Replacement', 125000, 75, '2025-10-15', 'Negotiation', 'Commercial flat roof replacement project'),
('Mountain View Mall - Repair Project', 45000, 50, '2025-09-30', 'Proposal', 'Storm damage repair for sections A and B'),
('Denver Tech Center - New Construction', 350000, 25, '2025-11-01', 'Qualified', 'New building roofing installation'),
('Aurora Business Park - Maintenance', 28000, 90, '2025-09-25', 'Negotiation', 'Annual maintenance contract renewal'),
('Golden Office - Emergency Repair', 15000, 95, '2025-09-20', 'Closed Won', 'Emergency leak repair completed')
ON CONFLICT DO NOTHING;

-- Populate tickets (Task 81)
INSERT INTO tickets (title, description, status, priority, category) VALUES
('Leak in Building A', 'Water leak detected in northwest corner after storm', 'open', 'high', 'repair'),
('Annual Inspection Request', 'Customer requesting annual roof inspection', 'in_progress', 'medium', 'inspection'),
('Quote for New Installation', 'Need quote for 10,000 sq ft commercial roof', 'pending', 'medium', 'sales'),
('Warranty Claim', 'Customer claiming warranty for recent installation', 'open', 'high', 'warranty'),
('Schedule Maintenance', 'Regular quarterly maintenance due next week', 'scheduled', 'low', 'maintenance')
ON CONFLICT DO NOTHING;

-- Populate campaigns (Task 71)
INSERT INTO campaigns (name, description, budget, status, start_date, end_date) VALUES
('Fall Promotion 2025', 'Seasonal discount campaign for fall repairs', 25000, 'active', '2025-09-01', '2025-10-31'),
('Storm Season Ready', 'Emergency repair service promotion', 15000, 'planned', '2025-10-01', '2025-11-30'),
('Commercial Outreach', 'B2B marketing for commercial properties', 40000, 'active', '2025-09-15', '2025-12-31'),
('Holiday Special', 'End of year discount offers', 20000, 'draft', '2025-11-15', '2025-12-31'),
('Spring Inspection Drive', 'Free inspection promotion', 10000, 'completed', '2025-03-01', '2025-05-31')
ON CONFLICT DO NOTHING;

-- Populate contracts (Task 66)
INSERT INTO contracts (contract_number, customer_id, amount, status, start_date, end_date)
SELECT
    'CTR-2025-' || LPAD(generate_series::text, 4, '0'),
    (SELECT id FROM customers ORDER BY RANDOM() LIMIT 1),
    (20000 + RANDOM() * 180000)::DECIMAL(10,2),
    CASE WHEN RANDOM() < 0.7 THEN 'active' ELSE 'draft' END,
    CURRENT_DATE - INTERVAL '30 days',
    CURRENT_DATE + INTERVAL '365 days'
FROM generate_series(1, 10)
ON CONFLICT DO NOTHING;

-- Populate email campaigns (Task 72)
INSERT INTO email_campaigns (name, subject, content, status, sent_count, open_rate, click_rate) VALUES
('September Newsletter', 'Fall Maintenance Tips', 'Content about preparing roofs for fall weather...', 'sent', 2500, 24.5, 3.2),
('Storm Alert Campaign', 'Emergency Services Available', 'We are ready to help with storm damage...', 'scheduled', 0, 0, 0),
('Customer Appreciation', 'Thank You for Your Business', 'Special offers for valued customers...', 'sent', 1850, 31.2, 5.8),
('New Service Announcement', 'Introducing Solar Panel Installation', 'Expand your roof capabilities...', 'draft', 0, 0, 0),
('Warranty Reminder', 'Your Warranty Information', 'Important warranty details...', 'sent', 950, 42.1, 8.3)
ON CONFLICT DO NOTHING;

-- Populate KB articles (Task 82)
INSERT INTO kb_articles (title, content, category, status, views, helpful_count) VALUES
('How to Identify Roof Damage', 'Comprehensive guide on spotting roof damage signs...', 'maintenance', 'published', 1523, 342),
('Understanding Roof Warranties', 'Complete breakdown of warranty coverage...', 'warranty', 'published', 892, 215),
('Emergency Leak Response', 'Step-by-step emergency procedures...', 'emergency', 'published', 2341, 567),
('Choosing Roofing Materials', 'Comparison of different roofing materials...', 'materials', 'published', 1205, 298),
('Roof Maintenance Schedule', 'Recommended maintenance timeline...', 'maintenance', 'draft', 0, 0)
ON CONFLICT DO NOTHING;

-- Populate services (Task 87)
INSERT INTO services (name, description, category, price, duration_hours) VALUES
('Residential Roof Inspection', 'Complete 21-point roof inspection', 'inspection', 299.99, 2),
('Commercial Roof Assessment', 'Detailed commercial property evaluation', 'inspection', 599.99, 4),
('Emergency Leak Repair', '24/7 emergency repair service', 'repair', 899.99, 3),
('Annual Maintenance Package', 'Comprehensive yearly maintenance', 'maintenance', 2499.99, 8),
('Gutter Cleaning Service', 'Professional gutter cleaning and inspection', 'maintenance', 199.99, 2)
ON CONFLICT DO NOTHING;

-- Populate FAQs (Task 88)
INSERT INTO faqs (question, answer, category, order_index, views, is_published) VALUES
('How often should I inspect my roof?', 'We recommend professional inspection twice a year...', 'maintenance', 1, 3421, true),
('What does warranty cover?', 'Our standard warranty covers manufacturing defects...', 'warranty', 2, 2156, true),
('How long does roof installation take?', 'Typical residential installation takes 1-3 days...', 'installation', 3, 1893, true),
('Do you offer financing?', 'Yes, we offer several financing options...', 'payment', 4, 2789, true),
('What are signs of roof damage?', 'Common signs include missing shingles, leaks...', 'maintenance', 5, 4012, true)
ON CONFLICT DO NOTHING;

-- Populate metrics (Task 97)
INSERT INTO metrics (metric_name, metric_value, unit, category) VALUES
('Average Response Time', 2.5, 'hours', 'performance'),
('Customer Satisfaction Score', 4.7, 'rating', 'quality'),
('Jobs Completed This Month', 127, 'count', 'operations'),
('Revenue This Quarter', 1850000, 'dollars', 'financial'),
('Lead Conversion Rate', 23.5, 'percent', 'sales')
ON CONFLICT DO NOTHING;

-- Populate forecasts (Task 68)
INSERT INTO forecasts (period_start, period_end, forecast_type, predicted_revenue, confidence_level) VALUES
('2025-10-01', '2025-10-31', 'monthly', 650000, 85),
('2025-11-01', '2025-11-30', 'monthly', 580000, 82),
('2025-12-01', '2025-12-31', 'monthly', 420000, 78),
('2025-10-01', '2025-12-31', 'quarterly', 1650000, 80),
('2025-01-01', '2025-12-31', 'annual', 7200000, 75)
ON CONFLICT DO NOTHING;

-- Populate territories (Task 69)
INSERT INTO territories (name, region, zip_codes) VALUES
('Denver Metro', 'Central', ARRAY['80201', '80202', '80203', '80204', '80205']),
('Aurora District', 'East', ARRAY['80010', '80011', '80012', '80013', '80014']),
('Westminster Zone', 'North', ARRAY['80030', '80031', '80020', '80021', '80023']),
('Littleton Area', 'South', ARRAY['80120', '80121', '80122', '80123', '80124']),
('Golden Region', 'West', ARRAY['80401', '80402', '80403', '80419', '80422'])
ON CONFLICT DO NOTHING;

-- Populate risk management (Task 104)
INSERT INTO risks (name, description, category, probability, impact, mitigation_plan, status) VALUES
('Supply Chain Disruption', 'Material shortage due to supplier issues', 'operational', 'medium', 'high', 'Maintain relationships with multiple suppliers', 'mitigated'),
('Seasonal Weather Impact', 'Severe weather affecting operations', 'environmental', 'high', 'medium', 'Flexible scheduling and weather monitoring', 'identified'),
('Labor Shortage', 'Difficulty finding qualified workers', 'resource', 'medium', 'medium', 'Training programs and competitive compensation', 'monitoring'),
('Regulatory Changes', 'New building codes affecting operations', 'compliance', 'low', 'high', 'Stay updated on regulations, legal consultation', 'identified'),
('Economic Downturn', 'Reduced demand due to economy', 'financial', 'low', 'high', 'Diversify service offerings and markets', 'monitoring')
ON CONFLICT DO NOTHING;

-- Populate strategic objectives (Task 110)
INSERT INTO strategic_objectives (name, description, category, target_date, progress, status) VALUES
('Expand Market Share', 'Increase market share to 15% in Denver metro', 'growth', '2025-12-31', 65, 'active'),
('Digital Transformation', 'Fully digitize operations and customer experience', 'technology', '2025-06-30', 78, 'active'),
('Customer Satisfaction 95%', 'Achieve 95% customer satisfaction rating', 'quality', '2025-09-30', 88, 'active'),
('Revenue Growth 25%', 'Grow annual revenue by 25% year-over-year', 'financial', '2025-12-31', 52, 'active'),
('Sustainability Initiative', 'Reduce carbon footprint by 30%', 'environmental', '2025-12-31', 41, 'active')
ON CONFLICT DO NOTHING;