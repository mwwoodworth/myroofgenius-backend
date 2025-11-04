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

CREATE TABLE IF NOT EXISTS memory_context_graph (
        source_id UUID,
        target_id UUID,
        relationship_type VARCHAR(50),
        strength FLOAT DEFAULT 0.5,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (source_id, target_id)
    );

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

