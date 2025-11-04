-- Milestone tracking Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS milestone_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_milestone_tracking_status ON milestone_tracking(status);
CREATE INDEX IF NOT EXISTS idx_milestone_tracking_created_at ON milestone_tracking(created_at);

CREATE TRIGGER set_milestone_tracking_updated_at
BEFORE UPDATE ON milestone_tracking
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
