-- ============================================================================
-- BrainOps Database Comprehensive Schema Fix and Optimization
-- Generated: 2025-07-23
-- Author: Senior PostgreSQL DBA
-- ============================================================================

-- This script performs a complete database optimization including:
-- 1. Critical fixes for missing primary keys and constraints
-- 2. Performance optimizations and index management  
-- 3. Data type corrections and standardization
-- 4. Security enhancements with RLS
-- 5. Naming convention fixes
-- 6. Update trigger automation

BEGIN;

-- ============================================================================
-- SECTION 1: CRITICAL FIXES - MUST BE APPLIED IMMEDIATELY
-- ============================================================================

-- 1.1 Add missing primary keys
ALTER TABLE project_members ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid() PRIMARY KEY;
ALTER TABLE team_members ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid() PRIMARY KEY;

-- 1.2 Fix version column data types (String -> Integer)
DO $$
BEGIN
    -- Fix memory_entries version column
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'memory_entries' 
               AND column_name = 'version' 
               AND data_type LIKE '%char%') THEN
        UPDATE memory_entries SET version = '1' WHERE version IS NULL OR version = '';
        UPDATE memory_entries SET version = FLOOR(version::numeric)::text WHERE version ~ '^[0-9]+(\.[0-9]+)?$';
        ALTER TABLE memory_entries ALTER COLUMN version TYPE INTEGER USING version::integer;
        ALTER TABLE memory_entries ALTER COLUMN version SET DEFAULT 1;
    END IF;
    
    -- Fix other tables with version columns
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'automation_workflows' 
               AND column_name = 'version' 
               AND data_type LIKE '%char%') THEN
        ALTER TABLE automation_workflows ADD COLUMN version_new INTEGER DEFAULT 1;
        UPDATE automation_workflows SET version_new = 
            CASE 
                WHEN version ~ '^[0-9]+$' THEN version::integer
                WHEN version ~ '^[0-9]+\.' THEN FLOOR(version::numeric)::integer
                ELSE 1
            END;
        ALTER TABLE automation_workflows DROP COLUMN version;
        ALTER TABLE automation_workflows RENAME COLUMN version_new TO version;
    END IF;
END $$;

-- ============================================================================
-- SECTION 2: TIMESTAMP DEFAULTS AND NOT NULL CONSTRAINTS
-- ============================================================================

-- 2.1 Create helper function for safe timestamp updates
CREATE OR REPLACE FUNCTION fix_timestamp_column(
    p_table_name TEXT,
    p_column_name TEXT,
    p_default_value TEXT DEFAULT 'CURRENT_TIMESTAMP'
) RETURNS VOID AS $$
BEGIN
    -- Add default
    EXECUTE format('ALTER TABLE %I ALTER COLUMN %I SET DEFAULT %s', 
                   p_table_name, p_column_name, p_default_value);
    
    -- Update NULL values
    EXECUTE format('UPDATE %I SET %I = %s WHERE %I IS NULL', 
                   p_table_name, p_column_name, p_default_value, p_column_name);
    
    -- Make NOT NULL if it's a standard timestamp column
    IF p_column_name IN ('created_at', 'updated_at') THEN
        EXECUTE format('ALTER TABLE %I ALTER COLUMN %I SET NOT NULL', 
                       p_table_name, p_column_name);
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not fix %.%: %', p_table_name, p_column_name, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- 2.2 Fix all timestamp columns
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_name IN ('created_at', 'updated_at', 'deleted_at', 'accessed_at')
        AND (column_default IS NULL OR column_default NOT LIKE '%CURRENT_TIMESTAMP%')
    LOOP
        PERFORM fix_timestamp_column(r.table_name, r.column_name);
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 3: DATA TYPE OPTIMIZATIONS
-- ============================================================================

-- 3.1 Fix VARCHAR without length to TEXT
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND data_type = 'character varying'
        AND character_maximum_length IS NULL
    LOOP
        EXECUTE format('ALTER TABLE %I ALTER COLUMN %I TYPE TEXT', 
                       r.table_name, r.column_name);
    END LOOP;
END $$;

