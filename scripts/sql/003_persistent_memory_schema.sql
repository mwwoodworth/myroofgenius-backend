-- BrainOps AI OS Persistent Memory Database Schema
-- Version: 1.0.0
-- Created: 2025-01-17
-- Complete schema for all operational data persistence

-- Core Environment Registry
CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE IF NOT EXISTS core.env_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL,
    value TEXT,
    encrypted_value BYTEA,
    scope VARCHAR(50) NOT NULL DEFAULT 'global' 
        CHECK (scope IN ('global', 'service', 'env', 'local')),
    environment VARCHAR(50) DEFAULT 'all'
        CHECK (environment IN ('all', 'dev', 'staging', 'prod', 'test')),
    service_name VARCHAR(100),
    description TEXT,
    data_type VARCHAR(50) DEFAULT 'string'
        CHECK (data_type IN ('string', 'number', 'boolean', 'json', 'url', 'secret')),
    required BOOLEAN NOT NULL DEFAULT false,
    default_value TEXT,
    validation_regex TEXT,
    last_verified_at TIMESTAMPTZ,
    last_verified_by VARCHAR(100),
    source_ref TEXT,
    git_ref VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deprecated_at TIMESTAMPTZ,
    CONSTRAINT env_key_scope_unique UNIQUE (key, scope, environment, service_name),
    CONSTRAINT value_or_encrypted CHECK (
        (value IS NOT NULL AND encrypted_value IS NULL) OR
        (value IS NULL AND encrypted_value IS NOT NULL)
    )
);

-- Operations Logging
CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS ops.run_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id VARCHAR(255) NOT NULL,
    component VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    environment VARCHAR(50) NOT NULL,
    input_ref TEXT,
    input_hash VARCHAR(64),
    output_ref TEXT,
    output_hash VARCHAR(64),
    status VARCHAR(50) NOT NULL 
        CHECK (status IN ('started', 'running', 'completed', 'failed', 'timeout', 'cancelled')),
    status_message TEXT,
    latency_ms INTEGER,
    cpu_ms INTEGER,
    memory_mb INTEGER,
    cost_usd DECIMAL(10,6),
    error_type VARCHAR(100),
    error_message TEXT,
    error_stack TEXT,
    retry_count INTEGER DEFAULT 0,
    parent_run_id VARCHAR(255),
    correlation_id VARCHAR(255),
    trace_id VARCHAR(255),
    span_id VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT run_id_unique UNIQUE (run_id, component)
);

CREATE TABLE IF NOT EXISTS ops.decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id VARCHAR(255) UNIQUE NOT NULL,
    who VARCHAR(100) NOT NULL,
    what TEXT NOT NULL,
    why TEXT NOT NULL,
    decision_type VARCHAR(50) NOT NULL
        CHECK (decision_type IN ('technical', 'business', 'operational', 'security', 'financial')),
    options JSONB NOT NULL DEFAULT '[]'::jsonb,
    selected JSONB NOT NULL,
    impact_assessment TEXT,
    risk_level VARCHAR(20) 
        CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    approval_required BOOLEAN DEFAULT false,
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    sop_ref TEXT,
    evidence_refs TEXT[],
    outcome TEXT,
    outcome_measured_at TIMESTAMPTZ,
    reversed_by UUID REFERENCES ops.decisions(id),
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Memory System
CREATE SCHEMA IF NOT EXISTS memory;

CREATE TABLE IF NOT EXISTS memory.agent_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL
        CHECK (agent_type IN ('claude', 'chatgpt', 'gemini', 'perplexity', 'notebook_lm', 'aurea', 'custom')),
    scope VARCHAR(50) NOT NULL DEFAULT 'session'
        CHECK (scope IN ('global', 'project', 'session', 'conversation')),
    memory_type VARCHAR(50) NOT NULL DEFAULT 'fact'
        CHECK (memory_type IN ('fact', 'procedure', 'decision', 'insight', 'error', 'success')),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding VECTOR(1536),
    importance_score DECIMAL(3,2) CHECK (importance_score BETWEEN 0 AND 1),
    access_count INTEGER DEFAULT 0,
    tags TEXT[],
    references JSONB DEFAULT '[]'::jsonb,
    context JSONB DEFAULT '{}'::jsonb,
    parent_memory_id UUID REFERENCES memory.agent_memories(id),
    supersedes_id UUID REFERENCES memory.agent_memories(id),
    last_accessed_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT unique_agent_content UNIQUE (agent_id, scope, content_hash)
);

