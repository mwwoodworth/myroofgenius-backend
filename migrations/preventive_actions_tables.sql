-- Preventive actions Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS preventive_actions (
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
CREATE INDEX IF NOT EXISTS idx_preventive_actions_status ON preventive_actions(status);
CREATE INDEX IF NOT EXISTS idx_preventive_actions_created_at ON preventive_actions(created_at);
CREATE INDEX IF NOT EXISTS idx_preventive_actions_name ON preventive_actions(name);

-- Trigger for updated_at
CREATE TRIGGER set_preventive_actions_updated_at
BEFORE UPDATE ON preventive_actions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
