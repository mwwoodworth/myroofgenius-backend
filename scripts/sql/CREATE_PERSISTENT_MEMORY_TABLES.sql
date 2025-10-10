-- Create persistent memory tables for AI agent system
-- Date: 2025-08-19

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing table if it has wrong schema
DROP TABLE IF EXISTS persistent_memory CASCADE;

-- Create enhanced persistent_memory table with proper schema
CREATE TABLE persistent_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL,  -- 'system_health', 'task', 'knowledge', 'error'
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_persistent_memory_type ON persistent_memory(type);
CREATE INDEX idx_persistent_memory_key ON persistent_memory(key);
CREATE INDEX idx_persistent_memory_created_at ON persistent_memory(created_at DESC);

-- Create context snapshots table for session continuity
CREATE TABLE IF NOT EXISTS context_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    context_type TEXT NOT NULL, -- 'task', 'system', 'error', 'decision'
    context_data JSONB NOT NULL,
    tags TEXT[],
    importance INT DEFAULT 5,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '30 days'
);

-- Create indexes for context snapshots
CREATE INDEX idx_context_snapshots_session ON context_snapshots(session_id);
CREATE INDEX idx_context_snapshots_type ON context_snapshots(context_type);
CREATE INDEX idx_context_snapshots_timestamp ON context_snapshots(timestamp DESC);

-- Create work history table to prevent duplication
CREATE TABLE IF NOT EXISTS work_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id TEXT,
    action TEXT NOT NULL,
    input JSONB,
    output JSONB,
    success BOOLEAN,
    error_message TEXT,
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for work history
CREATE INDEX idx_work_history_task_id ON work_history(task_id);
CREATE INDEX idx_work_history_action ON work_history(action);
CREATE INDEX idx_work_history_created_at ON work_history(created_at DESC);

-- Create knowledge base table for solutions
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    problem_signature TEXT UNIQUE,
    problem_description TEXT,
    solution TEXT NOT NULL,
    success_rate FLOAT DEFAULT 1.0,
    usage_count INT DEFAULT 0,
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for knowledge base
CREATE INDEX idx_knowledge_base_signature ON knowledge_base(problem_signature);
CREATE INDEX idx_knowledge_base_usage ON knowledge_base(usage_count DESC);
CREATE INDEX idx_knowledge_base_success_rate ON knowledge_base(success_rate DESC);

-- Create agent health monitoring table
CREATE TABLE IF NOT EXISTS agent_health_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    system_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'healthy', 'unhealthy', 'recovered'
    response_time_ms INT,
    error_message TEXT,
    recovery_attempted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for agent health logs
CREATE INDEX idx_agent_health_logs_agent ON agent_health_logs(agent_name);
CREATE INDEX idx_agent_health_logs_system ON agent_health_logs(system_name);
CREATE INDEX idx_agent_health_logs_status ON agent_health_logs(status);
CREATE INDEX idx_agent_health_logs_created_at ON agent_health_logs(created_at DESC);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for persistent_memory
CREATE TRIGGER update_persistent_memory_timestamp
    BEFORE UPDATE ON persistent_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Grant permissions
GRANT ALL ON persistent_memory TO postgres;
GRANT ALL ON context_snapshots TO postgres;
GRANT ALL ON work_history TO postgres;
GRANT ALL ON knowledge_base TO postgres;
GRANT ALL ON agent_health_logs TO postgres;

-- Insert initial system status record
INSERT INTO persistent_memory (type, key, value, metadata)
VALUES (
    'system_health',
    'initial_deployment',
    '{"status": "deployed", "version": "v8.7", "timestamp": "2025-08-19T10:51:00Z"}'::jsonb,
    '{"agent": "SystemSetup", "priority": "high"}'::jsonb
) ON CONFLICT (key) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Persistent memory tables created successfully';
    RAISE NOTICE 'Tables created: persistent_memory, context_snapshots, work_history, knowledge_base, agent_health_logs';
END $$;