-- Natural language processing Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS natural_language (
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
CREATE INDEX IF NOT EXISTS idx_natural_language_status ON natural_language(status);
CREATE INDEX IF NOT EXISTS idx_natural_language_created_at ON natural_language(created_at);
CREATE INDEX IF NOT EXISTS idx_natural_language_name ON natural_language(name);

-- Trigger for updated_at
CREATE TRIGGER set_natural_language_updated_at
BEFORE UPDATE ON natural_language
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
