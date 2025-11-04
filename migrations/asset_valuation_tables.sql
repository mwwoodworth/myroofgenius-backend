-- Asset valuation Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS asset_valuation (
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
CREATE INDEX IF NOT EXISTS idx_asset_valuation_status ON asset_valuation(status);
CREATE INDEX IF NOT EXISTS idx_asset_valuation_created_at ON asset_valuation(created_at);
CREATE INDEX IF NOT EXISTS idx_asset_valuation_name ON asset_valuation(name);

-- Trigger for updated_at
CREATE TRIGGER set_asset_valuation_updated_at
BEFORE UPDATE ON asset_valuation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
