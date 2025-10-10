-- Fix memory_sync table by adding missing column
-- The table exists but is missing the memory_id column

-- First, check what columns currently exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;

-- Add the missing memory_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'memory_sync' 
        AND column_name = 'memory_id'
    ) THEN
        ALTER TABLE memory_sync 
        ADD COLUMN memory_id VARCHAR(255) NOT NULL DEFAULT '';
        
        -- Remove the default after adding the column
        ALTER TABLE memory_sync 
        ALTER COLUMN memory_id DROP DEFAULT;
    END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;

-- If you need to see the full table structure
\d memory_sync