-- 3.2 Standardize email columns
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_name LIKE '%email%'
        AND (data_type != 'character varying' OR character_maximum_length > 255)
    LOOP
        EXECUTE format('ALTER TABLE %I ALTER COLUMN %I TYPE VARCHAR(255)', 
                       r.table_name, r.column_name);
    END LOOP;
END $$;

-- 3.3 Standardize phone columns
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_name LIKE '%phone%'
        AND (data_type != 'character varying' OR character_maximum_length > 50)
    LOOP
        EXECUTE format('ALTER TABLE %I ALTER COLUMN %I TYPE VARCHAR(50)', 
                       r.table_name, r.column_name);
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 4: PERFORMANCE INDEXES
-- ============================================================================

-- 4.1 Create indexes for all foreign key columns
DO $$
DECLARE
    r RECORD;
    index_name TEXT;
BEGIN
    FOR r IN 
        SELECT DISTINCT
            kcu.table_name,
            kcu.column_name
        FROM information_schema.key_column_usage kcu
        JOIN information_schema.table_constraints tc 
            ON kcu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND kcu.table_schema = 'public'
    LOOP
        index_name := 'idx_' || r.table_name || '_' || r.column_name;
        
        -- Check if index already exists
        IF NOT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename = r.table_name 
            AND indexdef LIKE '%' || r.column_name || '%'
        ) THEN
            EXECUTE format('CREATE INDEX %I ON %I (%I)', 
                           index_name, r.table_name, r.column_name);
        END IF;
    END LOOP;
END $$;

-- 4.2 Create composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_memory_entries_owner_lookup 
    ON memory_entries(owner_type, owner_id, key);
CREATE INDEX IF NOT EXISTS idx_memory_entries_timestamp_range 
    ON memory_entries(created_at DESC, accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_communications_lookup 
    ON communications(lead_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_status_date 
    ON projects(status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_assignment 
    ON tasks(assigned_to, status, due_date);

-- 4.3 Drop unused indexes (commented out for safety - review before uncommenting)
/*
DROP INDEX IF EXISTS idx_memory_sync_initiated_at;
DROP INDEX IF EXISTS idx_sync_time;
DROP INDEX IF EXISTS idx_session_id;
DROP INDEX IF EXISTS idx_importance;
-- Add more unused indexes from the analysis
*/

-- ============================================================================
-- SECTION 5: UPDATE TRIGGERS
-- ============================================================================

-- 5.1 Create or replace the update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5.2 Apply update triggers to all tables with updated_at column
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT DISTINCT table_name 
        FROM information_schema.columns 
        WHERE column_name = 'updated_at' 
        AND table_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON %I', 
                       r.table_name, r.table_name);
        EXECUTE format('CREATE TRIGGER update_%I_updated_at 
                        BEFORE UPDATE ON %I 
                        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()', 
                       r.table_name, r.table_name);
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 6: SECURITY - ROW LEVEL SECURITY
-- ============================================================================

-- 6.1 Enable RLS on user-facing tables
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND rowsecurity = false
        AND tablename NOT IN (
            'spatial_ref_sys', 'alembic_version', 'schema_migrations',
            'system_config', 'system_secrets', 'database_health_checks'
        )
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', r.tablename);
    END LOOP;
END $$;

-- 6.2 Create basic RLS policies for common tables
-- Note: These are basic policies - adjust based on your security requirements

-- Users table - users can only see their own record
CREATE POLICY users_select_own ON users 
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY users_update_own ON users 
    FOR UPDATE USING (auth.uid() = id);

-- Projects - users can see projects they're members of
CREATE POLICY projects_select_members ON projects 
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM project_members 
            WHERE project_id = projects.id 
            AND user_id = auth.uid()
        )
    );

-- Add more policies as needed...

-- ============================================================================
-- SECTION 7: CONSTRAINTS AND VALIDATIONS
-- ============================================================================

-- 7.1 Add check constraints for common validations
ALTER TABLE users ADD CONSTRAINT chk_users_email 
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

ALTER TABLE projects ADD CONSTRAINT chk_projects_status 
    CHECK (status IN ('draft', 'active', 'completed', 'cancelled', 'on_hold'));

ALTER TABLE invoices ADD CONSTRAINT chk_invoices_amount 
    CHECK (total_amount >= 0);

