-- Project dashboards Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS project_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_dashboards_status ON project_dashboards(status);
CREATE INDEX IF NOT EXISTS idx_project_dashboards_created_at ON project_dashboards(created_at);

CREATE TRIGGER set_project_dashboards_updated_at
BEFORE UPDATE ON project_dashboards
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
