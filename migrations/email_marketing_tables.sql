-- Email marketing Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS email_marketing (
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
CREATE INDEX IF NOT EXISTS idx_email_marketing_status ON email_marketing(status);
CREATE INDEX IF NOT EXISTS idx_email_marketing_created_at ON email_marketing(created_at);
CREATE INDEX IF NOT EXISTS idx_email_marketing_name ON email_marketing(name);

-- Trigger for updated_at
CREATE TRIGGER set_email_marketing_updated_at
BEFORE UPDATE ON email_marketing
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
