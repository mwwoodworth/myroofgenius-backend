-- Predictive analytics Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS predictive_analytics (
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
CREATE INDEX IF NOT EXISTS idx_predictive_analytics_status ON predictive_analytics(status);
CREATE INDEX IF NOT EXISTS idx_predictive_analytics_created_at ON predictive_analytics(created_at);
CREATE INDEX IF NOT EXISTS idx_predictive_analytics_name ON predictive_analytics(name);

-- Trigger for updated_at
CREATE TRIGGER set_predictive_analytics_updated_at
BEFORE UPDATE ON predictive_analytics
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
