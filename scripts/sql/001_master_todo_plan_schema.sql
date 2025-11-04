-- BrainOps AI OS Master To-Do Plan Schema
-- Version: 1.0.0
-- Created: 2025-01-17
-- This creates the persistent, hierarchical task management system

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS task_os;
CREATE SCHEMA IF NOT EXISTS ops;
CREATE SCHEMA IF NOT EXISTS memory;
CREATE SCHEMA IF NOT EXISTS docs;

-- Task OS Core Tables
CREATE TABLE IF NOT EXISTS task_os.epics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')),
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    owner_agent VARCHAR(100) DEFAULT 'AUREA',
    target_envs JSONB DEFAULT '["dev", "staging", "prod"]'::jsonb,
    required_inputs JSONB DEFAULT '{}'::jsonb,
    required_secrets TEXT[],
    acceptance_criteria JSONB NOT NULL DEFAULT '[]'::jsonb,
    sli_slo JSONB DEFAULT '{}'::jsonb,
    rollback_plan TEXT,
    definition_of_done TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    supersedes_id UUID REFERENCES task_os.epics(id),
    created_by VARCHAR(100) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_at TIMESTAMPTZ,
    CONSTRAINT epic_title_unique UNIQUE (title, version)
);

CREATE TABLE IF NOT EXISTS task_os.stories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    epic_id UUID NOT NULL REFERENCES task_os.epics(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')),
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    story_points INTEGER CHECK (story_points BETWEEN 1 AND 21),
    assignee_agent VARCHAR(100) DEFAULT 'AUREA',
    upstream_dependencies UUID[],
    downstream_dependencies UUID[],
    schema_changes JSONB DEFAULT '[]'::jsonb,
    acceptance_tests JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT story_title_unique UNIQUE (epic_id, title)
);

CREATE TABLE IF NOT EXISTS task_os.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    story_id UUID REFERENCES task_os.stories(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES task_os.tasks(id),
    epic_id UUID REFERENCES task_os.epics(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled', 'failed')),
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    assignee_agent VARCHAR(100) DEFAULT 'AUREA',
    task_type VARCHAR(50) DEFAULT 'implementation'
        CHECK (task_type IN ('implementation', 'migration', 'test', 'review', 'deploy', 'monitor')),
    required_inputs JSONB DEFAULT '{}'::jsonb,
    outputs JSONB DEFAULT '{}'::jsonb,
    evidence_refs TEXT[],
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    cost_usd DECIMAL(10,2),
    created_by VARCHAR(100) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    due_at TIMESTAMPTZ,
    CONSTRAINT task_epic_or_story CHECK (
        (story_id IS NOT NULL AND epic_id IS NULL) OR 
        (story_id IS NULL AND epic_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS task_os.subtasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES task_os.tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped')),
    sequence_order INTEGER NOT NULL,
    is_required BOOLEAN NOT NULL DEFAULT true,
    command TEXT,
    expected_output JSONB,
    actual_output JSONB,
    evidence_ref TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT subtask_order_unique UNIQUE (task_id, sequence_order)
);

CREATE TABLE IF NOT EXISTS task_os.checklists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES task_os.tasks(id) ON DELETE CASCADE,
    item TEXT NOT NULL,
    required BOOLEAN NOT NULL DEFAULT true,
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'checked', 'skipped', 'failed')),
    evidence_ref TEXT,
    checked_by VARCHAR(100),
    checked_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS task_os.dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_task_id UUID NOT NULL REFERENCES task_os.tasks(id) ON DELETE CASCADE,
    to_task_id UUID NOT NULL REFERENCES task_os.tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'blocks'
        CHECK (dependency_type IN ('blocks', 'requires', 'suggests')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT no_self_dependency CHECK (from_task_id != to_task_id),
    CONSTRAINT unique_dependency UNIQUE (from_task_id, to_task_id, dependency_type)
);

-- Indexes for performance
CREATE INDEX idx_epics_status ON task_os.epics(status);
CREATE INDEX idx_stories_epic ON task_os.stories(epic_id);
CREATE INDEX idx_stories_status ON task_os.stories(status);
CREATE INDEX idx_tasks_story ON task_os.tasks(story_id);
CREATE INDEX idx_tasks_epic ON task_os.tasks(epic_id);
CREATE INDEX idx_tasks_parent ON task_os.tasks(parent_id);
CREATE INDEX idx_tasks_status ON task_os.tasks(status);
CREATE INDEX idx_tasks_assignee ON task_os.tasks(assignee_agent);
CREATE INDEX idx_subtasks_task ON task_os.subtasks(task_id);
CREATE INDEX idx_checklists_task ON task_os.checklists(task_id);
CREATE INDEX idx_dependencies_from ON task_os.dependencies(from_task_id);
CREATE INDEX idx_dependencies_to ON task_os.dependencies(to_task_id);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_epics_updated_at BEFORE UPDATE ON task_os.epics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stories_updated_at BEFORE UPDATE ON task_os.stories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON task_os.tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- RLS Policies
ALTER TABLE task_os.epics ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_os.stories ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_os.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_os.subtasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_os.checklists ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_os.dependencies ENABLE ROW LEVEL SECURITY;

-- Grant permissions
GRANT USAGE ON SCHEMA task_os TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA task_os TO authenticated;
GRANT INSERT, UPDATE ON task_os.tasks, task_os.checklists TO authenticated;

-- Create read-only role for observability
CREATE ROLE IF NOT EXISTS task_os_reader;
GRANT USAGE ON SCHEMA task_os TO task_os_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA task_os TO task_os_reader;

-- Create writer role for CI/CD
CREATE ROLE IF NOT EXISTS task_os_writer;
GRANT USAGE ON SCHEMA task_os TO task_os_writer;
GRANT ALL ON ALL TABLES IN SCHEMA task_os TO task_os_writer;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA task_os TO task_os_writer;