-- Two-factor authentication Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS two_factor_auth (
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
CREATE INDEX IF NOT EXISTS idx_two_factor_auth_status ON two_factor_auth(status);
CREATE INDEX IF NOT EXISTS idx_two_factor_auth_created_at ON two_factor_auth(created_at);
CREATE INDEX IF NOT EXISTS idx_two_factor_auth_name ON two_factor_auth(name);

-- Trigger for updated_at
CREATE TRIGGER set_two_factor_auth_updated_at
BEFORE UPDATE ON two_factor_auth
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
