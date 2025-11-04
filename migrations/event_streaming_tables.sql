-- Event streaming Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS event_streaming (
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
CREATE INDEX IF NOT EXISTS idx_event_streaming_status ON event_streaming(status);
CREATE INDEX IF NOT EXISTS idx_event_streaming_created_at ON event_streaming(created_at);
CREATE INDEX IF NOT EXISTS idx_event_streaming_name ON event_streaming(name);

-- Trigger for updated_at
CREATE TRIGGER set_event_streaming_updated_at
BEFORE UPDATE ON event_streaming
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
