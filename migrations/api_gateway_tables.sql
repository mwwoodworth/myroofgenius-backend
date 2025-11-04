-- API gateway Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS api_gateway (
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
CREATE INDEX IF NOT EXISTS idx_api_gateway_status ON api_gateway(status);
CREATE INDEX IF NOT EXISTS idx_api_gateway_created_at ON api_gateway(created_at);
CREATE INDEX IF NOT EXISTS idx_api_gateway_name ON api_gateway(name);

-- Trigger for updated_at
CREATE TRIGGER set_api_gateway_updated_at
BEFORE UPDATE ON api_gateway
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
