-- Video conferencing Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS video_conferencing (
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
CREATE INDEX IF NOT EXISTS idx_video_conferencing_status ON video_conferencing(status);
CREATE INDEX IF NOT EXISTS idx_video_conferencing_created_at ON video_conferencing(created_at);
CREATE INDEX IF NOT EXISTS idx_video_conferencing_name ON video_conferencing(name);

-- Trigger for updated_at
CREATE TRIGGER set_video_conferencing_updated_at
BEFORE UPDATE ON video_conferencing
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
