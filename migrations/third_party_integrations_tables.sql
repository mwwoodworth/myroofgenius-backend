-- Third-party integrations Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS third_party_integrations (
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
CREATE INDEX IF NOT EXISTS idx_third_party_integrations_status ON third_party_integrations(status);
CREATE INDEX IF NOT EXISTS idx_third_party_integrations_created_at ON third_party_integrations(created_at);
CREATE INDEX IF NOT EXISTS idx_third_party_integrations_name ON third_party_integrations(name);

-- Trigger for updated_at
CREATE TRIGGER set_third_party_integrations_updated_at
BEFORE UPDATE ON third_party_integrations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
