-- Gantt charts Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS gantt_charts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gantt_charts_status ON gantt_charts(status);
CREATE INDEX IF NOT EXISTS idx_gantt_charts_created_at ON gantt_charts(created_at);

CREATE TRIGGER set_gantt_charts_updated_at
BEFORE UPDATE ON gantt_charts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
