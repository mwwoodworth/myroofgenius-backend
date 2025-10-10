-- BrainOps AI OS Master To-Do Plan Seed Data
-- Version: 1.0.0
-- Created: 2025-01-17
-- This seeds the comprehensive hierarchical task structure

-- Clear existing data (for idempotent runs)
TRUNCATE task_os.dependencies CASCADE;
TRUNCATE task_os.checklists CASCADE;
TRUNCATE task_os.subtasks CASCADE;
TRUNCATE task_os.tasks CASCADE;
TRUNCATE task_os.stories CASCADE;
TRUNCATE task_os.epics CASCADE;

-- Insert Epics
INSERT INTO task_os.epics (id, title, description, priority, status, definition_of_done, acceptance_criteria) VALUES
-- Infrastructure & Persistence
('e1000000-0000-0000-0000-000000000001', 
 'Persistent Master To-Do Plan', 
 'Create and maintain a comprehensive, hierarchical task management system that survives restarts and compactions',
 1, 'in_progress',
 'DB schema created, seed data loaded, CLI tools operational, all tasks queryable and versioned',
 '[{"criteria": "Schema supports full hierarchy", "met": false}, {"criteria": "Versioning implemented", "met": false}, {"criteria": "CLI tools working", "met": false}]'::jsonb),

('e1000000-0000-0000-0000-000000000002',
 'Persistent Memory DB Schema',
 'Implement comprehensive database schema for all operational data with proper constraints and RLS',
 1, 'pending',
 'All tables created with constraints, RLS policies active, migrations tested on staging and prod',
 '[{"criteria": "All schemas created", "met": false}, {"criteria": "RLS policies enforced", "met": false}, {"criteria": "Migrations reversible", "met": false}]'::jsonb),

('e1000000-0000-0000-0000-000000000003',
 'Master Env-Var Registry',
 'Build authoritative environment variable registry with validation and CI integration',
 1, 'pending',
 'Registry populated from all services, CI blocks on missing vars, secrets managed via OIDC',
 '[{"criteria": "Scanner finds all env usage", "met": false}, {"criteria": "CI validation working", "met": false}, {"criteria": "Secrets never in repo", "met": false}]'::jsonb),

('e1000000-0000-0000-0000-000000000004',
 'Task OS with Slack Integration',
 'Implement task management service with full Slack communication',
 2, 'pending',
 'FastAPI service deployed, Slack bot active, all events streaming to channels with evidence',
 '[{"criteria": "Service handles CRUD ops", "met": false}, {"criteria": "Slack bot responds", "met": false}, {"criteria": "Events have deep links", "met": false}]'::jsonb),

-- CI/CD & Infrastructure
('e1000000-0000-0000-0000-000000000005',
 'Docker & CI/CD Hardening',
 'Production-grade containerization and deployment pipeline',
 1, 'pending',
 'Multi-stage builds optimized, GHCR publishing working, vulnerability scanning enforced',
 '[{"criteria": "BuildKit cache working", "met": false}, {"criteria": "SBOM generated", "met": false}, {"criteria": "High vulns block merge", "met": false}]'::jsonb),

('e1000000-0000-0000-0000-000000000006',
 'Supabase Persistence & Migrations',
 'Implement safe, versioned database migration system',
 1, 'pending',
 'Migration pipeline with staging validation, automatic rollback capability, SOP updates',
 '[{"criteria": "Staging test required", "met": false}, {"criteria": "Rollback tested", "met": false}, {"criteria": "SOPs auto-updated", "met": false}]'::jsonb),

-- AI Systems
('e1000000-0000-0000-0000-000000000007',
 'AI Board & AUREA Integration',
 'Build LangGraph orchestration for AI board and AUREA conductor',
 2, 'pending',
 'LangGraph nodes operational, memory bus connected, all decisions persisted with evidence',
 '[{"criteria": "5 AI nodes integrated", "met": false}, {"criteria": "Memory bus working", "met": false}, {"criteria": "Decisions traceable", "met": false}]'::jsonb),

('e1000000-0000-0000-0000-000000000008',
 'Centerpoint Data Sync',
 'Complete 100% data synchronization with Centerpoint',
 2, 'pending',
 'All Centerpoint data ingested, validated, and reconciled with lineage tracking',
 '[{"criteria": "100% sync achieved", "met": false}, {"criteria": "Validation passing", "met": false}, {"criteria": "Lineage tracked", "met": false}]'::jsonb),

