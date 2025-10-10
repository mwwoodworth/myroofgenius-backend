-- Security logging Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS security_logging (
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
CREATE INDEX IF NOT EXISTS idx_security_logging_status ON security_logging(status);
CREATE INDEX IF NOT EXISTS idx_security_logging_created_at ON security_logging(created_at);
CREATE INDEX IF NOT EXISTS idx_security_logging_name ON security_logging(name);

-- Trigger for updated_at
CREATE TRIGGER set_security_logging_updated_at
BEFORE UPDATE ON security_logging
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
