-- Job lifecycle management tables
-- Track job status transitions and history

-- Create job status history table
CREATE TABLE IF NOT EXISTS job_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    changed_by UUID,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(255),
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create job notes table
CREATE TABLE IF NOT EXISTS job_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,
    attachments JSONB DEFAULT '[]',
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create notifications table if not exists
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255),
    message TEXT,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add missing columns to jobs table
ALTER TABLE jobs
    ADD COLUMN IF NOT EXISTS job_type VARCHAR(50),
    ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'medium',
    ADD COLUMN IF NOT EXISTS scheduled_start TIMESTAMP,
    ADD COLUMN IF NOT EXISTS scheduled_end TIMESTAMP,
    ADD COLUMN IF NOT EXISTS actual_start TIMESTAMP,
    ADD COLUMN IF NOT EXISTS actual_end TIMESTAMP,
    ADD COLUMN IF NOT EXISTS estimated_hours DECIMAL(10,2),
    ADD COLUMN IF NOT EXISTS actual_hours DECIMAL(10,2),
    ADD COLUMN IF NOT EXISTS estimated_cost DECIMAL(12,2),
    ADD COLUMN IF NOT EXISTS actual_cost DECIMAL(12,2),
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS cancelled_by UUID,
    ADD COLUMN IF NOT EXISTS cancellation_reason TEXT,
    ADD COLUMN IF NOT EXISTS assigned_crew_id UUID,
    ADD COLUMN IF NOT EXISTS service_address VARCHAR(255),
    ADD COLUMN IF NOT EXISTS service_city VARCHAR(100),
    ADD COLUMN IF NOT EXISTS service_state VARCHAR(2),
    ADD COLUMN IF NOT EXISTS service_zip VARCHAR(10),
    ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS custom_fields JSONB DEFAULT '{}';

-- Create employee_jobs junction table
CREATE TABLE IF NOT EXISTS employee_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL,
    job_id UUID NOT NULL,
    role VARCHAR(100),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    hours_worked DECIMAL(10,2),
    notes TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    UNIQUE(employee_id, job_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_status_history_job_id ON job_status_history(job_id);
CREATE INDEX IF NOT EXISTS idx_job_status_history_changed_at ON job_status_history(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_status_history_to_status ON job_status_history(to_status);

CREATE INDEX IF NOT EXISTS idx_job_notes_job_id ON job_notes(job_id);
CREATE INDEX IF NOT EXISTS idx_job_notes_created_at ON job_notes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_notes_is_internal ON job_notes(is_internal);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_resource ON notifications(resource_type, resource_id);

CREATE INDEX IF NOT EXISTS idx_employee_jobs_employee_id ON employee_jobs(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_jobs_job_id ON employee_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_employee_jobs_assigned_at ON employee_jobs(assigned_at DESC);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority);
CREATE INDEX IF NOT EXISTS idx_jobs_scheduled_start ON jobs(scheduled_start);
CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_assigned_crew_id ON jobs(assigned_crew_id);

-- Add triggers for updated_at
CREATE OR REPLACE FUNCTION update_job_notes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_job_notes_updated_at
    BEFORE UPDATE ON job_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_job_notes_updated_at();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON job_status_history TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON job_notes TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON notifications TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON employee_jobs TO authenticated;

-- Add RLS policies
ALTER TABLE job_status_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_jobs ENABLE ROW LEVEL SECURITY;

-- Users can see job history for jobs they have access to
CREATE POLICY job_status_history_policy ON job_status_history
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM jobs
            WHERE jobs.id = job_status_history.job_id
            AND (jobs.created_by = current_setting('app.current_user_id')::UUID
                OR jobs.assigned_crew_id IN (
                    SELECT crew_id FROM crew_members
                    WHERE user_id = current_setting('app.current_user_id')::UUID
                ))
        )
    );

-- Users can only see their own notifications
CREATE POLICY notifications_user_policy ON notifications
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID);
