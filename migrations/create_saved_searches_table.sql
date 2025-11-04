-- Create saved searches table for customer search functionality
-- This table stores user-defined search filters for later reuse

CREATE TABLE IF NOT EXISTS saved_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    filters JSONB NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    share_token VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    use_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_saved_searches_user_id ON saved_searches(user_id);
CREATE INDEX idx_saved_searches_created_at ON saved_searches(created_at DESC);
CREATE INDEX idx_saved_searches_last_used ON saved_searches(last_used DESC NULLS LAST);
CREATE INDEX idx_saved_searches_share_token ON saved_searches(share_token) WHERE share_token IS NOT NULL;
CREATE INDEX idx_saved_searches_is_public ON saved_searches(is_public) WHERE is_public = TRUE;

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_saved_searches_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_saved_searches_updated_at
    BEFORE UPDATE ON saved_searches
    FOR EACH ROW
    EXECUTE FUNCTION update_saved_searches_updated_at();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON saved_searches TO authenticated;
GRANT USAGE ON SEQUENCE saved_searches_id_seq TO authenticated;

-- Add RLS policies
ALTER TABLE saved_searches ENABLE ROW LEVEL SECURITY;

-- Users can manage their own searches
CREATE POLICY saved_searches_owner_policy ON saved_searches
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- Users can view public searches
CREATE POLICY saved_searches_public_read_policy ON saved_searches
    FOR SELECT
    USING (is_public = TRUE);

-- Users can view searches shared with them via token
CREATE POLICY saved_searches_shared_read_policy ON saved_searches
    FOR SELECT
    USING (share_token IS NOT NULL AND share_token = current_setting('app.share_token', TRUE));
