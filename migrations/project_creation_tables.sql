-- Project creation Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS project_creation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_creation_status ON project_creation(status);
CREATE INDEX IF NOT EXISTS idx_project_creation_created_at ON project_creation(created_at);

CREATE TRIGGER set_project_creation_updated_at
BEFORE UPDATE ON project_creation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
