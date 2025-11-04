-- Bid comparison Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS bid_comparison (
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
CREATE INDEX IF NOT EXISTS idx_bid_comparison_status ON bid_comparison(status);
CREATE INDEX IF NOT EXISTS idx_bid_comparison_created_at ON bid_comparison(created_at);
CREATE INDEX IF NOT EXISTS idx_bid_comparison_name ON bid_comparison(name);

-- Trigger for updated_at
CREATE TRIGGER set_bid_comparison_updated_at
BEFORE UPDATE ON bid_comparison
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
