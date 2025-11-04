-- Fix memory_sync table schema issue
-- Error: column "memory_id" of relation "memory_sync" does not exist

-- First, check current schema
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;

-- Drop and recreate the table with correct schema
DROP TABLE IF EXISTS memory_sync CASCADE;

CREATE TABLE memory_sync (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    memory_id VARCHAR(255) NOT NULL,
    source_agent VARCHAR(100) NOT NULL,
    target_agent VARCHAR(100) NOT NULL,
    sync_status VARCHAR(50) DEFAULT 'pending',
    sync_type VARCHAR(50) DEFAULT 'full',
    sync_direction VARCHAR(50) DEFAULT 'bidirectional',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    next_sync_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_memory_sync_memory_id ON memory_sync(memory_id);
CREATE INDEX idx_memory_sync_status ON memory_sync(sync_status);
CREATE INDEX idx_memory_sync_agents ON memory_sync(source_agent, target_agent);
CREATE INDEX idx_memory_sync_created_at ON memory_sync(created_at);

-- Add update trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_memory_sync_updated_at 
    BEFORE UPDATE ON memory_sync 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Verify the fix
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;