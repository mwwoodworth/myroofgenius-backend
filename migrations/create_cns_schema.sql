-- BrainOps Central Nervous System (CNS) Database Schema
-- The persistent memory hub for all operations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- CORE MEMORY LAYER
-- =====================================================

-- Master memory table for all system knowledge
CREATE TABLE IF NOT EXISTS system_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type VARCHAR(50) NOT NULL, -- context, task, decision, learning, insight, warning
    category VARCHAR(100),
    title TEXT,
    content JSONB NOT NULL,
    embeddings VECTOR(1536), -- For AI semantic search
    importance_score DECIMAL DEFAULT 0.5,
    confidence_score DECIMAL DEFAULT 1.0,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP, -- NULL means permanent
    tags TEXT[],
    linked_memories UUID[],
    source_system VARCHAR(100), -- claude_code, github, backend, frontend, etc.
    created_by VARCHAR(100),
    metadata JSONB
);

-- Task management with full history
CREATE TABLE IF NOT EXISTS task_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID UNIQUE,
    project_id UUID,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, blocked, completed, cancelled
    priority INTEGER DEFAULT 5, -- 1-10 scale
    urgency INTEGER DEFAULT 5,
    impact INTEGER DEFAULT 5,
    assignee_id UUID,
    parent_task_id UUID,
    subtasks UUID[],
    dependencies UUID[],
    blockers JSONB[],
    context JSONB, -- Full context when created
    ai_suggestions JSONB,
    ai_priority_reason TEXT,
    progress_history JSONB[],
    status_changes JSONB[],
    time_tracking JSONB,
    estimated_hours DECIMAL,
    actual_hours DECIMAL,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    due_date TIMESTAMP,
    tags TEXT[],
    attachments TEXT[],
    comments JSONB[]
);

-- Project tracking with complete history
CREATE TABLE IF NOT EXISTS project_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    code VARCHAR(50) UNIQUE,
    description TEXT,
    status VARCHAR(50) DEFAULT 'planning', -- planning, active, on_hold, completed, cancelled
    category VARCHAR(100),
    goals JSONB,
    success_criteria JSONB,
    milestones JSONB[],
    team_members UUID[],
    resources JSONB,
    timeline JSONB,
    budget JSONB,
    actual_cost JSONB,
    risks JSONB[],
    decisions JSONB[], -- Every decision made
    learnings JSONB[], -- What we learned
    metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    deadline TIMESTAMP
);

-- Conversation and context threads
CREATE TABLE IF NOT EXISTS context_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_type VARCHAR(50), -- conversation, development, planning, debugging
    title TEXT,
    participants TEXT[],
    messages JSONB[],
    decisions_made JSONB[],
    action_items UUID[], -- Links to tasks
    insights JSONB[],
    files TEXT[],
    code_changes JSONB[],
    summary TEXT,
    embeddings VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    tags TEXT[]
);

-- =====================================================
-- DECISION & LEARNING SYSTEM
-- =====================================================

-- Track every decision for future reference
CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_type VARCHAR(100),
    title TEXT NOT NULL,
    description TEXT,
    context JSONB,
    options_considered JSONB[],
    chosen_option JSONB,
    rationale TEXT,
    expected_outcome JSONB,
    actual_outcome JSONB,
    impact_score DECIMAL,
    success_score DECIMAL,
    lessons_learned TEXT,
    related_tasks UUID[],
    related_projects UUID[],
    created_at TIMESTAMP DEFAULT NOW(),
    evaluated_at TIMESTAMP,
    created_by VARCHAR(100)
);

-- System learning and improvements
CREATE TABLE IF NOT EXISTS system_learnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100),
    learning_type VARCHAR(50), -- pattern, mistake, success, optimization
    title TEXT,
    learning TEXT NOT NULL,
    context JSONB,
    evidence JSONB[],
    impact_score DECIMAL,
    confidence_score DECIMAL,
    applied_count INTEGER DEFAULT 0,
    last_applied TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    tags TEXT[],
    related_decisions UUID[]
);

-- =====================================================
-- AUTOMATION & RULES ENGINE
-- =====================================================

-- Automation rules for the CNS
CREATE TABLE IF NOT EXISTS automation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name TEXT NOT NULL,
    description TEXT,
    trigger_type VARCHAR(100), -- event, schedule, condition, threshold
    trigger_config JSONB,
    conditions JSONB[],
    action_type VARCHAR(100), -- create_task, notify, execute_workflow, update_status
    action_config JSONB,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 5,
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_executed TIMESTAMP,
    last_success TIMESTAMP,
    last_failure TIMESTAMP,
    error_log JSONB[],
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- =====================================================
-- SESSION & CONTINUITY
-- =====================================================

