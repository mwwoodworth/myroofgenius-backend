-- Permission matrix Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS permission_matrix (
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
CREATE INDEX IF NOT EXISTS idx_permission_matrix_status ON permission_matrix(status);
CREATE INDEX IF NOT EXISTS idx_permission_matrix_created_at ON permission_matrix(created_at);
CREATE INDEX IF NOT EXISTS idx_permission_matrix_name ON permission_matrix(name);

-- Trigger for updated_at
CREATE TRIGGER set_permission_matrix_updated_at
BEFORE UPDATE ON permission_matrix
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
