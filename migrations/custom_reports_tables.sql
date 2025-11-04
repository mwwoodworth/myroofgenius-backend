-- Custom reports Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS custom_reports (
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
CREATE INDEX IF NOT EXISTS idx_custom_reports_status ON custom_reports(status);
CREATE INDEX IF NOT EXISTS idx_custom_reports_created_at ON custom_reports(created_at);
CREATE INDEX IF NOT EXISTS idx_custom_reports_name ON custom_reports(name);

-- Trigger for updated_at
CREATE TRIGGER set_custom_reports_updated_at
BEFORE UPDATE ON custom_reports
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
