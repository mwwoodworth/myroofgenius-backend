-- Polls and surveys Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS polls_surveys (
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
CREATE INDEX IF NOT EXISTS idx_polls_surveys_status ON polls_surveys(status);
CREATE INDEX IF NOT EXISTS idx_polls_surveys_created_at ON polls_surveys(created_at);
CREATE INDEX IF NOT EXISTS idx_polls_surveys_name ON polls_surveys(name);

-- Trigger for updated_at
CREATE TRIGGER set_polls_surveys_updated_at
BEFORE UPDATE ON polls_surveys
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
