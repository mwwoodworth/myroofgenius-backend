-- Mobile API Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS mobile_api (
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
CREATE INDEX IF NOT EXISTS idx_mobile_api_status ON mobile_api(status);
CREATE INDEX IF NOT EXISTS idx_mobile_api_created_at ON mobile_api(created_at);
CREATE INDEX IF NOT EXISTS idx_mobile_api_name ON mobile_api(name);

-- Trigger for updated_at
CREATE TRIGGER set_mobile_api_updated_at
BEFORE UPDATE ON mobile_api
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
