-- Create missing AUREA knowledge table
CREATE TABLE IF NOT EXISTS aurea_os_knowledge (
    id SERIAL PRIMARY KEY,
    knowledge_id VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    content TEXT,
    source VARCHAR(255),
    confidence FLOAT DEFAULT 0.8,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create missing AI Board metrics table
CREATE TABLE IF NOT EXISTS ai_os_board_metrics (
    id SERIAL PRIMARY KEY,
    metric_id VARCHAR(255) UNIQUE NOT NULL,
    metric_type VARCHAR(100),
    value FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Create missing LangGraph nodes table
CREATE TABLE IF NOT EXISTS langgraph_os_nodes (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_id VARCHAR(255),
    node_type VARCHAR(100),
    configuration JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant all permissions on existing tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Alter table owners to postgres
ALTER TABLE aurea_os_consciousness OWNER TO postgres;
ALTER TABLE aurea_os_conversations OWNER TO postgres;
ALTER TABLE aurea_os_insights OWNER TO postgres;
ALTER TABLE aurea_os_thoughts OWNER TO postgres;
ALTER TABLE aurea_os_knowledge OWNER TO postgres;

ALTER TABLE ai_os_board_sessions OWNER TO postgres;
ALTER TABLE ai_os_board_agents OWNER TO postgres;
ALTER TABLE ai_os_board_decisions OWNER TO postgres;
ALTER TABLE ai_os_board_metrics OWNER TO postgres;
ALTER TABLE ai_os_neural_network OWNER TO postgres;

ALTER TABLE langgraph_os_workflows OWNER TO postgres;
ALTER TABLE langgraph_os_executions OWNER TO postgres;
ALTER TABLE langgraph_os_nodes OWNER TO postgres;

ALTER TABLE unified_ai_os_commands OWNER TO postgres;

-- Create indexes for the new tables
CREATE INDEX IF NOT EXISTS idx_aurea_os_knowledge_category ON aurea_os_knowledge(category);
CREATE INDEX IF NOT EXISTS idx_ai_os_board_metrics_type ON ai_os_board_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_langgraph_os_nodes_workflow ON langgraph_os_nodes(workflow_id);