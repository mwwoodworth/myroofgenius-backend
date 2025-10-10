-- ETL pipelines Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS etl_pipelines (
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
CREATE INDEX IF NOT EXISTS idx_etl_pipelines_status ON etl_pipelines(status);
CREATE INDEX IF NOT EXISTS idx_etl_pipelines_created_at ON etl_pipelines(created_at);
CREATE INDEX IF NOT EXISTS idx_etl_pipelines_name ON etl_pipelines(name);

-- Trigger for updated_at
CREATE TRIGGER set_etl_pipelines_updated_at
BEFORE UPDATE ON etl_pipelines
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
