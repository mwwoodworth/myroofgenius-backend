-- Alternative approach: Rename old table and create new one with correct schema

-- Step 1: Check current columns in memory_sync
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;

-- Step 2: Rename the existing table to preserve any data
ALTER TABLE IF EXISTS memory_sync RENAME TO memory_sync_old;

-- Step 3: Create new table with correct schema
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

-- Step 4: Create indexes
CREATE INDEX idx_memory_sync_memory_id ON memory_sync(memory_id);
CREATE INDEX idx_memory_sync_status ON memory_sync(sync_status);
CREATE INDEX idx_memory_sync_agents ON memory_sync(source_agent, target_agent);
CREATE INDEX idx_memory_sync_created_at ON memory_sync(created_at);

-- Step 5: If the old table has data you want to preserve, migrate it
-- (Adjust column names based on what exists in the old table)
-- INSERT INTO memory_sync (source_agent, target_agent, sync_status, created_at)
-- SELECT source_agent, target_agent, sync_status, created_at
-- FROM memory_sync_old
-- WHERE source_agent IS NOT NULL;

-- Step 6: Verify the new table
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;

-- Step 7: Once verified, you can drop the old table
-- DROP TABLE IF EXISTS memory_sync_old;