CREATE TABLE IF NOT EXISTS memory.memory_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id UUID NOT NULL REFERENCES memory.agent_memories(id) ON DELETE CASCADE,
    used_by_agent VARCHAR(100) NOT NULL,
    used_in_context TEXT,
    usage_type VARCHAR(50) 
        CHECK (usage_type IN ('retrieve', 'reference', 'modify', 'invalidate')),
    effectiveness_score DECIMAL(3,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Documentation & SOPs
CREATE SCHEMA IF NOT EXISTS docs;

CREATE TABLE IF NOT EXISTS docs.sops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sop_id VARCHAR(100) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    area VARCHAR(100) NOT NULL,
    md_body TEXT NOT NULL,
    html_body TEXT,
    search_vector tsvector,
    tags TEXT[],
    owner VARCHAR(100) NOT NULL DEFAULT 'system',
    review_required_by TIMESTAMPTZ,
    last_reviewed_at TIMESTAMPTZ,
    last_reviewed_by VARCHAR(100),
    automation_level VARCHAR(50) DEFAULT 'manual'
        CHECK (automation_level IN ('manual', 'assisted', 'automated', 'autonomous')),
    automation_script TEXT,
    test_coverage DECIMAL(5,2),
    compliance_frameworks TEXT[],
    effective_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    supersedes_id UUID REFERENCES docs.sops(id),
    created_by VARCHAR(100) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT sop_version_unique UNIQUE (sop_id, version)
);

CREATE TABLE IF NOT EXISTS docs.sop_revisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sop_id UUID NOT NULL REFERENCES docs.sops(id) ON DELETE CASCADE,
    revision_type VARCHAR(50) NOT NULL
        CHECK (revision_type IN ('create', 'update', 'review', 'approve', 'deprecate')),
    changed_by VARCHAR(100) NOT NULL,
    change_summary TEXT NOT NULL,
    diff_content TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Data Pipeline Tables
CREATE SCHEMA IF NOT EXISTS data;

CREATE TABLE IF NOT EXISTS data.centerpoint_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL
        CHECK (source_type IN ('api', 'database', 'file', 'stream', 'webhook')),
    connection_string TEXT,
    credentials_ref VARCHAR(255),
    schema_definition JSONB,
    sync_frequency_minutes INTEGER,
    last_sync_at TIMESTAMPTZ,
    next_sync_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data.centerpoint_ingestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES data.centerpoint_sources(id),
    ingestion_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'partial')),
    total_records INTEGER,
    processed_records INTEGER,
    failed_records INTEGER,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    error_log TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data.centerpoint_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_table VARCHAR(100) NOT NULL,
    source_column VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    target_column VARCHAR(100) NOT NULL,
    transform_function TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT mapping_unique UNIQUE (source_table, source_column, target_table, target_column)
);

CREATE TABLE IF NOT EXISTS data.centerpoint_reconciliations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reconciliation_date DATE NOT NULL,
    source_system VARCHAR(100) NOT NULL,
    target_system VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    source_count INTEGER NOT NULL,
    target_count INTEGER NOT NULL,
    matched_count INTEGER NOT NULL,
    unmatched_source INTEGER NOT NULL,
    unmatched_target INTEGER NOT NULL,
    discrepancies JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL
        CHECK (status IN ('balanced', 'imbalanced', 'investigating', 'resolved')),
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT reconciliation_unique UNIQUE (reconciliation_date, source_system, target_system, entity_type)
);

CREATE TABLE IF NOT EXISTS data.centerpoint_lineage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    source_system VARCHAR(100) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    transform_applied TEXT,
    ingestion_id UUID REFERENCES data.centerpoint_ingestions(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT lineage_unique UNIQUE (entity_type, entity_id, source_system, source_id)
);

-- Email System
CREATE SCHEMA IF NOT EXISTS email;

CREATE TABLE IF NOT EXISTS email.sendgrid_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL
        CHECK (event_type IN ('processed', 'dropped', 'delivered', 'deferred', 'bounce', 'open', 'click', 'spam_report', 'unsubscribe', 'group_unsubscribe', 'group_resubscribe')),
    message_id VARCHAR(255) NOT NULL,
    template_id VARCHAR(100),
    recipient_email VARCHAR(255) NOT NULL,
    sender_email VARCHAR(255),
    subject TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    smtp_id VARCHAR(255),
    sg_event_id VARCHAR(255),
    sg_message_id VARCHAR(255),
    category TEXT[],
    unique_args JSONB,
    marketing_campaign_id VARCHAR(100),
    marketing_campaign_name VARCHAR(255),
    payload_json JSONB NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Revenue System
CREATE SCHEMA IF NOT EXISTS revenue;

