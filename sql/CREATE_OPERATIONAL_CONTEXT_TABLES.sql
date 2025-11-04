-- BrainOps Operational Context System
-- Ensures we NEVER lose track and maintain 24/7 autonomous operations
-- Created: 2025-08-19
-- Based on comprehensive blueprint analysis

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. System Blueprint Table - Single source of truth
CREATE TABLE IF NOT EXISTS operational_blueprint (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(20) NOT NULL,
    section VARCHAR(100) NOT NULL,
    subsection VARCHAR(100),
    content JSONB NOT NULL,
    priority INTEGER DEFAULT 0, -- 0=info, 1=important, 2=critical, 3=urgent
    status VARCHAR(50) DEFAULT 'active',
    dependencies JSONB DEFAULT '[]'::jsonb,
    implementation_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_referenced TIMESTAMPTZ DEFAULT NOW(),
    reference_count INTEGER DEFAULT 0,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    UNIQUE(version, section, subsection)
);

-- 2. Real-time System Status - Live operational context
CREATE TABLE IF NOT EXISTS operational_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- healthy, degraded, critical, offline
    health_score DECIMAL(5,2),
    last_check TIMESTAMPTZ DEFAULT NOW(),
    metrics JSONB DEFAULT '{}',
    errors JSONB DEFAULT '[]'::jsonb,
    warnings JSONB DEFAULT '[]'::jsonb,
    auto_recovery_attempts INTEGER DEFAULT 0,
    human_intervention_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(component)
);

-- 3. Deployment Registry - Track all deployments
CREATE TABLE IF NOT EXISTS deployment_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    environment VARCHAR(50) NOT NULL, -- dev, staging, production
    deployment_type VARCHAR(50), -- docker, vercel, render
    commit_hash VARCHAR(100),
    docker_image VARCHAR(255),
    deploy_hook VARCHAR(500),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    rollback_version VARCHAR(50),
    deployment_logs TEXT,
    created_by VARCHAR(100) DEFAULT 'claude-code',
    metadata JSONB DEFAULT '{}',
    UNIQUE(service, version, environment)
);

-- 4. MCP Integration Registry - Track all MCP connections
CREATE TABLE IF NOT EXISTS mcp_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service VARCHAR(100) NOT NULL,
    tool_count INTEGER,
    status VARCHAR(50) DEFAULT 'disconnected',
    connection_url VARCHAR(500),
    authentication JSONB, -- encrypted credentials
    capabilities JSONB DEFAULT '[]'::jsonb,
    last_sync TIMESTAMPTZ,
    sync_frequency_minutes INTEGER DEFAULT 5,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(service)
);

-- 5. Task Execution Log - Track all automated tasks
CREATE TABLE IF NOT EXISTS task_execution_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_name VARCHAR(200) NOT NULL,
    task_type VARCHAR(50), -- scheduled, triggered, manual
    priority INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    input_params JSONB DEFAULT '{}',
    output_result JSONB DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    parent_task_id UUID REFERENCES task_execution_log(id),
    created_by VARCHAR(100),
    metadata JSONB DEFAULT '{}'
);

-- 6. Decision History - AI and system decisions
CREATE TABLE IF NOT EXISTS decision_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_type VARCHAR(100) NOT NULL,
    decision_context JSONB NOT NULL,
    options_evaluated JSONB DEFAULT '[]'::jsonb,
    decision_made JSONB NOT NULL,
    confidence_score DECIMAL(5,4),
    reasoning TEXT,
    outcome VARCHAR(50),
    impact_assessment JSONB DEFAULT '{}',
    decision_maker VARCHAR(100), -- ai-agent, system, human
    created_at TIMESTAMPTZ DEFAULT NOW(),
    feedback JSONB DEFAULT '{}',
    learned_patterns JSONB DEFAULT '{}'
);

-- 7. Continuous Learning Table - Store learned patterns
CREATE TABLE IF NOT EXISTS operational_learning (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type VARCHAR(100) NOT NULL,
    pattern_description TEXT,
    trigger_conditions JSONB NOT NULL,
    recommended_action JSONB NOT NULL,
    success_rate DECIMAL(5,2),
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tags TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- 8. Critical Paths - Never forget critical workflows
CREATE TABLE IF NOT EXISTS critical_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    path_name VARCHAR(200) NOT NULL,
    path_type VARCHAR(50), -- deployment, recovery, scaling, maintenance
    steps JSONB NOT NULL, -- ordered array of steps
    dependencies JSONB DEFAULT '[]'::jsonb,
    estimated_duration_minutes INTEGER,
    last_execution TIMESTAMPTZ,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    average_duration_minutes DECIMAL(10,2),
    rollback_procedure JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(path_name)
);

