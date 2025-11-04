-- Create AI memory table for persistent context
CREATE TABLE IF NOT EXISTS ai_memory (
    id TEXT PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_ai_memory_key ON ai_memory(key);

-- Enable RLS
ALTER TABLE ai_memory ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role has full access" ON ai_memory
    FOR ALL USING (true);
