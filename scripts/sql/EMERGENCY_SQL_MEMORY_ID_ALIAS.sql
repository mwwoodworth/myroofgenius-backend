-- EMERGENCY SQL FALLBACK SCRIPT
-- Purpose: Add 'id' column alias to memory tables if code still references it
-- Use this ONLY if production throws "column id does not exist" errors
-- Date: 2025-07-22

-- WARNING: This is a temporary fix. The proper solution is to use the correct column names in the code.

-- For memories table (if it exists and uses 'memory_id' but code expects 'id')
DO $$
BEGIN
    -- Check if memories table exists and has memory_id but not id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'memories' 
        AND column_name = 'memory_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'memories' 
        AND column_name = 'id'
    ) THEN
        -- Add id column as an alias for memory_id
        ALTER TABLE memories ADD COLUMN id UUID GENERATED ALWAYS AS (memory_id) STORED;
        RAISE NOTICE 'Added id column alias to memories table';
    END IF;
END $$;

-- For memory_entries table
DO $$
BEGIN
    -- Check if memory_entries table exists and has memory_id but not id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'memory_entries' 
        AND column_name = 'memory_id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'memory_entries' 
        AND column_name = 'id'
    ) THEN
        -- Add id column as an alias for memory_id
        ALTER TABLE memory_entries ADD COLUMN id UUID GENERATED ALWAYS AS (memory_id) STORED;
        RAISE NOTICE 'Added id column alias to memory_entries table';
    END IF;
END $$;

-- For ai_memories table (reverse case - if it has 'id' but code expects 'memory_id')
DO $$
BEGIN
    -- Check if ai_memories table exists and has id but not memory_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ai_memories' 
        AND column_name = 'id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ai_memories' 
        AND column_name = 'memory_id'
    ) THEN
        -- Add memory_id column as an alias for id
        ALTER TABLE ai_memories ADD COLUMN memory_id UUID GENERATED ALWAYS AS (id) STORED;
        RAISE NOTICE 'Added memory_id column alias to ai_memories table';
    END IF;
END $$;

-- For memory_objects table
DO $$
BEGIN
    -- Check if memory_objects table exists and has id but not memory_id
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'memory_objects' 
        AND column_name = 'id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'memory_objects' 
        AND column_name = 'memory_id'
    ) THEN
        -- Add memory_id column as an alias for id
        ALTER TABLE memory_objects ADD COLUMN memory_id UUID GENERATED ALWAYS AS (id) STORED;
        RAISE NOTICE 'Added memory_id column alias to memory_objects table';
    END IF;
END $$;

-- Create a view that provides a unified interface for memory access
CREATE OR REPLACE VIEW v_unified_memory AS
SELECT 
    COALESCE(memory_id, id) as memory_id,
    COALESCE(id, memory_id) as id,
    owner_type,
    owner_id,
    key,
    context_json as value,
    tags,
    category,
    version,
    created_at,
    updated_at,
    accessed_at
FROM memory_entries
WHERE EXISTS (SELECT 1 FROM memory_entries LIMIT 1);

-- Grant appropriate permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON v_unified_memory TO PUBLIC;

-- Summary of what this script does:
-- 1. Adds 'id' column alias to tables that only have 'memory_id'
-- 2. Adds 'memory_id' column alias to tables that only have 'id'
-- 3. Creates a unified view that provides both fields regardless of underlying schema
-- 4. This ensures the application works regardless of which field it tries to access

-- To check current schema after running:
-- SELECT table_name, column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name IN ('memories', 'memory_entries', 'ai_memories', 'memory_objects')
-- AND column_name IN ('id', 'memory_id')
-- ORDER BY table_name, column_name;