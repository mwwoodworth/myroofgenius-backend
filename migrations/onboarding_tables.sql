-- Employee onboarding Tables
-- Auto-generated migration

CREATE TABLE IF NOT EXISTS onboarding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_onboarding_status ON onboarding(status);
CREATE INDEX IF NOT EXISTS idx_onboarding_created_at ON onboarding(created_at);

CREATE TRIGGER set_onboarding_updated_at
BEFORE UPDATE ON onboarding
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
