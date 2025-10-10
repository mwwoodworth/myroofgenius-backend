-- Forums Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS forums (
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
CREATE INDEX IF NOT EXISTS idx_forums_status ON forums(status);
CREATE INDEX IF NOT EXISTS idx_forums_created_at ON forums(created_at);
CREATE INDEX IF NOT EXISTS idx_forums_name ON forums(name);

-- Trigger for updated_at
CREATE TRIGGER set_forums_updated_at
BEFORE UPDATE ON forums
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
