-- Project reporting Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS project_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_project_reports_status ON project_reports(status);
CREATE INDEX IF NOT EXISTS idx_project_reports_created_at ON project_reports(created_at);

CREATE TRIGGER set_project_reports_updated_at
BEFORE UPDATE ON project_reports
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
