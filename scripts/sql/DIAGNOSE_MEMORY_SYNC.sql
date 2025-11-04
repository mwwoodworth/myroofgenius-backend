-- Diagnostic queries for memory_sync table issue

-- 1. Show all columns in the current memory_sync table
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'memory_sync'
ORDER BY ordinal_position;

-- 2. Check if memory_id column exists
SELECT EXISTS (
    SELECT 1 
    FROM information_schema.columns 
    WHERE table_name = 'memory_sync' 
    AND column_name = 'memory_id'
) AS memory_id_exists;

-- 3. Show table definition
SELECT 
    table_name,
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'memory_sync';

-- 4. Count rows in the table
SELECT COUNT(*) as row_count FROM memory_sync;

-- 5. Show first few rows (if any exist)
SELECT * FROM memory_sync LIMIT 5;