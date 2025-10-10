-- Project Management Tables - Tasks 51-60
-- Complete project lifecycle management system

-- Projects table (Task 51 - Project Creation)
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    description TEXT,
    project_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    priority VARCHAR(20) DEFAULT 'medium',
    customer_id UUID,
    manager_id VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    budget DECIMAL(15,2),
    actual_cost DECIMAL(15,2) DEFAULT 0,
    completion_percentage INTEGER DEFAULT 0,
    is_template BOOLEAN DEFAULT false,
    parent_project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Project team members (Task 51)
CREATE TABLE IF NOT EXISTS project_team (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    employee_id VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    allocation_percentage INTEGER DEFAULT 100,
    start_date DATE NOT NULL,
    end_date DATE,
    hourly_rate DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_project_team UNIQUE(project_id, employee_id, role)
);

-- Project phases (Task 52 - Project Planning)
CREATE TABLE IF NOT EXISTS project_phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_name VARCHAR(200) NOT NULL,
    phase_number INTEGER NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'planned',
    deliverables TEXT[],
    budget DECIMAL(12,2),
    actual_cost DECIMAL(12,2) DEFAULT 0,
    completion_percentage INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_project_phase UNIQUE(project_id, phase_number)
);

-- Project tasks (Task 52)
CREATE TABLE IF NOT EXISTS project_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES project_phases(id) ON DELETE CASCADE,
    task_code VARCHAR(50) UNIQUE NOT NULL,
    task_name VARCHAR(200) NOT NULL,
    description TEXT,
    assigned_to VARCHAR(100),
    status VARCHAR(50) DEFAULT 'todo',
    priority VARCHAR(20) DEFAULT 'medium',
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    start_date DATE,
    due_date DATE,
    completed_date DATE,
    completion_percentage INTEGER DEFAULT 0,
    dependencies UUID[],
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Milestones (Task 53 - Milestone Tracking)
CREATE TABLE IF NOT EXISTS project_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    milestone_name VARCHAR(200) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    completed_date DATE,
    status VARCHAR(50) DEFAULT 'pending',
    deliverables TEXT[],
    success_criteria TEXT,
    payment_triggered BOOLEAN DEFAULT false,
    payment_amount DECIMAL(12,2),
    responsible_person VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resource allocations (Task 54 - Resource Allocation)
CREATE TABLE IF NOT EXISTS project_resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    resource_name VARCHAR(200) NOT NULL,
    quantity DECIMAL(10,2) DEFAULT 1,
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(12,2),
    allocation_start DATE NOT NULL,
    allocation_end DATE,
    status VARCHAR(50) DEFAULT 'allocated',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Gantt chart data (Task 55 - Gantt Charts)
CREATE TABLE IF NOT EXISTS project_gantt_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES project_tasks(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES project_gantt_tasks(id) ON DELETE CASCADE,
    task_name VARCHAR(200) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration INTEGER NOT NULL,
    progress INTEGER DEFAULT 0,
    dependencies UUID[],
    row_order INTEGER,
    expanded BOOLEAN DEFAULT true,
    color VARCHAR(7),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dependencies (Task 56 - Dependencies Management)
CREATE TABLE IF NOT EXISTS project_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    predecessor_task_id UUID NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    successor_task_id UUID NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) NOT NULL DEFAULT 'finish_to_start',
    lag_days INTEGER DEFAULT 0,
    is_critical BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_dependency UNIQUE(predecessor_task_id, successor_task_id)
);