-- Business Systems
('e1000000-0000-0000-0000-000000000009',
 'ERP AI-Native Hardening',
 'Transform ERP into AI-native powerhouse with full observability',
 2, 'pending',
 'Copilot embedded, OpenTelemetry active, KPIs on dashboard, a11y gates passing',
 '[{"criteria": "Copilot responding", "met": false}, {"criteria": "Traces flowing", "met": false}, {"criteria": "a11y 100%", "met": false}]'::jsonb),

('e1000000-0000-0000-0000-000000000010',
 'Revenue & SendGrid Pipelines',
 'Implement real money and email pipelines with full tracking',
 1, 'pending',
 'Stripe/Gumroad webhooks processing, SendGrid events captured, test transactions verified',
 '[{"criteria": "Payment webhooks live", "met": false}, {"criteria": "Emails delivered", "met": false}, {"criteria": "Audit logs complete", "met": false}]'::jsonb),

-- Orchestration & Testing
('e1000000-0000-0000-0000-000000000011',
 'LangGraph Orchestration',
 'Implement end-to-end business flow orchestration',
 3, 'pending',
 'Lead-to-cash flow automated, all nodes emit proof, ground-truth validation passing',
 '[{"criteria": "Full flow working", "met": false}, {"criteria": "Proofs generated", "met": false}, {"criteria": "Validation passing", "met": false}]'::jsonb),

('e1000000-0000-0000-0000-000000000012',
 'Reality-Check Testing Suite',
 'Comprehensive testing that validates real business outcomes',
 2, 'pending',
 'All systems have real-data tests, CI fails on missing evidence, business metrics verified',
 '[{"criteria": "Real data used", "met": false}, {"criteria": "Evidence required", "met": false}, {"criteria": "Metrics accurate", "met": false}]'::jsonb),

('e1000000-0000-0000-0000-000000000013',
 'Founder Notifications & Governance',
 'Implement executive notification and decision tracking',
 3, 'pending',
 'Founder receives critical alerts, all decisions logged, SOPs maintained as source of truth',
 '[{"criteria": "Slack DMs working", "met": false}, {"criteria": "Decisions tracked", "met": false}, {"criteria": "SOPs current", "met": false}]'::jsonb);

-- Insert Stories for Epic 1 (Persistent Master To-Do Plan)
INSERT INTO task_os.stories (id, epic_id, title, description, priority, story_points) VALUES
('s1000000-0000-0000-0000-000000000001', 'e1000000-0000-0000-0000-000000000001',
 'Design hierarchical task schema',
 'Create database schema supporting epics, stories, tasks, subtasks with full metadata',
 1, 5),
('s1000000-0000-0000-0000-000000000002', 'e1000000-0000-0000-0000-000000000001',
 'Implement seed data loader',
 'Create comprehensive seed data covering all 13 epics with realistic task breakdowns',
 1, 3),
('s1000000-0000-0000-0000-000000000003', 'e1000000-0000-0000-0000-000000000001',
 'Build CLI tools for task management',
 'Create command-line tools for querying and updating task status',
 2, 8);

-- Insert Tasks for Story 1
INSERT INTO task_os.tasks (id, story_id, title, description, priority, task_type, status) VALUES
('t1000000-0000-0000-0000-000000000001', 's1000000-0000-0000-0000-000000000001',
 'Create epic and story tables',
 'Define tables for epics and stories with all required fields',
 1, 'migration', 'completed'),
('t1000000-0000-0000-0000-000000000002', 's1000000-0000-0000-0000-000000000001',
 'Create task and subtask tables',
 'Define tables for tasks and subtasks with hierarchical relationships',
 1, 'migration', 'completed'),
('t1000000-0000-0000-0000-000000000003', 's1000000-0000-0000-0000-000000000001',
 'Add constraints and indexes',
 'Implement foreign keys, check constraints, and performance indexes',
 1, 'migration', 'in_progress'),
('t1000000-0000-0000-0000-000000000004', 's1000000-0000-0000-0000-000000000001',
 'Implement RLS policies',
 'Create row-level security policies for all tables',
 2, 'migration', 'pending');

-- Insert Subtasks for detailed implementation
INSERT INTO task_os.subtasks (task_id, title, sequence_order, is_required, command) VALUES
('t1000000-0000-0000-0000-000000000001', 
 'Create task_os schema', 1, true,
 'CREATE SCHEMA IF NOT EXISTS task_os;'),
('t1000000-0000-0000-0000-000000000001',
 'Create epics table', 2, true,
 'CREATE TABLE task_os.epics (...);'),
('t1000000-0000-0000-0000-000000000001',
 'Create stories table', 3, true,
 'CREATE TABLE task_os.stories (...);');

