-- Job tasks and cost tracking tables

-- Create job_tasks table
CREATE TABLE IF NOT EXISTS job_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2),
    assigned_to UUID,
    parent_task_id UUID,
    dependencies JSONB DEFAULT '[]',
    due_date TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    completion_percentage INTEGER DEFAULT 0,
    tags JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_task_id) REFERENCES job_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create task checklist items table
CREATE TABLE IF NOT EXISTS task_checklist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    item_text TEXT NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_by UUID,
    completed_at TIMESTAMP,
    notes TEXT,
    display_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES job_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (completed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create task status history table
CREATE TABLE IF NOT EXISTS task_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    changed_by UUID,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (task_id) REFERENCES job_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create task templates table
CREATE TABLE IF NOT EXISTS task_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    job_type VARCHAR(100),
    tasks JSONB NOT NULL,
    estimated_total_hours DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create job_expenses table
CREATE TABLE IF NOT EXISTS job_expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(12,2),
    quantity DECIMAL(10,2) DEFAULT 1,
    unit_cost DECIMAL(12,2),
    total_amount DECIMAL(12,2) NOT NULL,
    billable_amount DECIMAL(12,2) DEFAULT 0,
    vendor VARCHAR(255),
    invoice_number VARCHAR(100),
    expense_date DATE NOT NULL,
    employee_id UUID,
    is_billable BOOLEAN DEFAULT TRUE,
    markup_percentage DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    approved_by UUID,
    approved_at TIMESTAMP,
    approval_notes TEXT,
    receipt_url TEXT,
    notes TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create job_material_usage table
CREATE TABLE IF NOT EXISTS job_material_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    material_id UUID NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(12,2),
    total_cost DECIMAL(12,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create job_labor_entries table
CREATE TABLE IF NOT EXISTS job_labor_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    employee_id UUID NOT NULL,
    hours_worked DECIMAL(10,2) NOT NULL,
    hourly_rate DECIMAL(10,2),
    total_cost DECIMAL(12,2),
    work_date DATE NOT NULL,
    task_id UUID,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES job_tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create materials table if not exists
CREATE TABLE IF NOT EXISTS materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    unit_of_measure VARCHAR(50),
    unit_cost DECIMAL(12,2),
    quantity_on_hand DECIMAL(10,2) DEFAULT 0,
    reorder_level DECIMAL(10,2),
    vendor VARCHAR(255),
    sku VARCHAR(100),
    category VARCHAR(100),
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_tasks_job_id ON job_tasks(job_id);
CREATE INDEX IF NOT EXISTS idx_job_tasks_assigned_to ON job_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_job_tasks_parent_task_id ON job_tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_job_tasks_status ON job_tasks(status);
CREATE INDEX IF NOT EXISTS idx_job_tasks_due_date ON job_tasks(due_date);

CREATE INDEX IF NOT EXISTS idx_task_checklist_items_task_id ON task_checklist_items(task_id);
CREATE INDEX IF NOT EXISTS idx_task_checklist_items_is_completed ON task_checklist_items(is_completed);

CREATE INDEX IF NOT EXISTS idx_task_status_history_task_id ON task_status_history(task_id);
CREATE INDEX IF NOT EXISTS idx_task_status_history_changed_at ON task_status_history(changed_at DESC);

CREATE INDEX IF NOT EXISTS idx_job_expenses_job_id ON job_expenses(job_id);
CREATE INDEX IF NOT EXISTS idx_job_expenses_category ON job_expenses(category);
CREATE INDEX IF NOT EXISTS idx_job_expenses_expense_date ON job_expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_job_expenses_status ON job_expenses(status);
CREATE INDEX IF NOT EXISTS idx_job_expenses_employee_id ON job_expenses(employee_id);

CREATE INDEX IF NOT EXISTS idx_job_material_usage_job_id ON job_material_usage(job_id);
CREATE INDEX IF NOT EXISTS idx_job_material_usage_material_id ON job_material_usage(material_id);

CREATE INDEX IF NOT EXISTS idx_job_labor_entries_job_id ON job_labor_entries(job_id);
CREATE INDEX IF NOT EXISTS idx_job_labor_entries_employee_id ON job_labor_entries(employee_id);
CREATE INDEX IF NOT EXISTS idx_job_labor_entries_work_date ON job_labor_entries(work_date);

-- Add missing columns to employees table if needed
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS hourly_rate DECIMAL(10,2);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON job_tasks TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON task_checklist_items TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON task_status_history TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON task_templates TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON job_expenses TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON job_material_usage TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON job_labor_entries TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON materials TO authenticated;
