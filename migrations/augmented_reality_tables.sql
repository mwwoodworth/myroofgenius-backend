-- Augmented reality Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS augmented_reality (
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
CREATE INDEX IF NOT EXISTS idx_augmented_reality_status ON augmented_reality(status);
CREATE INDEX IF NOT EXISTS idx_augmented_reality_created_at ON augmented_reality(created_at);
CREATE INDEX IF NOT EXISTS idx_augmented_reality_name ON augmented_reality(name);

-- Trigger for updated_at
CREATE TRIGGER set_augmented_reality_updated_at
BEFORE UPDATE ON augmented_reality
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
