-- CNS (Central Nervous System) Database Schema
-- Creates all required tables for persistent memory and task management
-- v135.0.0 - Production Ready

-- Ensure pgvector extension is enabled (already installed!)
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- CORE MEMORY TABLE - The brain's persistent storage
-- =====================================================
CREATE TABLE IF NOT EXISTS cns_memory (
    memory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type VARCHAR(50) NOT NULL, -- context, decision, learning, event, etc.
    category VARCHAR(100) NOT NULL,   -- customer, job, invoice, system, etc.
    title TEXT NOT NULL,
    content JSONB NOT NULL,           -- Flexible JSON storage
    embedding vector(1536),           -- OpenAI ada-002 embeddings
    importance_score FLOAT DEFAULT 0.5,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    accessed_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    expires_at TIMESTAMP              -- Optional expiry for temporary memories
);

-- Indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_cns_memory_embedding
    ON cns_memory USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_cns_memory_type ON cns_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_cns_memory_category ON cns_memory(category);
CREATE INDEX IF NOT EXISTS idx_cns_memory_importance ON cns_memory(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_cns_memory_created ON cns_memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cns_memory_tags ON cns_memory USING gin(tags);

-- =====================================================
-- TASK MANAGEMENT - The brain's action center
-- =====================================================
CREATE TABLE IF NOT EXISTS cns_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    parent_task_id UUID,
    title TEXT NOT NULL,
    description TEXT,
    priority FLOAT DEFAULT 0.5,       -- AI-calculated priority
    urgency FLOAT DEFAULT 0.5,        -- AI-calculated urgency
    importance FLOAT DEFAULT 0.5,     -- AI-calculated importance
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, blocked
    assigned_to VARCHAR(255),
    created_by VARCHAR(255),
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    dependencies UUID[] DEFAULT '{}', -- Other tasks this depends on
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (parent_task_id) REFERENCES cns_tasks(task_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_cns_tasks_status ON cns_tasks(status);
CREATE INDEX IF NOT EXISTS idx_cns_tasks_priority ON cns_tasks(priority DESC);
CREATE INDEX IF NOT EXISTS idx_cns_tasks_due_date ON cns_tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_cns_tasks_project ON cns_tasks(project_id);

-- =====================================================
-- PROJECTS - High-level organization
-- =====================================================
CREATE TABLE IF NOT EXISTS cns_projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    priority FLOAT DEFAULT 0.5,
    owner VARCHAR(255),
    team TEXT[] DEFAULT '{}',
    start_date TIMESTAMP DEFAULT NOW(),
    target_date TIMESTAMP,
    completed_at TIMESTAMP,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cns_projects_status ON cns_projects(status);
CREATE INDEX IF NOT EXISTS idx_cns_projects_priority ON cns_projects(priority DESC);

-- =====================================================
-- THREADS - Conversation continuity
-- =====================================================
CREATE TABLE IF NOT EXISTS cns_threads (
    thread_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    context TEXT,
    participants TEXT[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cns_threads_status ON cns_threads(status);
CREATE INDEX IF NOT EXISTS idx_cns_threads_activity ON cns_threads(last_activity DESC);

-- =====================================================
-- DECISIONS - Learning from choices
-- =====================================================
CREATE TABLE IF NOT EXISTS cns_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context TEXT NOT NULL,
    question TEXT NOT NULL,
    options JSONB NOT NULL,           -- Array of options considered
    chosen_option JSONB NOT NULL,     -- What was chosen
    reasoning TEXT,                    -- Why it was chosen
    outcome VARCHAR(50),               -- success, failure, partial, unknown
    outcome_details TEXT,
    confidence_score FLOAT,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    evaluated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cns_decisions_outcome ON cns_decisions(outcome);
CREATE INDEX IF NOT EXISTS idx_cns_decisions_created ON cns_decisions(created_at DESC);

-- =====================================================
-- AUTOMATIONS - Event-driven actions
-- =====================================================
CREATE TABLE IF NOT EXISTS cns_automations (
    automation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    trigger_type VARCHAR(100) NOT NULL, -- time, event, condition
    trigger_config JSONB NOT NULL,      -- Specific trigger configuration
    action_type VARCHAR(100) NOT NULL,  -- task, notification, api_call, etc.
    action_config JSONB NOT NULL,       -- Specific action configuration
    enabled BOOLEAN DEFAULT true,
    last_triggered TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cns_automations_enabled ON cns_automations(enabled);
CREATE INDEX IF NOT EXISTS idx_cns_automations_trigger ON cns_automations(trigger_type);

-- =====================================================
-- LEARNING PATTERNS - AI improvement over time
-- =====================================================
CREATE TABLE IF NOT EXISTS cns_learning_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(100) NOT NULL, -- behavior, preference, optimization
    pattern_data JSONB NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    occurrences INTEGER DEFAULT 1,
    last_observed TIMESTAMP DEFAULT NOW(),
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cns_patterns_type ON cns_learning_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_cns_patterns_confidence ON cns_learning_patterns(confidence DESC);

-- =====================================================
-- CONTEXT PERSISTENCE - Cross-session memory
-- =====================================================
CREATE TABLE IF NOT EXISTS cns_context_persistence (
    context_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    context_type VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL,
    importance FLOAT DEFAULT 0.5,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cns_context_session ON cns_context_persistence(session_id);
CREATE INDEX IF NOT EXISTS idx_cns_context_user ON cns_context_persistence(user_id);
CREATE INDEX IF NOT EXISTS idx_cns_context_type ON cns_context_persistence(context_type);

-- =====================================================
-- SYSTEM DOCUMENTATION - Never lose track again
-- =====================================================
CREATE TABLE IF NOT EXISTS cns_system_documentation (
    doc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_name VARCHAR(100) NOT NULL,
    component VARCHAR(100) NOT NULL,
    doc_type VARCHAR(50) NOT NULL,    -- credential, api, process, architecture
    title TEXT NOT NULL,
    content JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(system_name, component, title)
);

CREATE INDEX IF NOT EXISTS idx_cns_docs_system ON cns_system_documentation(system_name);
CREATE INDEX IF NOT EXISTS idx_cns_docs_component ON cns_system_documentation(component);
CREATE INDEX IF NOT EXISTS idx_cns_docs_type ON cns_system_documentation(doc_type);

-- =====================================================
-- HELPER FUNCTIONS
-- =====================================================

-- Function to clean old memories
CREATE OR REPLACE FUNCTION cns_cleanup_old_memories()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM cns_memory
    WHERE expires_at < NOW()
    OR (importance_score < 0.3 AND last_accessed < NOW() - INTERVAL '30 days');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update task priorities
CREATE OR REPLACE FUNCTION cns_update_task_priority()
RETURNS TRIGGER AS $$
BEGIN
    -- Recalculate priority based on urgency and importance
    NEW.priority = (NEW.urgency * 0.6 + NEW.importance * 0.4);
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_task_priority
    BEFORE UPDATE ON cns_tasks
    FOR EACH ROW
    WHEN (OLD.urgency IS DISTINCT FROM NEW.urgency OR OLD.importance IS DISTINCT FROM NEW.importance)
    EXECUTE FUNCTION cns_update_task_priority();

-- =====================================================
-- INITIAL SYSTEM DOCUMENTATION
-- =====================================================
INSERT INTO cns_system_documentation (system_name, component, doc_type, title, content) VALUES
('BrainOps', 'Backend', 'architecture', 'System Overview', '{
    "version": "v135.0.0",
    "framework": "FastAPI",
    "database": "PostgreSQL with pgvector",
    "deployment": "Docker on Render",
    "features": ["CNS Memory System", "AI Integration", "Task Management", "Multi-tenant"]
}'::jsonb),
('BrainOps', 'Database', 'credential', 'Production Database', '{
    "host": "aws-0-us-east-2.pooler.supabase.com",
    "port": 5432,
    "database": "postgres",
    "user": "postgres.yomagoqdmxszqtdwuhab",
    "password": "Brain0ps2O2S"
}'::jsonb),
('BrainOps', 'Deployment', 'api', 'Render API', '{
    "api_key": "rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx",
    "service_id": "srv-d1tfs4idbo4c73di6k00",
    "url": "https://brainops-backend-prod.onrender.com"
}'::jsonb)
ON CONFLICT (system_name, component, title) DO UPDATE
SET content = EXCLUDED.content,
    updated_at = NOW(),
    version = cns_system_documentation.version + 1;

-- Success message
SELECT 'CNS Schema Created Successfully!' as status,
       COUNT(*) as tables_created
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'cns_%';