-- Approval automation Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS approval_automation (
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
CREATE INDEX IF NOT EXISTS idx_approval_automation_status ON approval_automation(status);
CREATE INDEX IF NOT EXISTS idx_approval_automation_created_at ON approval_automation(created_at);
CREATE INDEX IF NOT EXISTS idx_approval_automation_name ON approval_automation(name);

-- Trigger for updated_at
CREATE TRIGGER set_approval_automation_updated_at
BEFORE UPDATE ON approval_automation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
