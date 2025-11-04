-- Non-conformance Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS non_conformance (
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
CREATE INDEX IF NOT EXISTS idx_non_conformance_status ON non_conformance(status);
CREATE INDEX IF NOT EXISTS idx_non_conformance_created_at ON non_conformance(created_at);
CREATE INDEX IF NOT EXISTS idx_non_conformance_name ON non_conformance(name);

-- Trigger for updated_at
CREATE TRIGGER set_non_conformance_updated_at
BEFORE UPDATE ON non_conformance
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
