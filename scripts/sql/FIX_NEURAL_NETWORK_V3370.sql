-- FIX NEURAL NETWORK DATABASE ISSUES
-- Ensure all required tables exist with proper data

-- Create ai_memory_clusters if missing
CREATE TABLE IF NOT EXISTS ai_memory_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_name VARCHAR(255),
    importance_score FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_consolidated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert a default cluster to prevent division by zero
INSERT INTO ai_memory_clusters (cluster_name, importance_score, access_count)
VALUES ('default', 0.5, 1)
ON CONFLICT DO NOTHING;

-- Ensure copilot_messages has proper structure
ALTER TABLE copilot_messages 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

ALTER TABLE copilot_messages
ADD COLUMN IF NOT EXISTS meta_data JSONB DEFAULT '{}';

-- Insert a default memory to ensure stats work
INSERT INTO copilot_messages (
    content, 
    role, 
    is_active, 
    meta_data,
    created_at
)
VALUES (
    'System initialized with neural network v3.3.69',
    'system',
    true,
    '{"agent_id": "orchestrator", "type": "initialization"}',
    NOW()
)
ON CONFLICT DO NOTHING;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_copilot_messages_active 
ON copilot_messages(is_active) 
WHERE is_active = true;