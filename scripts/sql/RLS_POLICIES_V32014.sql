
-- RLS Policies for v3.2.014
-- Enable RLS on all critical tables
DO $$ 
BEGIN
    -- Enable RLS
    ALTER TABLE IF EXISTS brainops_shared_knowledge ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS prompt_trace ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS ai_agent_performance ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS memory_event_log ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS brainops_memory_events ENABLE ROW LEVEL SECURITY;
    ALTER TABLE IF EXISTS system_learning_log ENABLE ROW LEVEL SECURITY;
    
    -- Drop existing policies if they exist
    DROP POLICY IF EXISTS "allow_all" ON brainops_shared_knowledge;
    DROP POLICY IF EXISTS "allow_all" ON prompt_trace;
    DROP POLICY IF EXISTS "allow_all" ON ai_agent_performance;
    DROP POLICY IF EXISTS "allow_all" ON memory_event_log;
    DROP POLICY IF EXISTS "allow_all" ON brainops_memory_events;
    DROP POLICY IF EXISTS "allow_all" ON system_learning_log;
    
    -- Create permissive policies for now (can be tightened later)
    CREATE POLICY "allow_all" ON brainops_shared_knowledge FOR ALL USING (true);
    CREATE POLICY "allow_all" ON prompt_trace FOR ALL USING (true);
    CREATE POLICY "allow_all" ON ai_agent_performance FOR ALL USING (true);
    CREATE POLICY "allow_all" ON memory_event_log FOR ALL USING (true);
    CREATE POLICY "allow_all" ON brainops_memory_events FOR ALL USING (true);
    CREATE POLICY "allow_all" ON system_learning_log FOR ALL USING (true);
    
    RAISE NOTICE 'RLS policies applied successfully';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'RLS policy error: %', SQLERRM;
END $$;

-- Verify tables exist and have correct structure
SELECT 
    table_name,
    CASE 
        WHEN row_security_active THEN 'RLS Enabled'
        ELSE 'RLS Disabled'
    END as rls_status
FROM information_schema.tables t
LEFT JOIN pg_tables pt ON t.table_name = pt.tablename
WHERE t.table_schema = 'public' 
AND t.table_name IN (
    'brainops_shared_knowledge',
    'prompt_trace',
    'ai_agent_performance',
    'memory_event_log',
    'brainops_memory_events',
    'system_learning_log'
);
