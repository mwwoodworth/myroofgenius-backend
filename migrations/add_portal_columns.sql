-- Add customer portal columns to customers table
-- These columns enable self-service portal access for customers

-- Add portal-specific columns
ALTER TABLE customers
    ADD COLUMN IF NOT EXISTS portal_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS portal_password_hash VARCHAR(255),
    ADD COLUMN IF NOT EXISTS portal_reset_token VARCHAR(255),
    ADD COLUMN IF NOT EXISTS portal_reset_expires TIMESTAMP,
    ADD COLUMN IF NOT EXISTS portal_last_login TIMESTAMP,
    ADD COLUMN IF NOT EXISTS portal_preferences JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS portal_2fa_enabled BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS portal_2fa_secret VARCHAR(255);

-- Create indexes for portal functionality
CREATE INDEX IF NOT EXISTS idx_customers_portal_enabled ON customers(portal_enabled) WHERE portal_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_customers_portal_reset_token ON customers(portal_reset_token) WHERE portal_reset_token IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_email_active ON customers(email, status) WHERE status = 'active';

-- Create support tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(50) DEFAULT 'normal',
    status VARCHAR(50) DEFAULT 'open',
    assigned_to UUID,
    resolution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for support tickets
CREATE INDEX idx_support_tickets_customer_id ON support_tickets(customer_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_support_tickets_priority ON support_tickets(priority);
CREATE INDEX idx_support_tickets_created_at ON support_tickets(created_at DESC);

-- Create documents table for customer documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID,
    job_id UUID,
    invoice_id UUID,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    size BIGINT,
    mime_type VARCHAR(100),
    storage_path TEXT,
    download_url TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for documents
CREATE INDEX idx_documents_customer_id ON documents(customer_id);
CREATE INDEX idx_documents_job_id ON documents(job_id);
CREATE INDEX idx_documents_invoice_id ON documents(invoice_id);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_documents_is_public ON documents(is_public);

-- Create portal activity log
CREATE TABLE IF NOT EXISTS portal_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Create indexes for activity log
CREATE INDEX idx_portal_activity_customer_id ON portal_activity_log(customer_id);
CREATE INDEX idx_portal_activity_created_at ON portal_activity_log(created_at DESC);
CREATE INDEX idx_portal_activity_action ON portal_activity_log(action);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON support_tickets TO authenticated;
GRANT SELECT ON documents TO authenticated;
GRANT SELECT, INSERT ON portal_activity_log TO authenticated;

-- Add RLS policies for portal tables
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE portal_activity_log ENABLE ROW LEVEL SECURITY;

-- Customers can only see their own tickets
CREATE POLICY support_tickets_customer_policy ON support_tickets
    FOR SELECT
    USING (customer_id = current_setting('app.current_customer_id')::UUID);

-- Customers can only see their public documents
CREATE POLICY documents_customer_policy ON documents
    FOR SELECT
    USING (customer_id = current_setting('app.current_customer_id')::UUID AND is_public = TRUE);

-- Customers can only see their own activity
CREATE POLICY portal_activity_customer_policy ON portal_activity_log
    FOR SELECT
    USING (customer_id = current_setting('app.current_customer_id')::UUID);
