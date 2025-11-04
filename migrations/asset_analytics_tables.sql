-- Asset analytics Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS asset_analytics (
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
CREATE INDEX IF NOT EXISTS idx_asset_analytics_status ON asset_analytics(status);
CREATE INDEX IF NOT EXISTS idx_asset_analytics_created_at ON asset_analytics(created_at);
CREATE INDEX IF NOT EXISTS idx_asset_analytics_name ON asset_analytics(name);

-- Trigger for updated_at
CREATE TRIGGER set_asset_analytics_updated_at
BEFORE UPDATE ON asset_analytics
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
