-- Live chat Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS live_chat (
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
CREATE INDEX IF NOT EXISTS idx_live_chat_status ON live_chat(status);
CREATE INDEX IF NOT EXISTS idx_live_chat_created_at ON live_chat(created_at);
CREATE INDEX IF NOT EXISTS idx_live_chat_name ON live_chat(name);

-- Trigger for updated_at
CREATE TRIGGER set_live_chat_updated_at
BEFORE UPDATE ON live_chat
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
