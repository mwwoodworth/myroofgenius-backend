-- Risk assessment Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS risk_assessment (
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
CREATE INDEX IF NOT EXISTS idx_risk_assessment_status ON risk_assessment(status);
CREATE INDEX IF NOT EXISTS idx_risk_assessment_created_at ON risk_assessment(created_at);
CREATE INDEX IF NOT EXISTS idx_risk_assessment_name ON risk_assessment(name);

-- Trigger for updated_at
CREATE TRIGGER set_risk_assessment_updated_at
BEFORE UPDATE ON risk_assessment
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
