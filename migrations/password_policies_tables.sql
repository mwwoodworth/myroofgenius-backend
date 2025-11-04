-- Password policies Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS password_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    data JSONB,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_password_policies_status ON password_policies(status);
CREATE INDEX IF NOT EXISTS idx_password_policies_created_at ON password_policies(created_at);
CREATE INDEX IF NOT EXISTS idx_password_policies_name ON password_policies(name);

-- Trigger for updated_at
CREATE TRIGGER set_password_policies_updated_at
BEFORE UPDATE ON password_policies
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
