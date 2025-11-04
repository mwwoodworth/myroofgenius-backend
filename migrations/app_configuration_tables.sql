-- App configuration Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS app_configuration (
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
CREATE INDEX IF NOT EXISTS idx_app_configuration_status ON app_configuration(status);
CREATE INDEX IF NOT EXISTS idx_app_configuration_created_at ON app_configuration(created_at);
CREATE INDEX IF NOT EXISTS idx_app_configuration_name ON app_configuration(name);

-- Trigger for updated_at
CREATE TRIGGER set_app_configuration_updated_at
BEFORE UPDATE ON app_configuration
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
