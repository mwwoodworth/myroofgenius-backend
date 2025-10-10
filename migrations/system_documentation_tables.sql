-- System documentation Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS system_documentation (
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
CREATE INDEX IF NOT EXISTS idx_system_documentation_status ON system_documentation(status);
CREATE INDEX IF NOT EXISTS idx_system_documentation_created_at ON system_documentation(created_at);
CREATE INDEX IF NOT EXISTS idx_system_documentation_name ON system_documentation(name);

-- Trigger for updated_at
CREATE TRIGGER set_system_documentation_updated_at
BEFORE UPDATE ON system_documentation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