-- 9. Environment Registry - Track all environments and their configs
CREATE TABLE IF NOT EXISTS environment_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    environment VARCHAR(50) NOT NULL,
    service VARCHAR(100) NOT NULL,
    configuration JSONB NOT NULL, -- env vars, secrets (encrypted)
    health_check_url VARCHAR(500),
    deployment_url VARCHAR(500),
    monitoring_urls JSONB DEFAULT '[]'::jsonb,
    dependencies JSONB DEFAULT '[]'::jsonb,
    sla_requirements JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(environment, service)
);

-- 10. Automation Workflows - Track all automation states
CREATE TABLE IF NOT EXISTS automation_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name VARCHAR(200) NOT NULL,
    workflow_type VARCHAR(50),
    trigger_conditions JSONB NOT NULL,
    workflow_definition JSONB NOT NULL, -- LangGraph, Make.com, etc
    current_state VARCHAR(100),
    execution_count INTEGER DEFAULT 0,
    last_execution TIMESTAMPTZ,
    next_scheduled_run TIMESTAMPTZ,
    performance_metrics JSONB DEFAULT '{}',
    error_recovery_strategy JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(workflow_name)
);

-- Create indexes for performance
CREATE INDEX idx_blueprint_section ON operational_blueprint(section, subsection);
CREATE INDEX idx_blueprint_status ON operational_blueprint(status, implementation_status);
CREATE INDEX idx_blueprint_priority ON operational_blueprint(priority DESC);
CREATE INDEX idx_blueprint_tags ON operational_blueprint USING GIN(tags);

CREATE INDEX idx_status_component ON operational_status(component, status);
CREATE INDEX idx_status_health ON operational_status(health_score);
CREATE INDEX idx_status_intervention ON operational_status(human_intervention_required);

CREATE INDEX idx_deployment_service ON deployment_registry(service, environment);
CREATE INDEX idx_deployment_status ON deployment_registry(status);
CREATE INDEX idx_deployment_time ON deployment_registry(started_at DESC);

CREATE INDEX idx_task_status ON task_execution_log(status, task_type);
CREATE INDEX idx_task_time ON task_execution_log(started_at DESC);
CREATE INDEX idx_task_parent ON task_execution_log(parent_task_id);

CREATE INDEX idx_decision_type ON decision_history(decision_type);
CREATE INDEX idx_decision_time ON decision_history(created_at DESC);
CREATE INDEX idx_decision_maker ON decision_history(decision_maker);

CREATE INDEX idx_learning_pattern ON operational_learning(pattern_type);
CREATE INDEX idx_learning_usage ON operational_learning(usage_count DESC);
CREATE INDEX idx_learning_tags ON operational_learning USING GIN(tags);

CREATE INDEX idx_critical_path ON critical_paths(path_type);
CREATE INDEX idx_critical_execution ON critical_paths(last_execution DESC);

CREATE INDEX idx_environment ON environment_registry(environment, service);

CREATE INDEX idx_workflow_active ON automation_workflows(is_active, workflow_type);
CREATE INDEX idx_workflow_next_run ON automation_workflows(next_scheduled_run);

-- Create update trigger for timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to all tables
CREATE TRIGGER update_operational_blueprint_updated_at BEFORE UPDATE ON operational_blueprint 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_operational_status_updated_at BEFORE UPDATE ON operational_status 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deployment_registry_updated_at BEFORE UPDATE ON deployment_registry 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mcp_integrations_updated_at BEFORE UPDATE ON mcp_integrations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_operational_learning_updated_at BEFORE UPDATE ON operational_learning 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_critical_paths_updated_at BEFORE UPDATE ON critical_paths 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_environment_registry_updated_at BEFORE UPDATE ON environment_registry 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_automation_workflows_updated_at BEFORE UPDATE ON automation_workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Initial system message
INSERT INTO operational_blueprint (version, section, subsection, content, priority, status)
VALUES (
    '1.0.0',
    'system',
    'initialization',
    '{
        "message": "Operational Context System Initialized",
        "purpose": "Never lose track of anything ever again",
        "capabilities": [
            "Blueprint management",
            "Real-time status tracking",
            "Deployment registry",
            "MCP integration tracking",
            "Task execution logging",
            "Decision history",
            "Continuous learning",
            "Critical path management",
            "Environment configuration",
            "Automation workflow tracking"
        ],
        "timestamp": "2025-08-19T11:30:00Z"
    }'::jsonb,
    3,
    'active'
)
ON CONFLICT (version, section, subsection) DO NOTHING;

-- Success message
SELECT 'Operational Context Tables Created Successfully! 🎯' as status;