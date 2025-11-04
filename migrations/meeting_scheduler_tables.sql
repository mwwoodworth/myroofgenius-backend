-- Meeting scheduler Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS meeting_scheduler (
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
CREATE INDEX IF NOT EXISTS idx_meeting_scheduler_status ON meeting_scheduler(status);
CREATE INDEX IF NOT EXISTS idx_meeting_scheduler_created_at ON meeting_scheduler(created_at);
CREATE INDEX IF NOT EXISTS idx_meeting_scheduler_name ON meeting_scheduler(name);

-- Trigger for updated_at
CREATE TRIGGER set_meeting_scheduler_updated_at
BEFORE UPDATE ON meeting_scheduler
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