-- Insert Checklists for validation
INSERT INTO task_os.checklists (task_id, item, required) VALUES
('t1000000-0000-0000-0000-000000000001', 'Schema created successfully', true),
('t1000000-0000-0000-0000-000000000001', 'Tables support UUID primary keys', true),
('t1000000-0000-0000-0000-000000000001', 'Foreign key relationships established', true),
('t1000000-0000-0000-0000-000000000002', 'Hierarchical queries work correctly', true),
('t1000000-0000-0000-0000-000000000002', 'Circular dependency prevention works', true);

-- Insert Dependencies
INSERT INTO task_os.dependencies (from_task_id, to_task_id, dependency_type) VALUES
('t1000000-0000-0000-0000-000000000001', 't1000000-0000-0000-0000-000000000002', 'blocks'),
('t1000000-0000-0000-0000-000000000002', 't1000000-0000-0000-0000-000000000003', 'blocks'),
('t1000000-0000-0000-0000-000000000003', 't1000000-0000-0000-0000-000000000004', 'blocks');

-- Insert sample Stories and Tasks for other Epics (abbreviated for space)
-- Epic 2: Persistent Memory DB Schema
INSERT INTO task_os.stories (epic_id, title, priority) VALUES
('e1000000-0000-0000-0000-000000000002', 'Create core schema tables', 1),
('e1000000-0000-0000-0000-000000000002', 'Implement memory tables', 1),
('e1000000-0000-0000-0000-000000000002', 'Setup operational logging', 2);

-- Epic 3: Master Env-Var Registry
INSERT INTO task_os.stories (epic_id, title, priority) VALUES
('e1000000-0000-0000-0000-000000000003', 'Build env scanner tool', 1),
('e1000000-0000-0000-0000-000000000003', 'Create validation pipeline', 1),
('e1000000-0000-0000-0000-000000000003', 'Integrate with CI/CD', 2);

-- Create function to get task hierarchy
CREATE OR REPLACE FUNCTION task_os.get_task_hierarchy(epic_uuid UUID DEFAULT NULL)
RETURNS TABLE (
    level INTEGER,
    id UUID,
    parent_id UUID,
    title TEXT,
    status VARCHAR(50),
    type TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE hierarchy AS (
        -- Epics level
        SELECT 1 as level, 
               e.id, 
               NULL::UUID as parent_id, 
               e.title, 
               e.status,
               'epic'::TEXT as type
        FROM task_os.epics e
        WHERE (epic_uuid IS NULL OR e.id = epic_uuid)
        
        UNION ALL
        
        -- Stories level
        SELECT 2 as level,
               s.id,
               s.epic_id as parent_id,
               s.title,
               s.status,
               'story'::TEXT as type
        FROM task_os.stories s
        INNER JOIN hierarchy h ON h.id = s.epic_id AND h.type = 'epic'
        
        UNION ALL
        
        -- Tasks level
        SELECT 3 as level,
               t.id,
               COALESCE(t.story_id, t.epic_id) as parent_id,
               t.title,
               t.status,
               'task'::TEXT as type
        FROM task_os.tasks t
        INNER JOIN hierarchy h ON 
            (h.id = t.story_id AND h.type = 'story') OR
            (h.id = t.epic_id AND h.type = 'epic')
            
        UNION ALL
        
        -- Subtasks level
        SELECT 4 as level,
               st.id,
               st.task_id as parent_id,
               st.title,
               st.status,
               'subtask'::TEXT as type
        FROM task_os.subtasks st
        INNER JOIN hierarchy h ON h.id = st.task_id AND h.type = 'task'
    )
    SELECT * FROM hierarchy ORDER BY level, parent_id, title;
END;
$$ LANGUAGE plpgsql;

-- Create view for task status summary
CREATE OR REPLACE VIEW task_os.task_status_summary AS
SELECT 
    'epics' as level,
    status,
    COUNT(*) as count
FROM task_os.epics
GROUP BY status

UNION ALL

SELECT 
    'stories' as level,
    status,
    COUNT(*) as count
FROM task_os.stories
GROUP BY status

UNION ALL

SELECT 
    'tasks' as level,
    status,
    COUNT(*) as count
FROM task_os.tasks
GROUP BY status

UNION ALL

SELECT 
    'subtasks' as level,
    status,
    COUNT(*) as count
FROM task_os.subtasks
GROUP BY status

ORDER BY level, status;

-- Verify insertion
DO $$
DECLARE
    epic_count INTEGER;
    story_count INTEGER;
    task_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO epic_count FROM task_os.epics;
    SELECT COUNT(*) INTO story_count FROM task_os.stories;
    SELECT COUNT(*) INTO task_count FROM task_os.tasks;
    
    RAISE NOTICE 'Master To-Do Plan loaded: % epics, % stories, % tasks', 
                 epic_count, story_count, task_count;
END $$;