-- Shift management Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS shift_management (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_shift_management_status ON shift_management(status);
CREATE INDEX IF NOT EXISTS idx_shift_management_created_at ON shift_management(created_at);

CREATE TRIGGER set_shift_management_updated_at
BEFORE UPDATE ON shift_management
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
