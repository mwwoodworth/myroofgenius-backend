-- A/B testing Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS ab_testing (
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
CREATE INDEX IF NOT EXISTS idx_ab_testing_status ON ab_testing(status);
CREATE INDEX IF NOT EXISTS idx_ab_testing_created_at ON ab_testing(created_at);
CREATE INDEX IF NOT EXISTS idx_ab_testing_name ON ab_testing(name);

-- Trigger for updated_at
CREATE TRIGGER set_ab_testing_updated_at
BEFORE UPDATE ON ab_testing
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
