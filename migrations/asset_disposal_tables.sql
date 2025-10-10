-- Asset disposal Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS asset_disposal (
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
CREATE INDEX IF NOT EXISTS idx_asset_disposal_status ON asset_disposal(status);
CREATE INDEX IF NOT EXISTS idx_asset_disposal_created_at ON asset_disposal(created_at);
CREATE INDEX IF NOT EXISTS idx_asset_disposal_name ON asset_disposal(name);

-- Trigger for updated_at
CREATE TRIGGER set_asset_disposal_updated_at
BEFORE UPDATE ON asset_disposal
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
