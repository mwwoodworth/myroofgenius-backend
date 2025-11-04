-- Create AI OS specific tables with unique names
CREATE TABLE IF NOT EXISTS ai_os_board_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_decisions INTEGER DEFAULT 0,
    successful_decisions INTEGER DEFAULT 0,
    failed_decisions INTEGER DEFAULT 0,
    average_confidence FLOAT DEFAULT 0.0,
    average_impact FLOAT DEFAULT 0.0,
    session_metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_os_board_agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    capabilities JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    last_active TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_os_board_decisions (
    id SERIAL PRIMARY KEY,
    decision_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES ai_os_board_sessions(session_id) ON DELETE CASCADE,
    decision_type VARCHAR(100),
    priority VARCHAR(50),
    description TEXT,
    context JSONB DEFAULT '{}',
    reasoning JSONB DEFAULT '{}',
    outcome JSONB DEFAULT '{}',
    confidence_score FLOAT,
    impact_score FLOAT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_os_neural_network (
    id SERIAL PRIMARY KEY,
    network_id VARCHAR(255) UNIQUE NOT NULL,
    layer_type VARCHAR(100),
    neurons JSONB DEFAULT '[]',
    weights JSONB DEFAULT '[]',
    biases JSONB DEFAULT '[]',
    activation_function VARCHAR(50),
    learning_rate FLOAT DEFAULT 0.01,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create AUREA OS tables
CREATE TABLE IF NOT EXISTS aurea_os_consciousness (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    consciousness_level VARCHAR(100) DEFAULT 'adaptive',
    current_thoughts JSONB DEFAULT '[]',
    active_patterns JSONB DEFAULT '[]',
    emotional_state FLOAT DEFAULT 0.0,
    energy_level FLOAT DEFAULT 1.0,
    focus_areas JSONB DEFAULT '[]',
    goals JSONB DEFAULT '[]',
    learning_rate FLOAT DEFAULT 0.01,
    creativity_index FLOAT DEFAULT 0.5,
    autonomy_level FLOAT DEFAULT 0.3,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_decisions INTEGER DEFAULT 0,
    successful_outcomes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aurea_os_thoughts (
    id SERIAL PRIMARY KEY,
    thought_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES aurea_os_consciousness(session_id) ON DELETE CASCADE,
    thought_pattern VARCHAR(100),
    content TEXT,
    confidence FLOAT,
    emotional_tone FLOAT,
    associations JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aurea_os_conversations (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES aurea_os_consciousness(session_id) ON DELETE CASCADE,
    user_message TEXT,
    aurea_response TEXT,
    emotional_context JSONB DEFAULT '{}',
    decision_context JSONB DEFAULT '{}',
    learning_points JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aurea_os_insights (
    id SERIAL PRIMARY KEY,
    insight_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) REFERENCES aurea_os_consciousness(session_id) ON DELETE CASCADE,
    insight_type VARCHAR(100),
    content TEXT,
    confidence FLOAT,
    impact_score FLOAT,
    actionable BOOLEAN DEFAULT false,
    actions_taken JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create LangGraph OS tables
CREATE TABLE IF NOT EXISTS langgraph_os_workflows (
    id SERIAL PRIMARY KEY,
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    state JSONB DEFAULT '{}',
    nodes JSONB DEFAULT '[]',
    edges JSONB DEFAULT '[]',
    current_node VARCHAR(255),
    execution_history JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'idle',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS langgraph_os_executions (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_id VARCHAR(255) REFERENCES langgraph_os_workflows(workflow_id) ON DELETE CASCADE,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    execution_path JSONB DEFAULT '[]',
    duration_ms INTEGER,
    status VARCHAR(50) DEFAULT 'running',
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS unified_ai_os_commands (
    id SERIAL PRIMARY KEY,
    command_id VARCHAR(255) UNIQUE NOT NULL,
    command_type VARCHAR(100),
    payload JSONB DEFAULT '{}',
    source VARCHAR(100),
    target VARCHAR(100),
    priority INTEGER DEFAULT 5,
    status VARCHAR(50) DEFAULT 'queued',
    result JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_os_board_sessions_status ON ai_os_board_sessions(status);
CREATE INDEX IF NOT EXISTS idx_ai_os_board_decisions_session ON ai_os_board_decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_os_board_decisions_status ON ai_os_board_decisions(status);
CREATE INDEX IF NOT EXISTS idx_aurea_os_thoughts_session ON aurea_os_thoughts(session_id);
CREATE INDEX IF NOT EXISTS idx_aurea_os_conversations_session ON aurea_os_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_aurea_os_insights_session ON aurea_os_insights(session_id);
CREATE INDEX IF NOT EXISTS idx_langgraph_os_executions_workflow ON langgraph_os_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_unified_os_commands_status ON unified_ai_os_commands(status);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;