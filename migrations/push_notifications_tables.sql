-- Push notifications Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS push_notifications (
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
CREATE INDEX IF NOT EXISTS idx_push_notifications_status ON push_notifications(status);
CREATE INDEX IF NOT EXISTS idx_push_notifications_created_at ON push_notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_push_notifications_name ON push_notifications(name);

-- Trigger for updated_at
CREATE TRIGGER set_push_notifications_updated_at
BEFORE UPDATE ON push_notifications
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
