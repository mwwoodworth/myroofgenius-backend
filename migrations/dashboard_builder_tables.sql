-- Dashboard builder Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS dashboard_builder (
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
CREATE INDEX IF NOT EXISTS idx_dashboard_builder_status ON dashboard_builder(status);
CREATE INDEX IF NOT EXISTS idx_dashboard_builder_created_at ON dashboard_builder(created_at);
CREATE INDEX IF NOT EXISTS idx_dashboard_builder_name ON dashboard_builder(name);

-- Trigger for updated_at
CREATE TRIGGER set_dashboard_builder_updated_at
BEFORE UPDATE ON dashboard_builder
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
