-- Commission tracking Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS commission_tracking (
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
CREATE INDEX IF NOT EXISTS idx_commission_tracking_status ON commission_tracking(status);
CREATE INDEX IF NOT EXISTS idx_commission_tracking_created_at ON commission_tracking(created_at);
CREATE INDEX IF NOT EXISTS idx_commission_tracking_name ON commission_tracking(name);

-- Trigger for updated_at
CREATE TRIGGER set_commission_tracking_updated_at
BEFORE UPDATE ON commission_tracking
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
