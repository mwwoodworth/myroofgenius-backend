-- Alert automation Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS alert_automation (
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
CREATE INDEX IF NOT EXISTS idx_alert_automation_status ON alert_automation(status);
CREATE INDEX IF NOT EXISTS idx_alert_automation_created_at ON alert_automation(created_at);
CREATE INDEX IF NOT EXISTS idx_alert_automation_name ON alert_automation(name);

-- Trigger for updated_at
CREATE TRIGGER set_alert_automation_updated_at
BEFORE UPDATE ON alert_automation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
