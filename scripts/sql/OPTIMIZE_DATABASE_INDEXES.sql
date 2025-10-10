-- ============================================================
-- DATABASE OPTIMIZATION - Production Indexes and Performance
-- ============================================================

-- Performance indexes for customers table
CREATE INDEX IF NOT EXISTS idx_customers_external_id ON customers(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_customers_name_search ON customers USING gin(to_tsvector('english', name));

-- Performance indexes for jobs table
CREATE INDEX IF NOT EXISTS idx_jobs_customer_id ON jobs(customer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status) WHERE status != 'completed';
CREATE INDEX IF NOT EXISTS idx_jobs_job_number ON jobs(job_number) WHERE job_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_dates ON jobs(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- Performance indexes for invoices table
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_job_id ON invoices(job_id) WHERE job_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status) WHERE status != 'paid';
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date) WHERE status != 'paid';

-- Performance indexes for estimates table
CREATE INDEX IF NOT EXISTS idx_estimates_customer_id ON estimates(customer_id);
CREATE INDEX IF NOT EXISTS idx_estimates_job_id ON estimates(job_id) WHERE job_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_estimates_status ON estimates(status) WHERE status = 'pending';

-- Performance indexes for products table
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku) WHERE sku IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category) WHERE category IS NOT NULL;

-- Performance indexes for centerpoint sync tables
CREATE INDEX IF NOT EXISTS idx_cp_sync_log_started ON centerpoint_sync_log(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_cp_files_entity ON centerpoint_files(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_cp_files_downloaded ON centerpoint_files(is_downloaded) WHERE is_downloaded = false;

-- Performance indexes for centerpoint data tables
CREATE INDEX IF NOT EXISTS idx_cp_invoices_status ON centerpoint_invoices(status) WHERE status != 'paid';
CREATE INDEX IF NOT EXISTS idx_cp_employees_active ON centerpoint_employees(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_cp_tickets_status ON centerpoint_tickets(status) WHERE status = 'open';

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_jobs_customer_status ON jobs(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_invoices_customer_status ON invoices(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_files_entity_composite ON centerpoint_files(entity_type, entity_id, is_downloaded);

-- Tag sample data appropriately
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_sample BOOLEAN DEFAULT false;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_sample BOOLEAN DEFAULT false;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS is_sample BOOLEAN DEFAULT false;
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS is_sample BOOLEAN DEFAULT false;
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_sample BOOLEAN DEFAULT false;

-- Update metadata columns to track sample data
ALTER TABLE customers ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE products ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Mark any potential sample data (can be adjusted based on criteria)
UPDATE customers SET is_sample = true, metadata = jsonb_set(metadata, '{is_sample}', 'true')
WHERE email LIKE '%test%' OR email LIKE '%demo%' OR email LIKE '%example%';

UPDATE jobs SET is_sample = true, metadata = jsonb_set(metadata, '{is_sample}', 'true')
WHERE description LIKE '%test%' OR description LIKE '%demo%' OR customer_id IS NULL;

UPDATE products SET is_sample = true, metadata = jsonb_set(metadata, '{is_sample}', 'true')
WHERE name LIKE '%Test%' OR name LIKE '%Demo%' OR sku LIKE 'TEST%';

-- Performance statistics views
CREATE OR REPLACE VIEW v_database_stats AS
SELECT 
    'customers' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_sample = true) as sample_records,
    COUNT(*) FILTER (WHERE external_id LIKE 'CP-%') as centerpoint_records,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as recent_records
FROM customers
UNION ALL
SELECT 
    'jobs',
    COUNT(*),
    COUNT(*) FILTER (WHERE is_sample = true),
    COUNT(*) FILTER (WHERE job_number LIKE 'CP-%'),
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours')
FROM jobs
UNION ALL
SELECT 
    'invoices',
    COUNT(*),
    COUNT(*) FILTER (WHERE is_sample = true),
    0,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours')
FROM invoices
UNION ALL
SELECT 
    'products',
    COUNT(*),
    COUNT(*) FILTER (WHERE is_sample = true),
    0,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours')
FROM products;

-- Table statistics for optimization
ANALYZE customers;
ANALYZE jobs;
ANALYZE invoices;
ANALYZE estimates;
ANALYZE products;
ANALYZE centerpoint_files;
ANALYZE centerpoint_invoices;
ANALYZE centerpoint_employees;
ANALYZE centerpoint_tickets;
ANALYZE centerpoint_photos;
ANALYZE centerpoint_estimates;
ANALYZE centerpoint_sync_log;

-- Report optimization results
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC
LIMIT 20;

-- Show table sizes
SELECT 
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    pg_size_pretty(pg_relation_size(relid)) as table_size,
    pg_size_pretty(pg_indexes_size(relid)) as indexes_size
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;

-- Success message
SELECT '✅ Database optimization complete!' as status,
       COUNT(DISTINCT indexname) as total_indexes,
       COUNT(DISTINCT tablename) as optimized_tables
FROM pg_indexes
WHERE schemaname = 'public';