-- Claude Code session tracking
CREATE TABLE IF NOT EXISTS claude_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) UNIQUE,
    session_start TIMESTAMP DEFAULT NOW(),
    session_end TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    messages JSONB[],
    context JSONB,
    todos_created UUID[],
    tasks_completed UUID[],
    decisions_made UUID[],
    files_modified TEXT[],
    commands_executed JSONB[],
    errors_encountered JSONB[],
    insights_generated JSONB[],
    total_tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- INTEGRATION TRACKING
-- =====================================================

-- Track all external system integrations
CREATE TABLE IF NOT EXISTS integration_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_name VARCHAR(100), -- github, render, vercel, slack, etc.
    sync_type VARCHAR(50), -- pull, push, bidirectional
    last_sync TIMESTAMP,
    next_sync TIMESTAMP,
    sync_status VARCHAR(50),
    items_synced INTEGER,
    errors JSONB[],
    configuration JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- METRICS & ANALYTICS
-- =====================================================

-- System metrics for performance tracking
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(100),
    metric_name VARCHAR(100),
    value DECIMAL,
    unit VARCHAR(50),
    context JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    tags TEXT[]
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- System memory indexes
CREATE INDEX idx_system_memory_type ON system_memory(memory_type);
CREATE INDEX idx_system_memory_category ON system_memory(category);
CREATE INDEX idx_system_memory_tags ON system_memory USING gin(tags);
CREATE INDEX idx_system_memory_importance ON system_memory(importance_score DESC);
CREATE INDEX idx_system_memory_created ON system_memory(created_at DESC);
CREATE INDEX idx_system_memory_embeddings ON system_memory USING ivfflat (embeddings vector_cosine_ops);

-- Task memory indexes
CREATE INDEX idx_task_memory_status ON task_memory(status);
CREATE INDEX idx_task_memory_priority ON task_memory(priority DESC);
CREATE INDEX idx_task_memory_project ON task_memory(project_id);
CREATE INDEX idx_task_memory_assignee ON task_memory(assignee_id);
CREATE INDEX idx_task_memory_due ON task_memory(due_date);

-- Project memory indexes
CREATE INDEX idx_project_memory_status ON project_memory(status);
CREATE INDEX idx_project_memory_category ON project_memory(category);

-- Context threads indexes
CREATE INDEX idx_context_threads_type ON context_threads(thread_type);
CREATE INDEX idx_context_threads_active ON context_threads(is_active, last_active DESC);
CREATE INDEX idx_context_threads_embeddings ON context_threads USING ivfflat (embeddings vector_cosine_ops);

-- Decision indexes
CREATE INDEX idx_decisions_type ON decisions(decision_type);
CREATE INDEX idx_decisions_created ON decisions(created_at DESC);

-- Learning indexes
CREATE INDEX idx_learnings_category ON system_learnings(category);
CREATE INDEX idx_learnings_type ON system_learnings(learning_type);
CREATE INDEX idx_learnings_impact ON system_learnings(impact_score DESC);

-- Session indexes
CREATE INDEX idx_claude_sessions_active ON claude_sessions(is_active);
CREATE INDEX idx_claude_sessions_start ON claude_sessions(session_start DESC);

-- =====================================================
-- TRIGGERS FOR AUTO-UPDATES
-- =====================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_system_memory_updated_at
    BEFORE UPDATE ON system_memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-increment access count
CREATE OR REPLACE FUNCTION increment_access_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE system_memory
    SET access_count = access_count + 1,
        last_accessed = NOW()
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =====================================================
-- INITIAL DATA
-- =====================================================

-- Insert genesis memory
INSERT INTO system_memory (
    memory_type,
    category,
    title,
    content,
    importance_score,
    source_system
) VALUES (
    'context',
    'system_initialization',
    'BrainOps CNS Genesis',
    '{"event": "Central Nervous System initialized", "purpose": "Create persistent memory hub for all operations", "timestamp": "' || NOW() || '"}'::jsonb,
    1.0,
    'database'
) ON CONFLICT DO NOTHING;

-- Create initial automation rules
INSERT INTO automation_rules (
    rule_name,
    description,
    trigger_type,
    trigger_config,
    action_type,
    action_config
) VALUES
(
    'Auto-create tasks from conversations',
    'Automatically extract and create tasks from Claude Code conversations',
    'event',
    '{"event": "conversation_analyzed", "source": "claude_code"}'::jsonb,
    'create_task',
    '{"auto_assign": true, "auto_prioritize": true}'::jsonb
),
(
    'Daily summary generation',
    'Generate daily summary of all activities',
    'schedule',
    '{"cron": "0 0 * * *", "timezone": "UTC"}'::jsonb,
    'execute_workflow',
    '{"workflow": "generate_daily_summary"}'::jsonb
)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;