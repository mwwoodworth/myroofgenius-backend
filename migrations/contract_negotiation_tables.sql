-- Contract negotiation Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS contract_negotiation (
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
CREATE INDEX IF NOT EXISTS idx_contract_negotiation_status ON contract_negotiation(status);
CREATE INDEX IF NOT EXISTS idx_contract_negotiation_created_at ON contract_negotiation(created_at);
CREATE INDEX IF NOT EXISTS idx_contract_negotiation_name ON contract_negotiation(name);

-- Trigger for updated_at
CREATE TRIGGER set_contract_negotiation_updated_at
BEFORE UPDATE ON contract_negotiation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
