-- AI assistant Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS ai_assistant (
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
CREATE INDEX IF NOT EXISTS idx_ai_assistant_status ON ai_assistant(status);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_created_at ON ai_assistant(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_assistant_name ON ai_assistant(name);

-- Trigger for updated_at
CREATE TRIGGER set_ai_assistant_updated_at
BEFORE UPDATE ON ai_assistant
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
