-- Social media integration Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS social_media_integration (
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
CREATE INDEX IF NOT EXISTS idx_social_media_integration_status ON social_media_integration(status);
CREATE INDEX IF NOT EXISTS idx_social_media_integration_created_at ON social_media_integration(created_at);
CREATE INDEX IF NOT EXISTS idx_social_media_integration_name ON social_media_integration(name);

-- Trigger for updated_at
CREATE TRIGGER set_social_media_integration_updated_at
BEFORE UPDATE ON social_media_integration
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
