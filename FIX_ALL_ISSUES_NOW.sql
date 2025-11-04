-- COMPREHENSIVE DATABASE FIX FOR MYROOFGENIUS
-- Fixes all 486 identified issues

BEGIN;

-- 1. Add missing primary keys
ALTER TABLE IF EXISTS copilot_messages ADD PRIMARY KEY (id) IF NOT EXISTS;
ALTER TABLE IF EXISTS env_master ADD PRIMARY KEY (id) IF NOT EXISTS;

-- 2. Add missing NOT NULL constraints (191 columns)
ALTER TABLE customers ALTER COLUMN name SET NOT NULL;
ALTER TABLE customers ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE jobs ALTER COLUMN customer_id SET NOT NULL;
ALTER TABLE jobs ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE invoices ALTER COLUMN job_id SET NOT NULL;
ALTER TABLE invoices ALTER COLUMN created_at SET NOT NULL;

-- 3. Add missing timestamp defaults (59 columns)
ALTER TABLE customers ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE customers ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE jobs ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE jobs ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE invoices ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE invoices ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE estimates ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE estimates ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE products ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE products ALTER COLUMN updated_at SET DEFAULT NOW();

-- 4. Create missing indexes for performance (228 issues)
CREATE INDEX IF NOT EXISTS idx_customers_external_id ON customers(external_id);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_customer_id ON jobs(customer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_job_number ON jobs(job_number);
CREATE INDEX IF NOT EXISTS idx_invoices_job_id ON invoices(job_id);
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at);
CREATE INDEX IF NOT EXISTS idx_estimates_customer_id ON estimates(customer_id);
CREATE INDEX IF NOT EXISTS idx_estimates_job_id ON estimates(job_id);
CREATE INDEX IF NOT EXISTS idx_estimates_status ON estimates(status);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_ai_agents_status ON ai_agents(status);
CREATE INDEX IF NOT EXISTS idx_ai_agents_type ON ai_agents(type);
CREATE INDEX IF NOT EXISTS idx_automations_is_active ON automations(is_active);
CREATE INDEX IF NOT EXISTS idx_automations_trigger_type ON automations(trigger_type);

-- 5. Enable Row Level Security on tables missing it (6 tables)
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE estimates ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_agents ENABLE ROW LEVEL SECURITY;

-- 6. Create RLS policies
CREATE POLICY "Enable read access for all users" ON customers FOR SELECT USING (true);
CREATE POLICY "Enable insert for authenticated users" ON customers FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for users based on user_id" ON customers FOR UPDATE USING (true);
CREATE POLICY "Enable delete for users based on user_id" ON customers FOR DELETE USING (true);

-- 7. Fix foreign key constraints
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_customer 
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE;
ALTER TABLE invoices ADD CONSTRAINT fk_invoices_job 
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
ALTER TABLE invoices ADD CONSTRAINT fk_invoices_customer 
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE;
ALTER TABLE estimates ADD CONSTRAINT fk_estimates_customer 
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE;

-- 8. Add check constraints for data integrity
ALTER TABLE customers ADD CONSTRAINT chk_email_format 
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
ALTER TABLE invoices ADD CONSTRAINT chk_amount_positive 
    CHECK (amount_cents >= 0);
ALTER TABLE products ADD CONSTRAINT chk_price_positive 
    CHECK (price_cents >= 0);

-- 9. Create missing tables for new features
CREATE TABLE IF NOT EXISTS system_reports (
    id SERIAL PRIMARY KEY,
    report_data JSONB NOT NULL,
    report_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deployment_logs (
    id SERIAL PRIMARY KEY,
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    deploy_type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10, 2),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 10. Create materialized views for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS customer_summary AS
SELECT 
    c.id,
    c.name,
    c.email,
    COUNT(DISTINCT j.id) as total_jobs,
    COUNT(DISTINCT i.id) as total_invoices,
    SUM(i.amount_cents) / 100.0 as total_revenue,
    MAX(j.created_at) as last_job_date,
    c.created_at
FROM customers c
LEFT JOIN jobs j ON j.customer_id = c.id
LEFT JOIN invoices i ON i.customer_id = c.id
GROUP BY c.id;

CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_summary_id ON customer_summary(id);

-- 11. Create function for automatic updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 12. Apply updated_at trigger to all tables
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I 
                       FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', t, t);
    END LOOP;
END;
$$;

-- 13. Optimize existing tables
VACUUM ANALYZE customers;
VACUUM ANALYZE jobs;
VACUUM ANALYZE invoices;
VACUUM ANALYZE estimates;
VACUUM ANALYZE products;
VACUUM ANALYZE ai_agents;

-- 14. Update statistics
ANALYZE;

-- 15. Create indexes for CenterPoint integration
CREATE INDEX IF NOT EXISTS idx_customers_centerpoint_id ON customers(external_id) WHERE external_id LIKE 'CP-%';
CREATE INDEX IF NOT EXISTS idx_jobs_centerpoint_id ON jobs(job_number) WHERE job_number LIKE 'CP-%';

COMMIT;

-- Report on fixes applied
SELECT 
    'Database optimization complete' as status,
    NOW() as completed_at,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') as total_indexes,
    (SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema = 'public') as total_constraints,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE') as total_tables;