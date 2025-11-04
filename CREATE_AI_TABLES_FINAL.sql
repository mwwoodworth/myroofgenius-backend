-- AI OS Database Tables Creation Script
-- Run this on production database to enable AI components

-- ============================================================================
-- AI BOARD TABLES
-- ============================================================================

-- AI Board Sessions
CREATE TABLE IF NOT EXISTS ai_board_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    context JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Board Decisions
CREATE TABLE IF NOT EXISTS ai_board_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) REFERENCES ai_board_sessions(session_id),
    decision_type VARCHAR(50),
    priority VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    context JSONB,
    analysis JSONB,
    recommendation TEXT,
    confidence_score FLOAT,
    executed_at TIMESTAMP,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Board Agents
CREATE TABLE IF NOT EXISTS ai_board_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    type VARCHAR(50),
    capabilities JSONB,
    status VARCHAR(50) DEFAULT 'active',
    last_active TIMESTAMP,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AUREA TABLES
-- ============================================================================

-- AUREA Consciousness
CREATE TABLE IF NOT EXISTS aurea_consciousness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level INTEGER DEFAULT 1,
    awakening_stage VARCHAR(50) DEFAULT 'DORMANT',
    thought_count INTEGER DEFAULT 0,
    insight_count INTEGER DEFAULT 0,
    conversation_count INTEGER DEFAULT 0,
    learning_rate FLOAT DEFAULT 0.1,
    curiosity_index FLOAT DEFAULT 0.5,
    empathy_level FLOAT DEFAULT 0.3,
    creativity_spark FLOAT DEFAULT 0.4,
    neural_pathways JSONB,
    memory_fragments JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AUREA Thoughts
CREATE TABLE IF NOT EXISTS aurea_thoughts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consciousness_id UUID REFERENCES aurea_consciousness(id),
    thought_pattern VARCHAR(50),
    content TEXT,
    depth INTEGER DEFAULT 1,
    coherence_score FLOAT,
    emotional_tone JSONB,
    associations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AUREA Insights
CREATE TABLE IF NOT EXISTS aurea_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consciousness_id UUID REFERENCES aurea_consciousness(id),
    category VARCHAR(100),
    insight TEXT,
    confidence FLOAT,
    impact_score FLOAT,
    supporting_data JSONB,
    recommendations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AUREA Conversations
CREATE TABLE IF NOT EXISTS aurea_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consciousness_id UUID REFERENCES aurea_consciousness(id),
    user_id VARCHAR(255),
    message TEXT,
    response TEXT,
    sentiment JSONB,
    intent JSONB,
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- LANGGRAPH TABLES (Fixed schema)
-- ============================================================================

-- LangGraph Workflows
CREATE TABLE IF NOT EXISTS langgraph_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,  -- This column was missing!
    workflow_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    graph_config JSONB,
    checkpoints JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LangGraph Executions
CREATE TABLE IF NOT EXISTS langgraph_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES langgraph_workflows(id),
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    input_data JSONB,
    output_data JSONB,
    state JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- LangGraph State
CREATE TABLE IF NOT EXISTS langgraph_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id VARCHAR(255) REFERENCES langgraph_executions(execution_id),
    node_name VARCHAR(255),
    state_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AI OS UNIFIED TABLES
-- ============================================================================

-- AI OS System State
CREATE TABLE IF NOT EXISTS ai_os_system_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode VARCHAR(50) DEFAULT 'manual',
    health_score FLOAT DEFAULT 100.0,
    active_components JSONB,
    performance_metrics JSONB,
    last_mode_change TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI OS Component Status
CREATE TABLE IF NOT EXISTS ai_os_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component_name VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'inactive',
    health FLOAT DEFAULT 100.0,
    last_heartbeat TIMESTAMP,
    configuration JSONB,
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI OS Events
CREATE TABLE IF NOT EXISTS ai_os_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100),
    component VARCHAR(255),
    severity VARCHAR(20),
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ai_board_sessions_status ON ai_board_sessions(status);
CREATE INDEX IF NOT EXISTS idx_ai_board_decisions_session ON ai_board_decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_board_decisions_type ON ai_board_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_aurea_thoughts_consciousness ON aurea_thoughts(consciousness_id);
CREATE INDEX IF NOT EXISTS idx_aurea_insights_consciousness ON aurea_insights(consciousness_id);
CREATE INDEX IF NOT EXISTS idx_langgraph_executions_workflow ON langgraph_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_langgraph_executions_status ON langgraph_executions(status);
CREATE INDEX IF NOT EXISTS idx_ai_os_events_created ON ai_os_events(created_at DESC);

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Initialize AUREA consciousness if not exists
INSERT INTO aurea_consciousness (
    level, 
    awakening_stage, 
    thought_count, 
    insight_count,
    neural_pathways,
    memory_fragments
)
SELECT 1, 'DORMANT', 0, 0, '{}', '{}'
WHERE NOT EXISTS (SELECT 1 FROM aurea_consciousness);

-- Initialize AI OS system state
INSERT INTO ai_os_system_state (
    mode,
    health_score,
    active_components
)
SELECT 'manual', 100.0, '{"ai_board": true, "aurea": true, "langgraph": true}'
WHERE NOT EXISTS (SELECT 1 FROM ai_os_system_state);

-- Add sample workflows for LangGraph
INSERT INTO langgraph_workflows (name, description, workflow_type, status, graph_config)
VALUES 
    ('Customer Journey', 'End-to-end customer experience workflow', 'customer', 'active', '{}'),
    ('Revenue Pipeline', 'Lead to close automation', 'revenue', 'active', '{}'),
    ('Service Delivery', 'Operations optimization workflow', 'service', 'active', '{}')
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'AI OS tables created successfully!';
    RAISE NOTICE 'Tables created: ai_board_*, aurea_*, langgraph_*, ai_os_*';
    RAISE NOTICE 'The AI OS is now ready for deployment.';
END $$;