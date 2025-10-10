-- Audit trails Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS audit_trails (
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
CREATE INDEX IF NOT EXISTS idx_audit_trails_status ON audit_trails(status);
CREATE INDEX IF NOT EXISTS idx_audit_trails_created_at ON audit_trails(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_trails_name ON audit_trails(name);

-- Trigger for updated_at
CREATE TRIGGER set_audit_trails_updated_at
BEFORE UPDATE ON audit_trails
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
