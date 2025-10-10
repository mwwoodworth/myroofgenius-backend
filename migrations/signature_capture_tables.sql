-- Signature capture Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS signature_capture (
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
CREATE INDEX IF NOT EXISTS idx_signature_capture_status ON signature_capture(status);
CREATE INDEX IF NOT EXISTS idx_signature_capture_created_at ON signature_capture(created_at);
CREATE INDEX IF NOT EXISTS idx_signature_capture_name ON signature_capture(name);

-- Trigger for updated_at
CREATE TRIGGER set_signature_capture_updated_at
BEFORE UPDATE ON signature_capture
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
