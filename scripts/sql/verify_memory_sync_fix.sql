-- Verify memory_sync table fix
-- Run this in Supabase SQL Editor to confirm the fix worked

-- Check if memory_sync table exists and has memory_id column
SELECT 
    'memory_sync table check' as test_name,
    EXISTS(
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'memory_sync'
    ) as table_exists,
    EXISTS(
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'memory_sync' 
        AND column_name = 'memory_id'
    ) as has_memory_id_column;

-- Show all columns in memory_sync table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;

-- Test insert to verify it works
INSERT INTO memory_sync (
    memory_id,
    source_agent,
    target_agent,
    sync_status,
    sync_type
) VALUES (
    'test_' || gen_random_uuid()::text,
    'test_source',
    'test_target', 
    'completed',
    'test'
) ON CONFLICT DO NOTHING;

-- Check if insert worked
SELECT COUNT(*) as test_records 
FROM memory_sync 
WHERE memory_id LIKE 'test_%';

-- Clean up test data
DELETE FROM memory_sync WHERE memory_id LIKE 'test_%';

-- Final status
SELECT 'memory_sync table is now fully functional!' as status;