-- Critical path (Task 57 - Critical Path)
CREATE TABLE IF NOT EXISTS project_critical_path (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES project_tasks(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    early_start DATE,
    early_finish DATE,
    late_start DATE,
    late_finish DATE,
    total_float INTEGER DEFAULT 0,
    free_float INTEGER DEFAULT 0,
    is_critical BOOLEAN DEFAULT false,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_critical_path UNIQUE(project_id, task_id)
);

-- Project templates (Task 58 - Project Templates)
CREATE TABLE IF NOT EXISTS project_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(200) NOT NULL UNIQUE,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(100),
    project_type VARCHAR(50) NOT NULL,
    typical_duration_days INTEGER,
    phases JSONB DEFAULT '[]',
    tasks JSONB DEFAULT '[]',
    milestones JSONB DEFAULT '[]',
    resources JSONB DEFAULT '[]',
    estimated_budget DECIMAL(12,2),
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Project reports (Task 59 - Project Reporting)
CREATE TABLE IF NOT EXISTS project_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    report_type VARCHAR(50) NOT NULL,
    report_date DATE NOT NULL,
    generated_by VARCHAR(100) NOT NULL,
    status_summary TEXT,
    progress_percentage INTEGER,
    budget_used DECIMAL(12,2),
    budget_remaining DECIMAL(12,2),
    issues_count INTEGER DEFAULT 0,
    risks_count INTEGER DEFAULT 0,
    key_metrics JSONB DEFAULT '{}',
    attachments TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Project dashboards config (Task 60 - Project Dashboards)
CREATE TABLE IF NOT EXISTS project_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,
    dashboard_name VARCHAR(200) NOT NULL,
    layout JSONB DEFAULT '{}',
    widgets JSONB DEFAULT '[]',
    refresh_interval INTEGER DEFAULT 300,
    is_default BOOLEAN DEFAULT false,
    is_shared BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_user_dashboard UNIQUE(project_id, user_id, dashboard_name)
);

-- Project time tracking
CREATE TABLE IF NOT EXISTS project_time_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES project_tasks(id) ON DELETE CASCADE,
    employee_id VARCHAR(100) NOT NULL,
    entry_date DATE NOT NULL,
    hours_worked DECIMAL(5,2) NOT NULL,
    description TEXT,
    billable BOOLEAN DEFAULT true,
    approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_manager ON projects(manager_id);
CREATE INDEX idx_projects_customer ON projects(customer_id);
CREATE INDEX idx_project_team_project ON project_team(project_id);
CREATE INDEX idx_project_team_employee ON project_team(employee_id);
CREATE INDEX idx_project_phases_project ON project_phases(project_id);
CREATE INDEX idx_project_tasks_project ON project_tasks(project_id);
CREATE INDEX idx_project_tasks_assigned ON project_tasks(assigned_to);
CREATE INDEX idx_project_tasks_status ON project_tasks(status);
CREATE INDEX idx_project_milestones_project ON project_milestones(project_id);
CREATE INDEX idx_project_milestones_due_date ON project_milestones(due_date);
CREATE INDEX idx_project_resources_project ON project_resources(project_id);
CREATE INDEX idx_project_gantt_project ON project_gantt_tasks(project_id);
CREATE INDEX idx_project_dependencies_project ON project_dependencies(project_id);
CREATE INDEX idx_project_critical_path_project ON project_critical_path(project_id);
CREATE INDEX idx_project_reports_project ON project_reports(project_id);
CREATE INDEX idx_project_dashboards_user ON project_dashboards(user_id);
CREATE INDEX idx_project_time_entries_project ON project_time_entries(project_id);
CREATE INDEX idx_project_time_entries_employee ON project_time_entries(employee_id);

-- Add comments
COMMENT ON TABLE projects IS 'Main project management table';
COMMENT ON TABLE project_team IS 'Project team members and roles';
COMMENT ON TABLE project_phases IS 'Project phases and stages';
COMMENT ON TABLE project_tasks IS 'Detailed project tasks';
COMMENT ON TABLE project_milestones IS 'Project milestones and deliverables';
COMMENT ON TABLE project_resources IS 'Resource allocation for projects';
COMMENT ON TABLE project_gantt_tasks IS 'Gantt chart visualization data';
COMMENT ON TABLE project_dependencies IS 'Task dependencies and relationships';
COMMENT ON TABLE project_critical_path IS 'Critical path analysis results';
COMMENT ON TABLE project_templates IS 'Reusable project templates';
COMMENT ON TABLE project_reports IS 'Project status reports';
COMMENT ON TABLE project_dashboards IS 'Customizable project dashboards';
COMMENT ON TABLE project_time_entries IS 'Time tracking for project tasks';