-- System settings Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS system_settings (
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
CREATE INDEX IF NOT EXISTS idx_system_settings_status ON system_settings(status);
CREATE INDEX IF NOT EXISTS idx_system_settings_created_at ON system_settings(created_at);
CREATE INDEX IF NOT EXISTS idx_system_settings_name ON system_settings(name);

-- Trigger for updated_at
CREATE TRIGGER set_system_settings_updated_at
BEFORE UPDATE ON system_settings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
