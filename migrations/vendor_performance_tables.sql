-- Vendor performance Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS vendor_performance (
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
CREATE INDEX IF NOT EXISTS idx_vendor_performance_status ON vendor_performance(status);
CREATE INDEX IF NOT EXISTS idx_vendor_performance_created_at ON vendor_performance(created_at);
CREATE INDEX IF NOT EXISTS idx_vendor_performance_name ON vendor_performance(name);

-- Trigger for updated_at
CREATE TRIGGER set_vendor_performance_updated_at
BEFORE UPDATE ON vendor_performance
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
