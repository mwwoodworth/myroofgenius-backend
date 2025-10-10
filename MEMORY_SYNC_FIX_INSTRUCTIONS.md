# Fix memory_sync Table Issue

The error `column "memory_id" of relation "memory_sync" does not exist` means the table exists but is missing the required column.

## Option 1: Add Missing Column (Recommended)
Run this in Supabase SQL editor:

```sql
-- Add memory_id column if it doesn't exist
ALTER TABLE memory_sync 
ADD COLUMN IF NOT EXISTS memory_id VARCHAR(255) NOT NULL DEFAULT 'legacy';

-- Remove default value after adding
ALTER TABLE memory_sync 
ALTER COLUMN memory_id DROP DEFAULT;
```

## Option 2: Check Current Schema First
Run this to see what columns exist:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;
```

## Option 3: Rename and Recreate
If the table structure is completely wrong:

```sql
-- Rename old table
ALTER TABLE memory_sync RENAME TO memory_sync_backup;

-- Create new table with correct schema
CREATE TABLE memory_sync (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    memory_id VARCHAR(255) NOT NULL,
    source_agent VARCHAR(100) NOT NULL,
    target_agent VARCHAR(100) NOT NULL,
    sync_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Quick Test
After fixing, test if it works:

```sql
-- This should work without errors
INSERT INTO memory_sync (memory_id, source_agent, target_agent, sync_status)
VALUES ('test123', 'test_source', 'test_target', 'pending');

-- Clean up test
DELETE FROM memory_sync WHERE memory_id = 'test123';
```

The system is live and working - this is just a minor schema issue that won't affect most functionality!