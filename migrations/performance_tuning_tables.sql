-- Performance tuning Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS performance_tuning (
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
CREATE INDEX IF NOT EXISTS idx_performance_tuning_status ON performance_tuning(status);
CREATE INDEX IF NOT EXISTS idx_performance_tuning_created_at ON performance_tuning(created_at);
CREATE INDEX IF NOT EXISTS idx_performance_tuning_name ON performance_tuning(name);

-- Trigger for updated_at
CREATE TRIGGER set_performance_tuning_updated_at
BEFORE UPDATE ON performance_tuning
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
