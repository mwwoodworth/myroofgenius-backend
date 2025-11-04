-- Service bus Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS service_bus (
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
CREATE INDEX IF NOT EXISTS idx_service_bus_status ON service_bus(status);
CREATE INDEX IF NOT EXISTS idx_service_bus_created_at ON service_bus(created_at);
CREATE INDEX IF NOT EXISTS idx_service_bus_name ON service_bus(name);

-- Trigger for updated_at
CREATE TRIGGER set_service_bus_updated_at
BEFORE UPDATE ON service_bus
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
