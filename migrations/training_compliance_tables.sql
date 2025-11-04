-- Training compliance Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS training_compliance (
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
CREATE INDEX IF NOT EXISTS idx_training_compliance_status ON training_compliance(status);
CREATE INDEX IF NOT EXISTS idx_training_compliance_created_at ON training_compliance(created_at);
CREATE INDEX IF NOT EXISTS idx_training_compliance_name ON training_compliance(name);

-- Trigger for updated_at
CREATE TRIGGER set_training_compliance_updated_at
BEFORE UPDATE ON training_compliance
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
