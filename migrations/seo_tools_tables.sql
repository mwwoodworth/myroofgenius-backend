-- SEO tools Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS seo_tools (
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
CREATE INDEX IF NOT EXISTS idx_seo_tools_status ON seo_tools(status);
CREATE INDEX IF NOT EXISTS idx_seo_tools_created_at ON seo_tools(created_at);
CREATE INDEX IF NOT EXISTS idx_seo_tools_name ON seo_tools(name);

-- Trigger for updated_at
CREATE TRIGGER set_seo_tools_updated_at
BEFORE UPDATE ON seo_tools
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
