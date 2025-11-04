-- Real-time monitoring Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS real_time_monitoring (
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
CREATE INDEX IF NOT EXISTS idx_real_time_monitoring_status ON real_time_monitoring(status);
CREATE INDEX IF NOT EXISTS idx_real_time_monitoring_created_at ON real_time_monitoring(created_at);
CREATE INDEX IF NOT EXISTS idx_real_time_monitoring_name ON real_time_monitoring(name);

-- Trigger for updated_at
CREATE TRIGGER set_real_time_monitoring_updated_at
BEFORE UPDATE ON real_time_monitoring
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
