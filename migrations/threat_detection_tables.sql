-- Threat detection Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS threat_detection (
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
CREATE INDEX IF NOT EXISTS idx_threat_detection_status ON threat_detection(status);
CREATE INDEX IF NOT EXISTS idx_threat_detection_created_at ON threat_detection(created_at);
CREATE INDEX IF NOT EXISTS idx_threat_detection_name ON threat_detection(name);

-- Trigger for updated_at
CREATE TRIGGER set_threat_detection_updated_at
BEFORE UPDATE ON threat_detection
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
