-- CREATE ALL AI TABLES PROPERLY
-- This will create all missing tables without errors

-- Drop existing tables with wrong schemas
DROP TABLE IF EXISTS langgraph_state CASCADE;
DROP TABLE IF EXISTS langgraph_executions CASCADE;
DROP TABLE IF EXISTS langgraph_workflows CASCADE;
DROP TABLE IF EXISTS ai_board_decisions CASCADE;
DROP TABLE IF EXISTS ai_os_events CASCADE;
DROP TABLE IF EXISTS ai_os_components CASCADE;
DROP TABLE IF EXISTS ai_os_system_state CASCADE;

-- Create LangGraph tables
CREATE TABLE langgraph_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    graph_config JSONB,
    checkpoints JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE langgraph_executions (
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

CREATE TABLE langgraph_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id VARCHAR(255) REFERENCES langgraph_executions(execution_id),
    node_name VARCHAR(255),
    state_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create AI Board decisions table
CREATE TABLE ai_board_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
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

-- Create AI OS tables
CREATE TABLE ai_os_system_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mode VARCHAR(50) DEFAULT 'manual',
    health_score FLOAT DEFAULT 100.0,
    active_components JSONB,
    performance_metrics JSONB,
    last_mode_change TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ai_os_components (
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

CREATE TABLE ai_os_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100),
    component VARCHAR(255),
    severity VARCHAR(20),
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add sample workflows
INSERT INTO langgraph_workflows (name, description, workflow_type, status, graph_config)
VALUES 
    ('Customer Journey', 'End-to-end customer experience workflow', 'customer', 'active', '{}'),
    ('Revenue Pipeline', 'Lead to close automation', 'revenue', 'active', '{}'),
    ('Service Delivery', 'Operations optimization workflow', 'service', 'active', '{}'),
    ('AI Decision Making', 'Intelligent choice processing', 'decision', 'active', '{}'),
    ('Autonomous Operations', 'Self-running systems', 'autonomous', 'active', '{}')
ON CONFLICT DO NOTHING;

-- Initialize AI OS system state
INSERT INTO ai_os_system_state (mode, health_score, active_components)
VALUES ('manual', 100.0, '{"ai_board": true, "aurea": true, "langgraph": true}')
ON CONFLICT DO NOTHING;

-- Initialize AI OS components
INSERT INTO ai_os_components (component_name, status, health)
VALUES 
    ('ai_board', 'active', 100.0),
    ('aurea', 'active', 100.0),
    ('langgraph', 'active', 100.0),
    ('unified_os', 'active', 100.0)
ON CONFLICT DO NOTHING;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_langgraph_executions_workflow ON langgraph_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_langgraph_executions_status ON langgraph_executions(status);
CREATE INDEX IF NOT EXISTS idx_ai_board_decisions_session ON ai_board_decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_board_decisions_type ON ai_board_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_ai_os_events_created ON ai_os_events(created_at DESC);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Success
DO $$
BEGIN
    RAISE NOTICE 'All AI tables created successfully!';
    RAISE NOTICE 'LangGraph, AI Board, and AI OS tables ready.';
END $$;