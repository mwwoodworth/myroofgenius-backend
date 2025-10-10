-- MASTER PERSISTENT MEMORY SYSTEM FOR PRODUCTION
-- This creates a comprehensive memory system that stores EVERYTHING
-- No more context loss, no more forgotten procedures, no more guessing

-- Drop existing tables if we need a clean slate (comment out in production)
-- DROP TABLE IF EXISTS persistent_memory CASCADE;
-- DROP TABLE IF EXISTS system_sops CASCADE;
-- DROP TABLE IF EXISTS system_architecture CASCADE;
-- DROP TABLE IF EXISTS system_configurations CASCADE;
-- DROP TABLE IF EXISTS deployment_history CASCADE;
-- DROP TABLE IF EXISTS decision_log CASCADE;
-- DROP TABLE IF EXISTS error_patterns CASCADE;

-- 1. MASTER PERSISTENT MEMORY TABLE
CREATE TABLE IF NOT EXISTS persistent_memory (
    id SERIAL PRIMARY KEY,
    memory_key TEXT UNIQUE NOT NULL,
    memory_value JSONB NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    importance INTEGER DEFAULT 5 CHECK (importance BETWEEN 1 AND 10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    tags TEXT[],
    dependencies TEXT[],
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1
);

-- 2. STANDARD OPERATING PROCEDURES (SOPs)
CREATE TABLE IF NOT EXISTS system_sops (
    id SERIAL PRIMARY KEY,
    sop_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL, -- deployment, testing, debugging, revenue, etc.
    steps JSONB NOT NULL, -- Detailed step-by-step procedures
    prerequisites JSONB DEFAULT '[]',
    tools_required TEXT[],
    expected_outcomes JSONB,
    error_handling JSONB,
    rollback_procedures JSONB,
    success_criteria JSONB,
    automation_possible BOOLEAN DEFAULT false,
    automation_script TEXT,
    last_executed TIMESTAMP WITH TIME ZONE,
    execution_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    average_duration_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by TEXT DEFAULT 'claude',
    approved_by TEXT,
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    tags TEXT[],
    related_sops TEXT[]
);

-- 3. SYSTEM ARCHITECTURE DOCUMENTATION
CREATE TABLE IF NOT EXISTS system_architecture (
    id SERIAL PRIMARY KEY,
    component_id TEXT UNIQUE NOT NULL,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL, -- frontend, backend, database, api, service, etc.
    description TEXT NOT NULL,
    technology_stack JSONB NOT NULL,
    dependencies JSONB DEFAULT '[]',
    configuration JSONB NOT NULL, -- All settings, env vars, etc.
    endpoints JSONB DEFAULT '[]', -- API endpoints if applicable
    database_schema JSONB, -- Tables, columns, relationships
    file_structure JSONB, -- Directory structure and key files
    deployment_info JSONB NOT NULL, -- Where/how it's deployed
    monitoring_info JSONB, -- How to monitor health
    logging_info JSONB, -- Where logs are stored
    security_info JSONB, -- Auth, permissions, etc.
    performance_metrics JSONB, -- Expected performance
    scaling_info JSONB, -- How to scale
    backup_info JSONB, -- Backup procedures
    disaster_recovery JSONB, -- DR procedures
    documentation_urls TEXT[],
    repository_url TEXT,
    live_url TEXT,
    staging_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_verified TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    health_status TEXT DEFAULT 'unknown',
    health_percentage DECIMAL(5,2),
    version TEXT,
    tags TEXT[]
);

-- 4. SYSTEM CONFIGURATIONS (Every setting, everywhere)
CREATE TABLE IF NOT EXISTS system_configurations (
    id SERIAL PRIMARY KEY,
    config_key TEXT UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    component TEXT NOT NULL,
    environment TEXT NOT NULL, -- development, staging, production
    category TEXT NOT NULL, -- ui, api, database, security, etc.
    subcategory TEXT,
    description TEXT,
    data_type TEXT, -- string, number, boolean, object, array
    possible_values JSONB, -- For enums or constrained values
    default_value JSONB,
    is_secret BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT true,
    validation_rules JSONB,
    dependencies TEXT[], -- Other configs this depends on
    affects TEXT[], -- What this config affects
    change_requires_restart BOOLEAN DEFAULT false,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    modified_by TEXT,
    change_history JSONB DEFAULT '[]',
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    tags TEXT[]
);

-- 5. DEPLOYMENT HISTORY (Every deployment, what worked, what didn't)
CREATE TABLE IF NOT EXISTS deployment_history (
    id SERIAL PRIMARY KEY,
    deployment_id TEXT UNIQUE NOT NULL,
    component TEXT NOT NULL,
    version TEXT NOT NULL,
    environment TEXT NOT NULL,
    deployment_type TEXT NOT NULL, -- docker, vercel, render, manual
    deployment_status TEXT NOT NULL, -- success, failed, partial, rollback
    deployment_steps JSONB NOT NULL,
    configuration_used JSONB NOT NULL,
    errors_encountered JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',
    performance_impact JSONB,
    rollback_performed BOOLEAN DEFAULT false,
    rollback_reason TEXT,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    deployed_by TEXT NOT NULL,
    commit_hash TEXT,
    commit_message TEXT,
    pull_request_number INTEGER,
    tests_passed BOOLEAN,
    test_results JSONB,
    monitoring_data JSONB,
    post_deployment_checks JSONB,
    notes TEXT,
    tags TEXT[]
);

-- 6. DECISION LOG (Every decision made, why, and outcomes)
CREATE TABLE IF NOT EXISTS decision_log (
    id SERIAL PRIMARY KEY,
    decision_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    context JSONB NOT NULL, -- What led to this decision
    options_considered JSONB NOT NULL, -- All options that were considered
    decision_made TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    expected_outcome JSONB,
    actual_outcome JSONB,
    success BOOLEAN,
    impact_assessment JSONB,
    lessons_learned TEXT,
    would_repeat BOOLEAN,
    related_decisions TEXT[],
    affected_components TEXT[],
    decided_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    decided_by TEXT DEFAULT 'claude',
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by TEXT,
    tags TEXT[]
);

-- 7. ERROR PATTERNS (Learn from every error)
CREATE TABLE IF NOT EXISTS error_patterns (
    id SERIAL PRIMARY KEY,
    error_id TEXT UNIQUE NOT NULL,
    error_message TEXT NOT NULL,
    error_type TEXT NOT NULL,
    component TEXT NOT NULL,
    frequency INTEGER DEFAULT 1,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    root_cause TEXT,
    immediate_fix JSONB,
    permanent_fix JSONB,
    prevention_measures JSONB,
    affected_users INTEGER,
    severity TEXT, -- critical, high, medium, low
    priority INTEGER CHECK (priority BETWEEN 1 AND 10),
    resolution_time_minutes INTEGER,
    automated_fix_available BOOLEAN DEFAULT false,
    automation_script TEXT,
    related_errors TEXT[],
    tags TEXT[],
    is_resolved BOOLEAN DEFAULT false,
    resolution_notes TEXT
);

-- 8. UI/UX SPECIFICATIONS (Every color, font, spacing)
CREATE TABLE IF NOT EXISTS ui_specifications (
    id SERIAL PRIMARY KEY,
    spec_id TEXT UNIQUE NOT NULL,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL, -- button, form, modal, page, etc.
    design_system TEXT NOT NULL, -- which design system it belongs to
    colors JSONB NOT NULL, -- primary, secondary, background, text, etc.
    typography JSONB NOT NULL, -- fonts, sizes, weights, line-heights
    spacing JSONB NOT NULL, -- margins, paddings, gaps
    dimensions JSONB, -- widths, heights, breakpoints
    animations JSONB, -- transitions, durations, easings
    interactions JSONB, -- hover, focus, active states
    accessibility JSONB, -- ARIA labels, keyboard nav, etc.
    responsive_behavior JSONB, -- mobile, tablet, desktop specs
    dark_mode_overrides JSONB,
    component_code TEXT, -- actual implementation
    css_classes TEXT[],
    tailwind_classes TEXT[],
    design_tokens JSONB,
    figma_link TEXT,
    storybook_link TEXT,
    screenshot_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    tags TEXT[]
);

-- 9. API DOCUMENTATION (Every endpoint, parameter, response)
CREATE TABLE IF NOT EXISTS api_documentation (
    id SERIAL PRIMARY KEY,
    endpoint_id TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    method TEXT NOT NULL,
    component TEXT NOT NULL,
    description TEXT NOT NULL,
    authentication_required BOOLEAN DEFAULT true,
    authorization_roles TEXT[],
    request_headers JSONB,
    request_params JSONB,
    request_body JSONB,
    response_success JSONB,
    response_errors JSONB,
    rate_limiting JSONB,
    caching_policy JSONB,
    examples JSONB,
    implementation_notes TEXT,
    performance_metrics JSONB,
    dependencies TEXT[],
    related_endpoints TEXT[],
    version TEXT,
    deprecated BOOLEAN DEFAULT false,
    deprecation_notice TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    tags TEXT[]
);

-- 10. INTEGRATION MAPPINGS (How everything connects)
CREATE TABLE IF NOT EXISTS integration_mappings (
    id SERIAL PRIMARY KEY,
    mapping_id TEXT UNIQUE NOT NULL,
    source_system TEXT NOT NULL,
    target_system TEXT NOT NULL,
    integration_type TEXT NOT NULL, -- api, webhook, database, file, etc.
    data_flow_direction TEXT NOT NULL, -- unidirectional, bidirectional
    mapping_rules JSONB NOT NULL,
    transformation_logic JSONB,
    validation_rules JSONB,
    error_handling JSONB,
    retry_policy JSONB,
    monitoring_config JSONB,
    performance_sla JSONB,
    dependencies TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    last_sync TIMESTAMP WITH TIME ZONE,
    sync_frequency TEXT,
    tags TEXT[]
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_persistent_memory_key ON persistent_memory(memory_key);
CREATE INDEX IF NOT EXISTS idx_persistent_memory_category ON persistent_memory(category);
CREATE INDEX IF NOT EXISTS idx_persistent_memory_tags ON persistent_memory USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_persistent_memory_active ON persistent_memory(is_active);
CREATE INDEX IF NOT EXISTS idx_persistent_memory_importance ON persistent_memory(importance DESC);

CREATE INDEX IF NOT EXISTS idx_sops_category ON system_sops(category);
CREATE INDEX IF NOT EXISTS idx_sops_active ON system_sops(is_active);
CREATE INDEX IF NOT EXISTS idx_sops_tags ON system_sops USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_architecture_component ON system_architecture(component_id);
CREATE INDEX IF NOT EXISTS idx_architecture_type ON system_architecture(component_type);
CREATE INDEX IF NOT EXISTS idx_architecture_health ON system_architecture(health_status);

CREATE INDEX IF NOT EXISTS idx_config_key ON system_configurations(config_key);
CREATE INDEX IF NOT EXISTS idx_config_component ON system_configurations(component);
CREATE INDEX IF NOT EXISTS idx_config_env ON system_configurations(environment);

CREATE INDEX IF NOT EXISTS idx_deployment_component ON deployment_history(component);
CREATE INDEX IF NOT EXISTS idx_deployment_status ON deployment_history(deployment_status);
CREATE INDEX IF NOT EXISTS idx_deployment_date ON deployment_history(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_decision_category ON decision_log(category);
CREATE INDEX IF NOT EXISTS idx_decision_date ON decision_log(decided_at DESC);

CREATE INDEX IF NOT EXISTS idx_error_component ON error_patterns(component);
CREATE INDEX IF NOT EXISTS idx_error_severity ON error_patterns(severity);
CREATE INDEX IF NOT EXISTS idx_error_resolved ON error_patterns(is_resolved);

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_persistent_memory_updated_at BEFORE UPDATE ON persistent_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_sops_updated_at BEFORE UPDATE ON system_sops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_architecture_updated_at BEFORE UPDATE ON system_architecture
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ui_specifications_updated_at BEFORE UPDATE ON ui_specifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_documentation_updated_at BEFORE UPDATE ON api_documentation
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for active memories
CREATE OR REPLACE VIEW active_memories AS
SELECT 
    memory_key,
    memory_value,
    category,
    importance,
    last_accessed,
    access_count
FROM persistent_memory
WHERE is_active = true
    AND (expires_at IS NULL OR expires_at > NOW())
ORDER BY importance DESC, last_accessed DESC;

-- Create view for current system health
CREATE OR REPLACE VIEW system_health AS
SELECT 
    component_name,
    component_type,
    health_status,
    health_percentage,
    last_verified,
    live_url
FROM system_architecture
WHERE is_active = true
ORDER BY health_percentage ASC NULLS FIRST;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres;

-- Initial success message
DO $$
BEGIN
    RAISE NOTICE 'Master Persistent Memory System created successfully!';
    RAISE NOTICE 'Tables created: persistent_memory, system_sops, system_architecture, system_configurations, deployment_history, decision_log, error_patterns, ui_specifications, api_documentation, integration_mappings';
    RAISE NOTICE 'Ready to store comprehensive system knowledge';
END $$;