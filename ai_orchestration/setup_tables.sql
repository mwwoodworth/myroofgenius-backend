-- AI Orchestration System Tables
-- This creates the persistent memory brain for all AI agents

-- Agent Registry: All AI agents in the system
CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id UUID PRIMARY KEY,
    agent_name VARCHAR(100) UNIQUE NOT NULL,
    specialization TEXT,
    capabilities JSONB,
    last_active TIMESTAMP,
    status VARCHAR(50) DEFAULT 'offline',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    configuration JSONB DEFAULT '{}'::jsonb
);

-- Agent Memory: Persistent memory for agents
CREATE TABLE IF NOT EXISTS agent_memory (
    memory_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agent_registry(agent_id) ON DELETE CASCADE,
    memory_type VARCHAR(50), -- knowledge, experience, error, solution, pattern, insight
    content JSONB NOT NULL,
    embedding VECTOR(1536), -- for semantic search (requires pgvector extension)
    relevance_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, -- optional expiration for temporary memories
    tags TEXT[] DEFAULT '{}' -- for categorization
);

-- Agent Communications: Inter-agent messaging
CREATE TABLE IF NOT EXISTS agent_communications (
    message_id UUID PRIMARY KEY,
    from_agent UUID REFERENCES agent_registry(agent_id),
    to_agent UUID REFERENCES agent_registry(agent_id),
    message_type VARCHAR(50), -- query, response, alert, update, request, report
    content JSONB NOT NULL,
    priority INTEGER DEFAULT 5,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    response_to UUID REFERENCES agent_communications(message_id) -- for threading
);

-- System State: Current state of all system components
CREATE TABLE IF NOT EXISTS system_state (
    state_id UUID PRIMARY KEY,
    component VARCHAR(100) UNIQUE NOT NULL, -- backend, frontend_mrg, frontend_wc, database, etc
    health_status VARCHAR(50) DEFAULT 'unknown', -- healthy, warning, error, critical, offline
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metrics JSONB DEFAULT '{}'::jsonb,
    issues JSONB DEFAULT '[]'::jsonb,
    agent_owner UUID REFERENCES agent_registry(agent_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orchestration Workflows: Defined workflows for agent coordination
CREATE TABLE IF NOT EXISTS orchestration_workflows (
    workflow_id UUID PRIMARY KEY,
    workflow_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    trigger_conditions JSONB, -- conditions that trigger this workflow
    agent_sequence JSONB[], -- ordered list of agents to activate
    status VARCHAR(50) DEFAULT 'inactive',
    last_execution TIMESTAMP,
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Executions: History of workflow runs
CREATE TABLE IF NOT EXISTS workflow_executions (
    execution_id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES orchestration_workflows(workflow_id),
    triggered_by VARCHAR(100), -- agent_id, schedule, manual, event
    trigger_data JSONB,
    status VARCHAR(50), -- running, completed, failed, cancelled
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    execution_log JSONB DEFAULT '[]'::jsonb,
    result JSONB
);

-- Agent Tasks: Tasks assigned to agents
CREATE TABLE IF NOT EXISTS agent_tasks (
    task_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agent_registry(agent_id),
    task_type VARCHAR(100),
    task_data JSONB,
    priority INTEGER DEFAULT 5,
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result JSONB,
    error TEXT
);

-- System Events: Important system events for learning
CREATE TABLE IF NOT EXISTS system_events (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR(100), -- error, deployment, commit, api_call, etc
    source VARCHAR(100), -- which component/agent
    severity VARCHAR(20), -- info, warning, error, critical
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    processed_by UUID REFERENCES agent_registry(agent_id)
);

-- Learning Episodes: Captured learning experiences
CREATE TABLE IF NOT EXISTS learning_episodes (
    episode_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agent_registry(agent_id),
    episode_type VARCHAR(50), -- success, failure, discovery, optimization
    context JSONB,
    actions_taken JSONB,
    outcome JSONB,
    lessons_learned TEXT[],
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_id ON agent_memory(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_type ON agent_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_agent_memory_created ON agent_memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_communications_to ON agent_communications(to_agent, processed);
CREATE INDEX IF NOT EXISTS idx_agent_communications_from ON agent_communications(from_agent);
CREATE INDEX IF NOT EXISTS idx_system_state_component ON system_state(component);
CREATE INDEX IF NOT EXISTS idx_system_state_status ON system_state(health_status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent ON agent_tasks(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events(event_type, processed);
CREATE INDEX IF NOT EXISTS idx_learning_episodes_agent ON learning_episodes(agent_id);

-- GIN index for JSONB search
CREATE INDEX IF NOT EXISTS idx_agent_memory_content ON agent_memory USING gin(content);
CREATE INDEX IF NOT EXISTS idx_system_events_data ON system_events USING gin(event_data);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_agent_memory_updated_at BEFORE UPDATE ON agent_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_state_updated_at BEFORE UPDATE ON system_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orchestration_workflows_updated_at BEFORE UPDATE ON orchestration_workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default workflows
INSERT INTO orchestration_workflows (workflow_id, workflow_name, description, trigger_conditions, agent_sequence)
VALUES 
    (gen_random_uuid(), 'system_health_check', 'Daily system health check', 
     '{"schedule": "daily", "time": "00:00"}'::jsonb,
     ARRAY['{"agent": "SystemArchitect", "action": "scan_system"}'::jsonb,
           '{"agent": "DatabaseAgent", "action": "check_health"}'::jsonb,
           '{"agent": "ErrorAgent", "action": "analyze_logs"}'::jsonb]),
    
    (gen_random_uuid(), 'error_resolution', 'Automatic error resolution',
     '{"trigger": "error_detected"}'::jsonb,
     ARRAY['{"agent": "ErrorAgent", "action": "analyze"}'::jsonb,
           '{"agent": "SystemArchitect", "action": "identify_component"}'::jsonb,
           '{"agent": "SpecialistAgent", "action": "fix"}'::jsonb]),
    
    (gen_random_uuid(), 'deployment_update', 'Handle deployment updates',
     '{"trigger": "deployment_webhook"}'::jsonb,
     ARRAY['{"agent": "DeploymentAgent", "action": "verify"}'::jsonb,
           '{"agent": "SystemArchitect", "action": "update_state"}'::jsonb,
           '{"agent": "MonitoringAgent", "action": "track"}'::jsonb])
ON CONFLICT (workflow_name) DO NOTHING;

-- Grant permissions (adjust as needed)
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- SYSTEM STATE SECURITY HARDENING (V8)
-- Revoke insecure defaults
REVOKE ALL ON TABLE system_state FROM anon;
REVOKE ALL ON TABLE system_state FROM authenticated;
REVOKE ALL ON TABLE system_state FROM app_agent_role;

-- Grant secure access
GRANT ALL ON TABLE system_state TO service_role;
GRANT SELECT ON TABLE system_state TO app_backend_role;
GRANT SELECT ON TABLE system_state TO app_mcp_role;

-- Enable RLS
ALTER TABLE system_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_state FORCE ROW LEVEL SECURITY;

-- Apply Policies
DROP POLICY IF EXISTS "service_role_all" ON system_state;
CREATE POLICY "service_role_all" ON system_state FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "backend_role_read" ON system_state;
CREATE POLICY "backend_role_read" ON system_state FOR SELECT TO app_backend_role USING (true);

DROP POLICY IF EXISTS "mcp_role_read" ON system_state;
CREATE POLICY "mcp_role_read" ON system_state FOR SELECT TO app_mcp_role USING (true);
