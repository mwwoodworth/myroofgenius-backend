-- Document sharing Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS document_sharing (
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
CREATE INDEX IF NOT EXISTS idx_document_sharing_status ON document_sharing(status);
CREATE INDEX IF NOT EXISTS idx_document_sharing_created_at ON document_sharing(created_at);
CREATE INDEX IF NOT EXISTS idx_document_sharing_name ON document_sharing(name);

-- Trigger for updated_at
CREATE TRIGGER set_document_sharing_updated_at
BEFORE UPDATE ON document_sharing
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
