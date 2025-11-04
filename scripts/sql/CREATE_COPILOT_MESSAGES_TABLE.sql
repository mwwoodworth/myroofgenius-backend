-- Create copilot_messages table for dashboard and system data storage
-- This table is used by various monitoring and dashboard services

CREATE TABLE IF NOT EXISTS copilot_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    role TEXT DEFAULT 'assistant',
    memory_type TEXT,
    tags TEXT[],
    meta_data JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    is_pinned BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_copilot_messages_memory_type ON copilot_messages(memory_type);
CREATE INDEX IF NOT EXISTS idx_copilot_messages_is_active ON copilot_messages(is_active);
CREATE INDEX IF NOT EXISTS idx_copilot_messages_created_at ON copilot_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_copilot_messages_tags ON copilot_messages USING GIN(tags);

-- Add RLS policies
ALTER TABLE copilot_messages ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role full access" ON copilot_messages
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow anon read access to active messages
CREATE POLICY "Anon read active messages" ON copilot_messages
    FOR SELECT TO anon
    USING (is_active = true);

-- Grant permissions
GRANT ALL ON copilot_messages TO service_role;
GRANT SELECT ON copilot_messages TO anon;

-- Add update trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_copilot_messages_updated_at 
    BEFORE UPDATE ON copilot_messages 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment
COMMENT ON TABLE copilot_messages IS 'Storage for dashboard data, system messages, and persistent memory across all BrainOps systems';