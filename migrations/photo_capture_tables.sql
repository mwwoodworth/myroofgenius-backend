-- Photo capture Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS photo_capture (
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
CREATE INDEX IF NOT EXISTS idx_photo_capture_status ON photo_capture(status);
CREATE INDEX IF NOT EXISTS idx_photo_capture_created_at ON photo_capture(created_at);
CREATE INDEX IF NOT EXISTS idx_photo_capture_name ON photo_capture(name);

-- Trigger for updated_at
CREATE TRIGGER set_photo_capture_updated_at
BEFORE UPDATE ON photo_capture
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
