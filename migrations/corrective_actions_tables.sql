-- Corrective actions Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS corrective_actions (
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
CREATE INDEX IF NOT EXISTS idx_corrective_actions_status ON corrective_actions(status);
CREATE INDEX IF NOT EXISTS idx_corrective_actions_created_at ON corrective_actions(created_at);
CREATE INDEX IF NOT EXISTS idx_corrective_actions_name ON corrective_actions(name);

-- Trigger for updated_at
CREATE TRIGGER set_corrective_actions_updated_at
BEFORE UPDATE ON corrective_actions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
