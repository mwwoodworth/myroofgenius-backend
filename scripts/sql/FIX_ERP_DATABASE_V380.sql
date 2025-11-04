-- Fix database for ERP API v3.3.80
-- Ensures all required tables exist with correct structure

-- Create organizations table if it doesn't exist
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL DEFAULT 'WeatherCraft Roofing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default organization if none exists
INSERT INTO organizations (id, name)
VALUES ('00000000-0000-0000-0000-000000000001', 'Default Organization')
ON CONFLICT (id) DO NOTHING;

-- Ensure customers table has all required columns
ALTER TABLE customers ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Ensure estimates table has all required columns
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id);
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS estimate_number VARCHAR(50);
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id);
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS subtotal BIGINT DEFAULT 0;
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS tax_amount BIGINT DEFAULT 0;
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS total_amount BIGINT DEFAULT 0;
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft';
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS line_items JSONB DEFAULT '[]'::jsonb;
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Ensure jobs table has all required columns
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS job_number VARCHAR(50);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS estimate_id UUID REFERENCES estimates(id);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS scheduled_start TIMESTAMP WITH TIME ZONE;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Ensure invoices table has all required columns
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(50);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total_amount BIGINT DEFAULT 0;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS amount_paid BIGINT DEFAULT 0;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS due_date DATE;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_estimates_customer_id ON estimates(customer_id);
CREATE INDEX IF NOT EXISTS idx_estimates_status ON estimates(status);
CREATE INDEX IF NOT EXISTS idx_jobs_customer_id ON jobs(customer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);

-- Grant permissions (if needed)
GRANT ALL ON organizations TO postgres;
GRANT ALL ON customers TO postgres;
GRANT ALL ON estimates TO postgres;
GRANT ALL ON jobs TO postgres;
GRANT ALL ON invoices TO postgres;