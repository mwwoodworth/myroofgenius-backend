-- Message queuing Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS message_queuing (
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
CREATE INDEX IF NOT EXISTS idx_message_queuing_status ON message_queuing(status);
CREATE INDEX IF NOT EXISTS idx_message_queuing_created_at ON message_queuing(created_at);
CREATE INDEX IF NOT EXISTS idx_message_queuing_name ON message_queuing(name);

-- Trigger for updated_at
CREATE TRIGGER set_message_queuing_updated_at
BEFORE UPDATE ON message_queuing
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
