-- Data export Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS data_export (
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
CREATE INDEX IF NOT EXISTS idx_data_export_status ON data_export(status);
CREATE INDEX IF NOT EXISTS idx_data_export_created_at ON data_export(created_at);
CREATE INDEX IF NOT EXISTS idx_data_export_name ON data_export(name);

-- Trigger for updated_at
CREATE TRIGGER set_data_export_updated_at
BEFORE UPDATE ON data_export
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
