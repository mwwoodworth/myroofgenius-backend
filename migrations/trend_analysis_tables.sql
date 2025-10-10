-- Trend analysis Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS trend_analysis (
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
CREATE INDEX IF NOT EXISTS idx_trend_analysis_status ON trend_analysis(status);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_created_at ON trend_analysis(created_at);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_name ON trend_analysis(name);

-- Trigger for updated_at
CREATE TRIGGER set_trend_analysis_updated_at
BEFORE UPDATE ON trend_analysis
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
