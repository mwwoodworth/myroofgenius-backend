-- Add metadata columns to tables that need them
-- Date: 2025-10-05
-- Purpose: Fix "column metadata does not exist" errors

-- Add metadata to ai_agents table
ALTER TABLE ai_agents
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Add metadata to other tables that may need it
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Update comment
COMMENT ON COLUMN ai_agents.metadata IS 'Additional agent metadata (AI-specific configuration)';
COMMENT ON COLUMN memories.metadata IS 'Additional memory metadata (context, tags, etc)';

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_ai_agents_metadata ON ai_agents USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_memories_metadata ON memories USING gin(metadata);
