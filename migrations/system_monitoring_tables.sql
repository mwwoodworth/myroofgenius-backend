-- System monitoring Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS system_monitoring (
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
CREATE INDEX IF NOT EXISTS idx_system_monitoring_status ON system_monitoring(status);
CREATE INDEX IF NOT EXISTS idx_system_monitoring_created_at ON system_monitoring(created_at);
CREATE INDEX IF NOT EXISTS idx_system_monitoring_name ON system_monitoring(name);

-- Trigger for updated_at
CREATE TRIGGER set_system_monitoring_updated_at
BEFORE UPDATE ON system_monitoring
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