ALTER TABLE tasks ADD CONSTRAINT chk_tasks_dates 
    CHECK (due_date IS NULL OR due_date >= created_at);

-- 7.2 Add NOT NULL constraints on critical fields
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Add NOT NULL to _type and _status columns
    FOR r IN 
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND is_nullable = 'YES'
        AND (column_name LIKE '%_type' OR column_name LIKE '%_status')
    LOOP
        -- Set default values first
        EXECUTE format('UPDATE %I SET %I = %L WHERE %I IS NULL', 
                       r.table_name, r.column_name, 'unknown', r.column_name);
        -- Then add NOT NULL
        EXECUTE format('ALTER TABLE %I ALTER COLUMN %I SET NOT NULL', 
                       r.table_name, r.column_name);
    END LOOP;
END $$;

-- ============================================================================
-- SECTION 8: CLEANUP AND MAINTENANCE
-- ============================================================================

-- 8.1 Update table statistics
ANALYZE;

-- 8.2 Create maintenance function
CREATE OR REPLACE FUNCTION perform_database_maintenance()
RETURNS TABLE(
    action TEXT,
    details TEXT
) AS $$
BEGIN
    -- Vacuum tables with high dead tuple ratio
    FOR action, details IN
        SELECT 
            'VACUUM ' || schemaname || '.' || tablename,
            'Dead tuples: ' || n_dead_tup || ', Live tuples: ' || n_live_tup
        FROM pg_stat_user_tables
        WHERE n_dead_tup > 1000 
        AND n_dead_tup > n_live_tup * 0.2
    LOOP
        EXECUTE action;
        RETURN NEXT;
    END LOOP;
    
    -- Reindex tables with bloated indexes
    FOR action, details IN
        SELECT 
            'REINDEX TABLE ' || schemaname || '.' || tablename,
            'Table size: ' || pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
        FROM pg_tables t
        JOIN pg_stat_user_tables s ON t.tablename = s.relname
        WHERE schemaname = 'public'
        AND pg_total_relation_size(schemaname||'.'||tablename) > 10485760 -- 10MB
    LOOP
        EXECUTE action;
        RETURN NEXT;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- 8.3 Create monitoring views
CREATE OR REPLACE VIEW v_table_health AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_ratio,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

CREATE OR REPLACE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan;

-- ============================================================================
-- SECTION 9: FINAL VALIDATIONS
-- ============================================================================

-- 9.1 Validate all fixes were applied
DO $$
DECLARE
    issues INTEGER := 0;
    r RECORD;
BEGIN
    -- Check for tables without primary keys
    FOR r IN 
        SELECT t.table_name
        FROM information_schema.tables t
        LEFT JOIN information_schema.table_constraints tc 
            ON t.table_name = tc.table_name 
            AND tc.constraint_type = 'PRIMARY KEY'
        WHERE t.table_schema = 'public' 
        AND t.table_type = 'BASE TABLE'
        AND tc.constraint_name IS NULL
    LOOP
        RAISE WARNING 'Table % still missing PRIMARY KEY', r.table_name;
        issues := issues + 1;
    END LOOP;
    
    -- Check for timestamp columns without defaults
    FOR r IN 
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_name IN ('created_at', 'updated_at')
        AND column_default IS NULL
    LOOP
        RAISE WARNING 'Column %.% still missing default', r.table_name, r.column_name;
        issues := issues + 1;
    END LOOP;
    
    IF issues = 0 THEN
        RAISE NOTICE 'All validations passed successfully!';
    ELSE
        RAISE WARNING 'Found % remaining issues', issues;
    END IF;
END $$;

-- Drop helper function
DROP FUNCTION IF EXISTS fix_timestamp_column(TEXT, TEXT, TEXT);

COMMIT;

-- ============================================================================
-- POST-MIGRATION NOTES
-- ============================================================================
-- 1. Review and uncomment the index drops in Section 4.3 after confirming they're truly unused
-- 2. Adjust RLS policies in Section 6.2 based on your application's security model
-- 3. Run VACUUM FULL on large tables during maintenance window
-- 4. Consider partitioning for tables over 10GB
-- 5. Set up regular maintenance using the perform_database_maintenance() function
-- 6. Monitor using v_table_health and v_index_usage views
-- ============================================================================