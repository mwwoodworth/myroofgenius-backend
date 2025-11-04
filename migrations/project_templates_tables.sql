-- Project templates Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS project_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_templates_status ON project_templates(status);
CREATE INDEX IF NOT EXISTS idx_project_templates_created_at ON project_templates(created_at);

CREATE TRIGGER set_project_templates_updated_at
BEFORE UPDATE ON project_templates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
