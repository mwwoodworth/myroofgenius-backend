-- Field service Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS field_service (
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
CREATE INDEX IF NOT EXISTS idx_field_service_status ON field_service(status);
CREATE INDEX IF NOT EXISTS idx_field_service_created_at ON field_service(created_at);
CREATE INDEX IF NOT EXISTS idx_field_service_name ON field_service(name);

-- Trigger for updated_at
CREATE TRIGGER set_field_service_updated_at
BEFORE UPDATE ON field_service
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
