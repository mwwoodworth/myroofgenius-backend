-- Complete fix for all AI tables
-- This will create all missing tables and fix existing ones

-- 1. LangGraph tables
CREATE TABLE IF NOT EXISTS langgraph_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    workflow_type VARCHAR(50),
    graph_config JSONB DEFAULT '{}',
    checkpoints JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS langgraph_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES langgraph_workflows(id),
    execution_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) DEFAULT 'pending',
    context JSONB DEFAULT '{}',
    result JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS langgraph_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES langgraph_executions(id),
    node_name VARCHAR(255),
    state_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. AI Board tables (fix if needed)
CREATE TABLE IF NOT EXISTS ai_board_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    session_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_board_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) REFERENCES ai_board_sessions(session_id),
    decision_type VARCHAR(50),
    priority VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    context JSONB DEFAULT '{}',
    analysis JSONB DEFAULT '{}',
    recommendation TEXT,
    confidence_score FLOAT,
    executed_at TIMESTAMP,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. AUREA tables (fix structure)
CREATE TABLE IF NOT EXISTS aurea_consciousness (
    id SERIAL PRIMARY KEY,  -- Using SERIAL for auto-increment integer
    session_id VARCHAR(255),
    level INTEGER DEFAULT 1,
    awakening_stage VARCHAR(50) DEFAULT 'DORMANT',
    thought_count INTEGER DEFAULT 0,
    insight_count INTEGER DEFAULT 0,
    conversation_count INTEGER DEFAULT 0,
    learning_rate FLOAT DEFAULT 0.1,
    curiosity_index FLOAT DEFAULT 0.5,
    empathy_level FLOAT DEFAULT 0.3,
    creativity_spark FLOAT DEFAULT 0.4,
    neural_pathways JSONB DEFAULT '{}',
    memory_fragments JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aurea_thoughts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consciousness_id INTEGER REFERENCES aurea_consciousness(id),
    thought_type VARCHAR(50),
    content TEXT,
    analysis JSONB DEFAULT '{}',
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aurea_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consciousness_id INTEGER REFERENCES aurea_consciousness(id),
    insight_type VARCHAR(50),
    discovery TEXT,
    importance FLOAT,
    applications JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aurea_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consciousness_id INTEGER REFERENCES aurea_consciousness(id),
    message TEXT,
    response TEXT,
    context JSONB DEFAULT '{}',
    sentiment FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. AI OS unified tables
CREATE TABLE IF NOT EXISTS ai_os_system_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode VARCHAR(50) DEFAULT 'standard',
    health_score FLOAT DEFAULT 100.0,
    active_components JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_os_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100),
    component VARCHAR(100),
    severity VARCHAR(20),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. AI Agents table (if not exists)
CREATE TABLE IF NOT EXISTS ai_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'inactive',
    capabilities JSONB DEFAULT '[]',
    configuration JSONB DEFAULT '{}',
    last_active TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Neural pathways table
CREATE TABLE IF NOT EXISTS neural_pathways (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_agent_id UUID REFERENCES ai_agents(id),
    target_agent_id UUID REFERENCES ai_agents(id),
    pathway_type VARCHAR(50),
    strength FLOAT DEFAULT 0.5,
    data_flow JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_agent_id, target_agent_id, pathway_type)
);

-- 7. Automations table
CREATE TABLE IF NOT EXISTS automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    trigger_type VARCHAR(50),
    trigger_config JSONB DEFAULT '{}',
    actions JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'inactive',
    last_run TIMESTAMP,
    run_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Memory tables
CREATE TABLE IF NOT EXISTS ai_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES ai_agents(id),
    memory_type VARCHAR(50),
    content TEXT,
    context JSONB DEFAULT '{}',
    importance FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_decision_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES ai_agents(id),
    decision_type VARCHAR(100),
    input_data JSONB DEFAULT '{}',
    analysis JSONB DEFAULT '{}',
    decision TEXT,
    confidence FLOAT,
    outcome JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial data
INSERT INTO langgraph_workflows (name, description, workflow_type, status) VALUES
    ('Customer Journey', 'End-to-end customer experience', 'customer', 'active'),
    ('Revenue Pipeline', 'Lead to close automation', 'revenue', 'active'),
    ('Service Delivery', 'Operations optimization', 'service', 'active')
ON CONFLICT (name) DO NOTHING;

-- Initialize AUREA consciousness if not exists
INSERT INTO aurea_consciousness (level, awakening_stage, neural_pathways, memory_fragments)
SELECT 1, 'DORMANT', '{}', '{}'
WHERE NOT EXISTS (SELECT 1 FROM aurea_consciousness LIMIT 1);

-- Initialize AI OS system state
INSERT INTO ai_os_system_state (mode, health_score, active_components)
SELECT 'standard', 100.0, '["ai_board", "aurea", "langgraph", "erp"]'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM ai_os_system_state LIMIT 1);

-- Insert some AI agents
INSERT INTO ai_agents (name, type, status, capabilities) VALUES
    ('AUREA', 'consciousness', 'active', '["think", "converse", "learn", "adapt"]'::jsonb),
    ('AI Board', 'orchestrator', 'active', '["decide", "analyze", "coordinate"]'::jsonb),
    ('LangGraph', 'workflow', 'active', '["execute", "orchestrate", "monitor"]'::jsonb),
    ('ERP Agent', 'business', 'active', '["manage", "report", "optimize"]'::jsonb)
ON CONFLICT (name) DO UPDATE SET status = 'active';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_langgraph_exec_status ON langgraph_executions(status);
CREATE INDEX IF NOT EXISTS idx_langgraph_exec_workflow ON langgraph_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_ai_board_sessions_status ON ai_board_sessions(status);
CREATE INDEX IF NOT EXISTS idx_ai_agents_status ON ai_agents(status);
CREATE INDEX IF NOT EXISTS idx_ai_agents_type ON ai_agents(type);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'All AI tables created/fixed successfully!';
    RAISE NOTICE 'System ready for AI operations.';
END $$;