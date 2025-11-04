-- Maintenance scheduling Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS maintenance_scheduling (
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
CREATE INDEX IF NOT EXISTS idx_maintenance_scheduling_status ON maintenance_scheduling(status);
CREATE INDEX IF NOT EXISTS idx_maintenance_scheduling_created_at ON maintenance_scheduling(created_at);
CREATE INDEX IF NOT EXISTS idx_maintenance_scheduling_name ON maintenance_scheduling(name);

-- Trigger for updated_at
CREATE TRIGGER set_maintenance_scheduling_updated_at
BEFORE UPDATE ON maintenance_scheduling
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
