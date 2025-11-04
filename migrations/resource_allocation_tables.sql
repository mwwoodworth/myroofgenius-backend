-- Resource allocation Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS resource_allocation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resource_allocation_status ON resource_allocation(status);
CREATE INDEX IF NOT EXISTS idx_resource_allocation_created_at ON resource_allocation(created_at);

CREATE TRIGGER set_resource_allocation_updated_at
BEFORE UPDATE ON resource_allocation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
