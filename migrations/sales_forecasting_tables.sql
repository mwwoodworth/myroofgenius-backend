-- Sales forecasting Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS sales_forecasting (
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
CREATE INDEX IF NOT EXISTS idx_sales_forecasting_status ON sales_forecasting(status);
CREATE INDEX IF NOT EXISTS idx_sales_forecasting_created_at ON sales_forecasting(created_at);
CREATE INDEX IF NOT EXISTS idx_sales_forecasting_name ON sales_forecasting(name);

-- Trigger for updated_at
CREATE TRIGGER set_sales_forecasting_updated_at
BEFORE UPDATE ON sales_forecasting
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
