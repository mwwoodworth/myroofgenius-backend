-- Remote support Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS remote_support (
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
CREATE INDEX IF NOT EXISTS idx_remote_support_status ON remote_support(status);
CREATE INDEX IF NOT EXISTS idx_remote_support_created_at ON remote_support(created_at);
CREATE INDEX IF NOT EXISTS idx_remote_support_name ON remote_support(name);

-- Trigger for updated_at
CREATE TRIGGER set_remote_support_updated_at
BEFORE UPDATE ON remote_support
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
