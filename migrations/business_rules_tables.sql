-- Business rules Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS business_rules (
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
CREATE INDEX IF NOT EXISTS idx_business_rules_status ON business_rules(status);
CREATE INDEX IF NOT EXISTS idx_business_rules_created_at ON business_rules(created_at);
CREATE INDEX IF NOT EXISTS idx_business_rules_name ON business_rules(name);

-- Trigger for updated_at
CREATE TRIGGER set_business_rules_updated_at
BEFORE UPDATE ON business_rules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
