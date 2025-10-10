-- Mobile forms Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS mobile_forms (
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
CREATE INDEX IF NOT EXISTS idx_mobile_forms_status ON mobile_forms(status);
CREATE INDEX IF NOT EXISTS idx_mobile_forms_created_at ON mobile_forms(created_at);
CREATE INDEX IF NOT EXISTS idx_mobile_forms_name ON mobile_forms(name);

-- Trigger for updated_at
CREATE TRIGGER set_mobile_forms_updated_at
BEFORE UPDATE ON mobile_forms
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
