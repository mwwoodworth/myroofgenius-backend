-- Lead scoring Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS lead_scoring (
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
CREATE INDEX IF NOT EXISTS idx_lead_scoring_status ON lead_scoring(status);
CREATE INDEX IF NOT EXISTS idx_lead_scoring_created_at ON lead_scoring(created_at);
CREATE INDEX IF NOT EXISTS idx_lead_scoring_name ON lead_scoring(name);

-- Trigger for updated_at
CREATE TRIGGER set_lead_scoring_updated_at
BEFORE UPDATE ON lead_scoring
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
