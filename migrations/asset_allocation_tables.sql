-- Asset allocation Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS asset_allocation (
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
CREATE INDEX IF NOT EXISTS idx_asset_allocation_status ON asset_allocation(status);
CREATE INDEX IF NOT EXISTS idx_asset_allocation_created_at ON asset_allocation(created_at);
CREATE INDEX IF NOT EXISTS idx_asset_allocation_name ON asset_allocation(name);

-- Trigger for updated_at
CREATE TRIGGER set_asset_allocation_updated_at
BEFORE UPDATE ON asset_allocation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
