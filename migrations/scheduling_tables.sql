-- Employee scheduling Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS scheduling (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheduling_status ON scheduling(status);
CREATE INDEX IF NOT EXISTS idx_scheduling_created_at ON scheduling(created_at);

CREATE TRIGGER set_scheduling_updated_at
BEFORE UPDATE ON scheduling
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
