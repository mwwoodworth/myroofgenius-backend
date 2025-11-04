-- Contract management Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS contract_management (
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
CREATE INDEX IF NOT EXISTS idx_contract_management_status ON contract_management(status);
CREATE INDEX IF NOT EXISTS idx_contract_management_created_at ON contract_management(created_at);
CREATE INDEX IF NOT EXISTS idx_contract_management_name ON contract_management(name);

-- Trigger for updated_at
CREATE TRIGGER set_contract_management_updated_at
BEFORE UPDATE ON contract_management
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
