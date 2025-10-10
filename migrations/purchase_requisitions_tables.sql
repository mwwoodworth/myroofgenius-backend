-- Purchase requisitions Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS purchase_requisitions (
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
CREATE INDEX IF NOT EXISTS idx_purchase_requisitions_status ON purchase_requisitions(status);
CREATE INDEX IF NOT EXISTS idx_purchase_requisitions_created_at ON purchase_requisitions(created_at);
CREATE INDEX IF NOT EXISTS idx_purchase_requisitions_name ON purchase_requisitions(name);

-- Trigger for updated_at
CREATE TRIGGER set_purchase_requisitions_updated_at
BEFORE UPDATE ON purchase_requisitions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
