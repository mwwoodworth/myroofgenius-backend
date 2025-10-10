-- Employee offboarding Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS offboarding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_offboarding_status ON offboarding(status);
CREATE INDEX IF NOT EXISTS idx_offboarding_created_at ON offboarding(created_at);

CREATE TRIGGER set_offboarding_updated_at
BEFORE UPDATE ON offboarding
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
