-- Extended leave management Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS leave_management_extended (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leave_management_extended_status ON leave_management_extended(status);
CREATE INDEX IF NOT EXISTS idx_leave_management_extended_created_at ON leave_management_extended(created_at);

CREATE TRIGGER set_leave_management_extended_updated_at
BEFORE UPDATE ON leave_management_extended
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
