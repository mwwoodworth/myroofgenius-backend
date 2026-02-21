-- Fixed Database Optimization Script
-- Correct PostgreSQL syntax for adding columns if they don't exist

-- Function to safely add columns
CREATE OR REPLACE FUNCTION add_column_if_not_exists(
    table_name text,
    column_name text,
    column_type text,
    default_value text DEFAULT NULL
) RETURNS void AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = $1 
        AND column_name = $2
    ) THEN
        IF default_value IS NOT NULL THEN
            EXECUTE format('ALTER TABLE %I ADD COLUMN %I %s DEFAULT %s', 
                          table_name, column_name, column_type, default_value);
        ELSE
            EXECUTE format('ALTER TABLE %I ADD COLUMN %I %s', 
                          table_name, column_name, column_type);
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_external_id ON customers(external_id);
CREATE INDEX IF NOT EXISTS idx_jobs_customer_id ON jobs(customer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_job_id ON invoices(job_id);
CREATE INDEX IF NOT EXISTS idx_estimates_customer_id ON estimates(customer_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_ai_agents_status ON ai_agents(status);

-- Add missing columns to tables
SELECT add_column_if_not_exists('customers', 'external_id', 'VARCHAR(255)');
SELECT add_column_if_not_exists('customers', 'created_at', 'TIMESTAMP', 'NOW()');
SELECT add_column_if_not_exists('customers', 'updated_at', 'TIMESTAMP', 'NOW()');

SELECT add_column_if_not_exists('jobs', 'job_number', 'VARCHAR(255)');
SELECT add_column_if_not_exists('jobs', 'created_at', 'TIMESTAMP', 'NOW()');
SELECT add_column_if_not_exists('jobs', 'updated_at', 'TIMESTAMP', 'NOW()');

SELECT add_column_if_not_exists('invoices', 'created_at', 'TIMESTAMP', 'NOW()');
SELECT add_column_if_not_exists('invoices', 'updated_at', 'TIMESTAMP', 'NOW()');

SELECT add_column_if_not_exists('estimates', 'created_at', 'TIMESTAMP', 'NOW()');
SELECT add_column_if_not_exists('estimates', 'updated_at', 'TIMESTAMP', 'NOW()');

SELECT add_column_if_not_exists('products', 'created_at', 'TIMESTAMP', 'NOW()');
SELECT add_column_if_not_exists('products', 'updated_at', 'TIMESTAMP', 'NOW()');

SELECT add_column_if_not_exists('ai_agents', 'created_at', 'TIMESTAMP', 'NOW()');
SELECT add_column_if_not_exists('ai_agents', 'updated_at', 'TIMESTAMP', 'NOW()');

-- Optimize tables
VACUUM ANALYZE customers;
VACUUM ANALYZE jobs;
VACUUM ANALYZE invoices;
VACUUM ANALYZE estimates;
VACUUM ANALYZE products;
VACUUM ANALYZE ai_agents;

-- Update statistics
ANALYZE;

-- Clean up function
DROP FUNCTION IF EXISTS add_column_if_not_exists(text, text, text, text);

-- Report success
SELECT 'Database optimization complete!' AS status;