CREATE TABLE IF NOT EXISTS revenue.payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL
        CHECK (provider IN ('stripe', 'gumroad', 'paypal', 'manual')),
    ext_id VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(255) UNIQUE,
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(50) NOT NULL
        CHECK (status IN ('pending', 'processing', 'succeeded', 'failed', 'cancelled', 'refunded', 'partial_refund')),
    payment_method VARCHAR(50),
    customer_ref VARCHAR(255),
    customer_email VARCHAR(255),
    product_ref VARCHAR(255),
    product_name VARCHAR(255),
    quantity INTEGER DEFAULT 1,
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    fee_cents INTEGER,
    net_cents INTEGER,
    tax_cents INTEGER,
    refunded_cents INTEGER DEFAULT 0,
    dispute_status VARCHAR(50),
    evidence_ref TEXT,
    receipt_url TEXT,
    invoice_id VARCHAR(255),
    subscription_id VARCHAR(255),
    failure_code VARCHAR(100),
    failure_message TEXT,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT payment_unique UNIQUE (provider, ext_id)
);

CREATE TABLE IF NOT EXISTS revenue.webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    signature VARCHAR(500),
    verified BOOLEAN DEFAULT false,
    processed BOOLEAN DEFAULT false,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX idx_env_registry_key ON core.env_registry(key);
CREATE INDEX idx_env_registry_scope ON core.env_registry(scope, environment);
CREATE INDEX idx_run_logs_run_id ON ops.run_logs(run_id);
CREATE INDEX idx_run_logs_component ON ops.run_logs(component, status);
CREATE INDEX idx_run_logs_started ON ops.run_logs(started_at DESC);
CREATE INDEX idx_decisions_type ON ops.decisions(decision_type, created_at DESC);
CREATE INDEX idx_agent_memories_agent ON memory.agent_memories(agent_id, scope);
CREATE INDEX idx_agent_memories_tags ON memory.agent_memories USING GIN(tags);
CREATE INDEX idx_agent_memories_embedding ON memory.agent_memories USING ivfflat(embedding);
CREATE INDEX idx_sops_search ON docs.sops USING GIN(search_vector);
CREATE INDEX idx_sops_tags ON docs.sops USING GIN(tags);
CREATE INDEX idx_sendgrid_events_message ON email.sendgrid_events(message_id);
CREATE INDEX idx_sendgrid_events_recipient ON email.sendgrid_events(recipient_email);
CREATE INDEX idx_payments_customer ON revenue.payments(customer_ref);
CREATE INDEX idx_payments_status ON revenue.payments(status, created_at DESC);

-- Update search vectors trigger for SOPs
CREATE OR REPLACE FUNCTION docs.update_sop_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.title, '') || ' ' || 
        COALESCE(NEW.category, '') || ' ' || 
        COALESCE(NEW.area, '') || ' ' || 
        COALESCE(NEW.md_body, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sop_search_vector
    BEFORE INSERT OR UPDATE ON docs.sops
    FOR EACH ROW
    EXECUTE FUNCTION docs.update_sop_search_vector();

-- RLS Policies
ALTER TABLE core.env_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops.run_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ops.decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory.agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE docs.sops ENABLE ROW LEVEL SECURITY;
ALTER TABLE revenue.payments ENABLE ROW LEVEL SECURITY;

-- Grants
GRANT USAGE ON SCHEMA core, ops, memory, docs, data, email, revenue TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA core, ops, memory, docs, data, email, revenue TO authenticated;

-- Create monitoring views
CREATE OR REPLACE VIEW ops.system_health AS
SELECT 
    component,
    COUNT(*) FILTER (WHERE status = 'completed') as successful,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    AVG(latency_ms) FILTER (WHERE status = 'completed') as avg_latency_ms,
    MAX(started_at) as last_run
FROM ops.run_logs
WHERE started_at > NOW() - INTERVAL '24 hours'
GROUP BY component;

CREATE OR REPLACE VIEW revenue.daily_revenue AS
SELECT 
    DATE(created_at) as date,
    provider,
    COUNT(*) as transaction_count,
    SUM(amount_cents) / 100.0 as gross_revenue,
    SUM(net_cents) / 100.0 as net_revenue,
    SUM(refunded_cents) / 100.0 as refunds
FROM revenue.payments
WHERE status = 'succeeded'
GROUP BY DATE(created_at), provider
ORDER BY date DESC;

-- Verification
DO $$
BEGIN
    RAISE NOTICE 'Persistent Memory Schema created successfully';
    RAISE NOTICE 'Schemas: core, ops, memory, docs, data, email, revenue';
    RAISE NOTICE 'Ready for data persistence across all systems';
END $$;