-- Integration monitoring Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS integration_monitoring (
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
CREATE INDEX IF NOT EXISTS idx_integration_monitoring_status ON integration_monitoring(status);
CREATE INDEX IF NOT EXISTS idx_integration_monitoring_created_at ON integration_monitoring(created_at);
CREATE INDEX IF NOT EXISTS idx_integration_monitoring_name ON integration_monitoring(name);

-- Trigger for updated_at
CREATE TRIGGER set_integration_monitoring_updated_at
BEFORE UPDATE ON integration_monitoring
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
