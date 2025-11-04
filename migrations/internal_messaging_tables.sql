-- Internal messaging Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS internal_messaging (
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
CREATE INDEX IF NOT EXISTS idx_internal_messaging_status ON internal_messaging(status);
CREATE INDEX IF NOT EXISTS idx_internal_messaging_created_at ON internal_messaging(created_at);
CREATE INDEX IF NOT EXISTS idx_internal_messaging_name ON internal_messaging(name);

-- Trigger for updated_at
CREATE TRIGGER set_internal_messaging_updated_at
BEFORE UPDATE ON internal_messaging
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
