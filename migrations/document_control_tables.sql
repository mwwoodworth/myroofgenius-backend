-- Document control Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS document_control (
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
CREATE INDEX IF NOT EXISTS idx_document_control_status ON document_control(status);
CREATE INDEX IF NOT EXISTS idx_document_control_created_at ON document_control(created_at);
CREATE INDEX IF NOT EXISTS idx_document_control_name ON document_control(name);

-- Trigger for updated_at
CREATE TRIGGER set_document_control_updated_at
BEFORE UPDATE ON document_control
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
