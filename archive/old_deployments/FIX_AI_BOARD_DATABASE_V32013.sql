-- 🚨 EMERGENCY DATABASE FIX FOR AI BOARD v3.2.013
-- Execute immediately to restore full functionality

-- 1. Create missing brainops_shared_knowledge table
CREATE TABLE IF NOT EXISTS brainops_shared_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_type TEXT,
    tags TEXT[],
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Create missing prompt_trace table
CREATE TABLE IF NOT EXISTS prompt_trace (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT,
    response TEXT,
    confidence FLOAT,
    agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Create ai_agent_performance table
CREATE TABLE IF NOT EXISTS ai_agent_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    success_rate FLOAT,
    avg_response_time_ms FLOAT,
    total_interactions INT,
    performance_data JSONB,
    project TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Create memory_event_log table
CREATE TABLE IF NOT EXISTS memory_event_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT,
    event_type TEXT,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Create brainops_memory_events table
CREATE TABLE IF NOT EXISTS brainops_memory_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project TEXT,
    event_type TEXT,
    event_data JSONB,
    severity TEXT,
    timestamp TIMESTAMPTZ DEFAULT now()
);

-- 6. Fix system_learning_log table constraints
ALTER TABLE system_learning_log ADD COLUMN IF NOT EXISTS agent_name TEXT;
ALTER TABLE system_learning_log ALTER COLUMN agent_name DROP NOT NULL;
ALTER TABLE system_learning_log ADD COLUMN IF NOT EXISTS learning_type TEXT;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_brainops_shared_knowledge_type ON brainops_shared_knowledge(knowledge_type);
CREATE INDEX IF NOT EXISTS idx_brainops_shared_knowledge_created ON brainops_shared_knowledge(created_at);
CREATE INDEX IF NOT EXISTS idx_prompt_trace_agent ON prompt_trace(agent);
CREATE INDEX IF NOT EXISTS idx_prompt_trace_created ON prompt_trace(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_agent_performance_name ON ai_agent_performance(agent_name);
CREATE INDEX IF NOT EXISTS idx_memory_event_log_user ON memory_event_log(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_event_log_type ON memory_event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_brainops_memory_events_project ON brainops_memory_events(project);
CREATE INDEX IF NOT EXISTS idx_brainops_memory_events_severity ON brainops_memory_events(severity);

-- Grant permissions
GRANT ALL ON brainops_shared_knowledge TO postgres;
GRANT ALL ON prompt_trace TO postgres;
GRANT ALL ON ai_agent_performance TO postgres;
GRANT ALL ON memory_event_log TO postgres;
GRANT ALL ON brainops_memory_events TO postgres;

-- Verify tables exist
SELECT 'brainops_shared_knowledge' as table_name, EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'brainops_shared_knowledge'
) as exists
UNION ALL
SELECT 'prompt_trace', EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'prompt_trace'
)
UNION ALL
SELECT 'ai_agent_performance', EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'ai_agent_performance'
)
UNION ALL
SELECT 'memory_event_log', EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'memory_event_log'
)
UNION ALL
SELECT 'brainops_memory_events', EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'brainops_memory_events'
);