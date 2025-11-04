-- Email automation Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS email_automation (
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
CREATE INDEX IF NOT EXISTS idx_email_automation_status ON email_automation(status);
CREATE INDEX IF NOT EXISTS idx_email_automation_created_at ON email_automation(created_at);
CREATE INDEX IF NOT EXISTS idx_email_automation_name ON email_automation(name);

-- Trigger for updated_at
CREATE TRIGGER set_email_automation_updated_at
BEFORE UPDATE ON email_automation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
