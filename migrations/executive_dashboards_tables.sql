-- Executive dashboards Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS executive_dashboards (
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
CREATE INDEX IF NOT EXISTS idx_executive_dashboards_status ON executive_dashboards(status);
CREATE INDEX IF NOT EXISTS idx_executive_dashboards_created_at ON executive_dashboards(created_at);
CREATE INDEX IF NOT EXISTS idx_executive_dashboards_name ON executive_dashboards(name);

-- Trigger for updated_at
CREATE TRIGGER set_executive_dashboards_updated_at
BEFORE UPDATE ON executive_dashboards
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
