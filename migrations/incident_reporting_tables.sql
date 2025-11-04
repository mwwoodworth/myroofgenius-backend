-- Incident reporting Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS incident_reporting (
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
CREATE INDEX IF NOT EXISTS idx_incident_reporting_status ON incident_reporting(status);
CREATE INDEX IF NOT EXISTS idx_incident_reporting_created_at ON incident_reporting(created_at);
CREATE INDEX IF NOT EXISTS idx_incident_reporting_name ON incident_reporting(name);

-- Trigger for updated_at
CREATE TRIGGER set_incident_reporting_updated_at
BEFORE UPDATE ON incident_reporting
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
