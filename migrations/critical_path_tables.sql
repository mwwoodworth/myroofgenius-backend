-- Critical path analysis Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS critical_path (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_critical_path_status ON critical_path(status);
CREATE INDEX IF NOT EXISTS idx_critical_path_created_at ON critical_path(created_at);

CREATE TRIGGER set_critical_path_updated_at
BEFORE UPDATE ON critical_path
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
