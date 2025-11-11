-- BrainOps Production Database Schema
-- Idempotent migrations for Supabase with pgvector

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS brainops;

-- Set search path
SET search_path TO brainops, public;

-- ============================================
-- CORE TABLES
-- ============================================

-- Persistent Memory with Vector Embeddings
CREATE TABLE IF NOT EXISTS brainops.memory_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    importance FLOAT NOT NULL DEFAULT 0.5 CHECK (importance >= 0 AND importance <= 1),
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    meta JSONB DEFAULT '{}',
    embedding vector(384),
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ DEFAULT NOW(),
    context_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for memory_entries
CREATE INDEX IF NOT EXISTS idx_memory_ts ON brainops.memory_entries(ts DESC);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON brainops.memory_entries(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memory_context ON brainops.memory_entries(context_id);
CREATE INDEX IF NOT EXISTS idx_memory_meta ON brainops.memory_entries USING gin(meta);
CREATE INDEX IF NOT EXISTS idx_memory_embedding ON brainops.memory_entries 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- System Knowledge Base
CREATE TABLE IF NOT EXISTS brainops.knowledge (
    category TEXT NOT NULL,
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    source TEXT DEFAULT 'system',
    verified BOOLEAN DEFAULT FALSE,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (category, key)
);

-- Indexes for knowledge
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON brainops.knowledge(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_ts ON brainops.knowledge(ts DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_value ON brainops.knowledge USING gin(value);

-- Decision History
CREATE TABLE IF NOT EXISTS brainops.decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decision_type TEXT NOT NULL,
    context JSONB NOT NULL,
    decision_made JSONB NOT NULL,
    outcome JSONB,
    score FLOAT CHECK (score >= 0 AND score <= 1),
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for decisions
CREATE INDEX IF NOT EXISTS idx_decisions_ts ON brainops.decisions(ts DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_type ON brainops.decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_decisions_score ON brainops.decisions(score DESC) WHERE score IS NOT NULL;

-- Run Logs
CREATE TABLE IF NOT EXISTS brainops.run_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    component TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    meta JSONB DEFAULT '{}',
    trace_id VARCHAR(64),
    span_id VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for run_logs
CREATE INDEX IF NOT EXISTS idx_logs_ts ON brainops.run_logs(ts DESC);
CREATE INDEX IF NOT EXISTS idx_logs_component ON brainops.run_logs(component);
CREATE INDEX IF NOT EXISTS idx_logs_level ON brainops.run_logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_trace ON brainops.run_logs(trace_id);

-- ============================================
-- OPERATIONAL TABLES
-- ============================================

-- Health Metrics
CREATE TABLE IF NOT EXISTS brainops.health_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('healthy', 'degraded', 'critical', 'unknown')),
    response_time_ms INTEGER,
    error_rate FLOAT,
    cpu_percent FLOAT,
    memory_percent FLOAT,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for health_metrics
CREATE INDEX IF NOT EXISTS idx_health_ts ON brainops.health_metrics(ts DESC);
CREATE INDEX IF NOT EXISTS idx_health_service ON brainops.health_metrics(service, ts DESC);
CREATE INDEX IF NOT EXISTS idx_health_status ON brainops.health_metrics(status) WHERE status != 'healthy';

-- Deployment History
CREATE TABLE IF NOT EXISTS brainops.deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    platform TEXT NOT NULL CHECK (platform IN ('vercel', 'render', 'github')),
    project TEXT NOT NULL,
    deployment_id TEXT NOT NULL,
    commit_sha VARCHAR(40),
    branch TEXT,
    status TEXT NOT NULL,
    smoke_test_passed BOOLEAN,
    rollback_of UUID REFERENCES brainops.deployments(id),
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for deployments
CREATE INDEX IF NOT EXISTS idx_deploy_ts ON brainops.deployments(ts DESC);
CREATE INDEX IF NOT EXISTS idx_deploy_platform ON brainops.deployments(platform, project);
CREATE INDEX IF NOT EXISTS idx_deploy_status ON brainops.deployments(status);

-- Incident Reports
CREATE TABLE IF NOT EXISTS brainops.incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    incident_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    description TEXT NOT NULL,
    affected_services TEXT[],
    remediation_actions JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    github_issue_url TEXT,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for incidents
CREATE INDEX IF NOT EXISTS idx_incident_ts ON brainops.incidents(ts DESC);
CREATE INDEX IF NOT EXISTS idx_incident_type ON brainops.incidents(incident_type);
CREATE INDEX IF NOT EXISTS idx_incident_severity ON brainops.incidents(severity);
CREATE INDEX IF NOT EXISTS idx_incident_resolved ON brainops.incidents(resolved);

-- ============================================
-- REVENUE TABLES
-- ============================================

-- Revenue Events
CREATE TABLE IF NOT EXISTS brainops.revenue_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type TEXT NOT NULL,
    amount DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    customer_id TEXT,
    product_id TEXT,
    ai_generated BOOLEAN DEFAULT FALSE,
    conversion_source TEXT,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for revenue_events
CREATE INDEX IF NOT EXISTS idx_revenue_ts ON brainops.revenue_events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_revenue_type ON brainops.revenue_events(event_type);
CREATE INDEX IF NOT EXISTS idx_revenue_customer ON brainops.revenue_events(customer_id);
CREATE INDEX IF NOT EXISTS idx_revenue_ai ON brainops.revenue_events(ai_generated) WHERE ai_generated = true;

-- Revenue Patterns
CREATE TABLE IF NOT EXISTS brainops.revenue_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type TEXT NOT NULL,
    conditions JSONB NOT NULL,
    action_taken JSONB NOT NULL,
    revenue_impact DECIMAL(10, 2),
    conversion_impact FLOAT,
    confidence FLOAT DEFAULT 0.5 CHECK (confidence >= 0 AND confidence <= 1),
    applications INTEGER DEFAULT 0,
    successful_applications INTEGER DEFAULT 0,
    last_applied TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for revenue_patterns
CREATE INDEX IF NOT EXISTS idx_pattern_type ON brainops.revenue_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_pattern_confidence ON brainops.revenue_patterns(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_pattern_impact ON brainops.revenue_patterns(revenue_impact DESC);

-- ============================================
-- WEBHOOK TABLES
-- ============================================

-- Webhook Events
CREATE TABLE IF NOT EXISTS brainops.webhook_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for webhook_events
CREATE INDEX IF NOT EXISTS idx_webhook_ts ON brainops.webhook_events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_source ON brainops.webhook_events(source);
CREATE INDEX IF NOT EXISTS idx_webhook_processed ON brainops.webhook_events(processed) WHERE processed = false;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION brainops.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create update triggers
DO $$
BEGIN
    -- Memory entries
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_memory_entries_updated_at') THEN
        CREATE TRIGGER update_memory_entries_updated_at
            BEFORE UPDATE ON brainops.memory_entries
            FOR EACH ROW EXECUTE FUNCTION brainops.update_updated_at();
    END IF;
    
    -- Knowledge
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_knowledge_updated_at') THEN
        CREATE TRIGGER update_knowledge_updated_at
            BEFORE UPDATE ON brainops.knowledge
            FOR EACH ROW EXECUTE FUNCTION brainops.update_updated_at();
    END IF;
    
    -- Revenue patterns
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_revenue_patterns_updated_at') THEN
        CREATE TRIGGER update_revenue_patterns_updated_at
            BEFORE UPDATE ON brainops.revenue_patterns
            FOR EACH ROW EXECUTE FUNCTION brainops.update_updated_at();
    END IF;
END $$;

-- Cleanup old logs function
CREATE OR REPLACE FUNCTION brainops.cleanup_old_logs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM brainops.run_logs
    WHERE ts < NOW() - INTERVAL '1 day' * days_to_keep
    AND level IN ('DEBUG', 'INFO');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Memory consolidation function
CREATE OR REPLACE FUNCTION brainops.consolidate_memories()
RETURNS TABLE(consolidated INTEGER, removed INTEGER) AS $$
DECLARE
    consolidated_count INTEGER := 0;
    removed_count INTEGER := 0;
BEGIN
    -- Remove low-importance, rarely accessed memories
    DELETE FROM brainops.memory_entries
    WHERE importance < 0.3 
    AND access_count < 2
    AND created_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS removed_count = ROW_COUNT;
    
    -- Boost importance of frequently accessed memories
    UPDATE brainops.memory_entries
    SET importance = LEAST(importance * 1.1, 1.0)
    WHERE access_count > 10;
    
    GET DIAGNOSTICS consolidated_count = ROW_COUNT;
    
    RETURN QUERY SELECT consolidated_count, removed_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

-- Enable RLS on sensitive tables
ALTER TABLE brainops.memory_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE brainops.knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE brainops.revenue_events ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth setup)
-- Service role has full access
CREATE POLICY service_full_access ON brainops.memory_entries
    FOR ALL USING (true);

CREATE POLICY service_knowledge_access ON brainops.knowledge
    FOR ALL USING (true);

CREATE POLICY service_revenue_access ON brainops.revenue_events
    FOR ALL USING (true);

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert initial knowledge
INSERT INTO brainops.knowledge (category, key, value, confidence, source)
VALUES 
    ('system', 'version', '"1.0.0"'::jsonb, 1.0, 'initial'),
    ('system', 'deployment_date', to_jsonb(NOW()), 1.0, 'initial'),
    ('config', 'error_threshold', '0.05'::jsonb, 1.0, 'initial'),
    ('config', 'latency_threshold_ms', '1000'::jsonb, 1.0, 'initial'),
    ('config', 'min_confidence', '0.3'::jsonb, 1.0, 'initial')
ON CONFLICT (category, key) DO NOTHING;

-- ============================================
-- GRANTS (adjust for your users)
-- ============================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA brainops TO postgres, anon, authenticated, service_role;

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA brainops TO service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA brainops TO anon, authenticated;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA brainops TO service_role;

-- Grant function permissions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA brainops TO service_role;