-- Fix app_users table by adding missing columns
-- v3.1.201

-- Add preferences column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'app_users' 
                   AND column_name = 'preferences') THEN
        ALTER TABLE app_users ADD COLUMN preferences JSONB DEFAULT '{}';
    END IF;
END $$;

-- Add permissions column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'app_users' 
                   AND column_name = 'permissions') THEN
        ALTER TABLE app_users ADD COLUMN permissions JSONB DEFAULT '[]';
    END IF;
END $$;

-- Add failed_login_attempts column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'app_users' 
                   AND column_name = 'failed_login_attempts') THEN
        ALTER TABLE app_users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
    END IF;
END $$;

-- Verify columns exist
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'app_users'
AND column_name IN ('preferences', 'permissions', 'failed_login_attempts')
ORDER BY column_name;