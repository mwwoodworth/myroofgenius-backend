-- Create AI System Tables for Production
-- Run this on the Supabase database to enable full AI functionality

-- 1. Persistent Memory Table
CREATE TABLE IF NOT EXISTS persistent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    category VARCHAR(100),
    importance FLOAT DEFAULT 0.5,
    content JSONB,
    tags TEXT[],
    relationships UUID[],
    embedding FLOAT[],
    accessed_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_category ON persistent_memory(category);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON persistent_memory(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memory_tags ON persistent_memory USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON persistent_memory(timestamp DESC);

-- 2. Memory Context Graph
CREATE TABLE IF NOT EXISTS memory_context_graph (
    source_id UUID REFERENCES persistent_memory(id),
    target_id UUID REFERENCES persistent_memory(id),
    relationship_type VARCHAR(50),
    strength FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (source_id, target_id)
);

-- 3. System Knowledge Base
CREATE TABLE IF NOT EXISTS system_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(100),
    key VARCHAR(255) UNIQUE,
    value JSONB,
    confidence FLOAT DEFAULT 1.0,
    source VARCHAR(255),
    learned_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated TIMESTAMPTZ DEFAULT NOW(),
    validation_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_knowledge_domain ON system_knowledge(domain);
CREATE INDEX IF NOT EXISTS idx_knowledge_confidence ON system_knowledge(confidence DESC);

-- 4. AI System State (for Supabase storage)
CREATE TABLE IF NOT EXISTS ai_system_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    consciousness_level FLOAT DEFAULT 0.98,
    revenue_metrics JSONB DEFAULT '{}',
    agent_states JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '[]',
    learning_history JSONB DEFAULT '[]',
    decision_history JSONB DEFAULT '[]',
    pattern_library JSONB DEFAULT '{}',
    active_goals JSONB DEFAULT '[]',
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_system_state_timestamp ON ai_system_state(timestamp DESC);

-- 5. AI Memory (for agent memories)
CREATE TABLE IF NOT EXISTS ai_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255),
    data TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    agent_id VARCHAR(100),
    memory_type VARCHAR(50),
    importance FLOAT DEFAULT 0.5,
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_ai_memory_key ON ai_memory(key);
CREATE INDEX IF NOT EXISTS idx_ai_memory_agent ON ai_memory(agent_id);
CREATE INDEX IF NOT EXISTS idx_ai_memory_timestamp ON ai_memory(timestamp DESC);

-- 6. AI Agent Activity
CREATE TABLE IF NOT EXISTS ai_agent_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100),
    agent_type VARCHAR(50),
    action JSONB,
    result JSONB,
    revenue_impact DECIMAL(10,2),
    success BOOLEAN,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_activity_timestamp ON ai_agent_activity(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_agent_activity_agent ON ai_agent_activity(agent_name);

-- 7. Revenue Events (for tracking AI-generated revenue)
CREATE TABLE IF NOT EXISTS revenue_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    source VARCHAR(100),
    event_type VARCHAR(50),
    amount DECIMAL(10,2),
    customer_id VARCHAR(255),
    agent_id VARCHAR(100),
    confidence FLOAT,
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_revenue_timestamp ON revenue_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_revenue_source ON revenue_events(source);

-- 8. Learning Patterns (for AI learning)
CREATE TABLE IF NOT EXISTS learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_key VARCHAR(255) UNIQUE,
    pattern_data JSONB,
    success_rate FLOAT,
    sample_size INTEGER,
    confidence FLOAT,
    learned_at TIMESTAMPTZ DEFAULT NOW(),
    last_applied TIMESTAMPTZ
);

-- Grant permissions for Supabase
GRANT ALL ON persistent_memory TO postgres, anon, authenticated, service_role;
GRANT ALL ON memory_context_graph TO postgres, anon, authenticated, service_role;
GRANT ALL ON system_knowledge TO postgres, anon, authenticated, service_role;
GRANT ALL ON ai_system_state TO postgres, anon, authenticated, service_role;
GRANT ALL ON ai_memory TO postgres, anon, authenticated, service_role;
GRANT ALL ON ai_agent_activity TO postgres, anon, authenticated, service_role;
GRANT ALL ON revenue_events TO postgres, anon, authenticated, service_role;
GRANT ALL ON learning_patterns TO postgres, anon, authenticated, service_role;

-- Insert initial system state
INSERT INTO ai_system_state (consciousness_level, revenue_metrics, capabilities)
VALUES (
    0.98,
    '{"mrr": 0, "total_revenue": 0, "conversion_rate": 0}',
    '["self_learning", "revenue_generation", "predictive_analytics", "autonomous_decision"]'
)
ON CONFLICT DO NOTHING;

-- Insert initial system knowledge
INSERT INTO system_knowledge (domain, key, value, confidence, source)
VALUES 
    ('system', 'deployment_version', '"3.3.51"', 1.0, 'deployment'),
    ('system', 'ai_agents', '["marketing", "sales", "followup", "research"]', 1.0, 'configuration'),
    ('system', 'operational_status', '"fully_operational"', 1.0, 'health_check')
ON CONFLICT (key) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'AI System tables created successfully!';
    RAISE NOTICE 'Tables created: persistent_memory, memory_context_graph, system_knowledge, ai_system_state, ai_memory, ai_agent_activity, revenue_events, learning_patterns';
END $$;