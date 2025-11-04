-- Single sign-on Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS single_sign_on (
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
CREATE INDEX IF NOT EXISTS idx_single_sign_on_status ON single_sign_on(status);
CREATE INDEX IF NOT EXISTS idx_single_sign_on_created_at ON single_sign_on(created_at);
CREATE INDEX IF NOT EXISTS idx_single_sign_on_name ON single_sign_on(name);

-- Trigger for updated_at
CREATE TRIGGER set_single_sign_on_updated_at
BEFORE UPDATE ON single_sign_on
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
