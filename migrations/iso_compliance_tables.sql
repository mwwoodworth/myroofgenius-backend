-- ISO compliance Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS iso_compliance (
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
CREATE INDEX IF NOT EXISTS idx_iso_compliance_status ON iso_compliance(status);
CREATE INDEX IF NOT EXISTS idx_iso_compliance_created_at ON iso_compliance(created_at);
CREATE INDEX IF NOT EXISTS idx_iso_compliance_name ON iso_compliance(name);

-- Trigger for updated_at
CREATE TRIGGER set_iso_compliance_updated_at
BEFORE UPDATE ON iso_compliance
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
