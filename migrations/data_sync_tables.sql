-- Data sync Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS data_sync (
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
CREATE INDEX IF NOT EXISTS idx_data_sync_status ON data_sync(status);
CREATE INDEX IF NOT EXISTS idx_data_sync_created_at ON data_sync(created_at);
CREATE INDEX IF NOT EXISTS idx_data_sync_name ON data_sync(name);

-- Trigger for updated_at
CREATE TRIGGER set_data_sync_updated_at
BEFORE UPDATE ON data_sync
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
