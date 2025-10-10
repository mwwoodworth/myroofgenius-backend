-- Mobile reports Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS mobile_reports (
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
CREATE INDEX IF NOT EXISTS idx_mobile_reports_status ON mobile_reports(status);
CREATE INDEX IF NOT EXISTS idx_mobile_reports_created_at ON mobile_reports(created_at);
CREATE INDEX IF NOT EXISTS idx_mobile_reports_name ON mobile_reports(name);

-- Trigger for updated_at
CREATE TRIGGER set_mobile_reports_updated_at
BEFORE UPDATE ON mobile_reports
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
