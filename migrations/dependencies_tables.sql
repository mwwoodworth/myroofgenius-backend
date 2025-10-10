-- Task dependencies Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dependencies_status ON dependencies(status);
CREATE INDEX IF NOT EXISTS idx_dependencies_created_at ON dependencies(created_at);

CREATE TRIGGER set_dependencies_updated_at
BEFORE UPDATE ON dependencies
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
