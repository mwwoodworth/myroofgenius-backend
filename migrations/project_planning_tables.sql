-- Project planning Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS project_planning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_planning_status ON project_planning(status);
CREATE INDEX IF NOT EXISTS idx_project_planning_created_at ON project_planning(created_at);

CREATE TRIGGER set_project_planning_updated_at
BEFORE UPDATE ON project_planning
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
