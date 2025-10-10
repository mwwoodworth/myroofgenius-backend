-- Employee Onboarding Tables - Task 45
-- Complete employee onboarding workflow management

-- Main onboarding process table
CREATE TABLE IF NOT EXISTS employee_onboarding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(100) NOT NULL,
    employee_name VARCHAR(200) NOT NULL,
    employee_email VARCHAR(255) NOT NULL,
    position VARCHAR(200) NOT NULL,
    department VARCHAR(100) NOT NULL,
    manager_id VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    orientation_date DATE,
    buddy_id VARCHAR(100),
    hr_coordinator_id VARCHAR(100),
    it_coordinator_id VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    salary DECIMAL(12,2),
    office_location VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Onboarding checklist table
CREATE TABLE IF NOT EXISTS onboarding_checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    onboarding_id UUID NOT NULL REFERENCES employee_onboarding(id) ON DELETE CASCADE,
    step VARCHAR(100) NOT NULL,
    description TEXT,
    assigned_to VARCHAR(100),
    due_date DATE,
    completed BOOLEAN DEFAULT false,
    completed_by VARCHAR(100),
    completed_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(onboarding_id, step)
);

-- Onboarding documents table
CREATE TABLE IF NOT EXISTS onboarding_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    onboarding_id UUID NOT NULL REFERENCES employee_onboarding(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_url TEXT,
    file_size INTEGER,
    mime_type VARCHAR(100),
    uploaded_by VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP WITH TIME ZONE,
    expiry_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Equipment assignment table
CREATE TABLE IF NOT EXISTS onboarding_equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    onboarding_id UUID NOT NULL REFERENCES employee_onboarding(id) ON DELETE CASCADE,
    equipment_type VARCHAR(100) NOT NULL,
    asset_tag VARCHAR(100),
    serial_number VARCHAR(200),
    model VARCHAR(200),
    manufacturer VARCHAR(200),
    assigned_date DATE NOT NULL,
    assigned_by VARCHAR(100) NOT NULL,
    return_date DATE,
    returned_by VARCHAR(100),
    condition VARCHAR(50) DEFAULT 'new',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Training schedule table
CREATE TABLE IF NOT EXISTS onboarding_training (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    onboarding_id UUID NOT NULL REFERENCES employee_onboarding(id) ON DELETE CASCADE,
    training_name VARCHAR(200) NOT NULL,
    training_type VARCHAR(100),
    trainer VARCHAR(200),
    scheduled_date DATE NOT NULL,
    completed_date DATE,
    duration_hours DECIMAL(5,2),
    location VARCHAR(200),
    completed BOOLEAN DEFAULT false,
    score DECIMAL(5,2),
    certification_issued BOOLEAN DEFAULT false,
    certificate_number VARCHAR(100),
    expiry_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Access provisioning table
CREATE TABLE IF NOT EXISTS onboarding_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    onboarding_id UUID NOT NULL REFERENCES employee_onboarding(id) ON DELETE CASCADE,
    system_name VARCHAR(200) NOT NULL,
    access_type VARCHAR(100) NOT NULL,
    username VARCHAR(200),
    access_level VARCHAR(100),
    granted_date DATE,
    granted_by VARCHAR(100),
    revoked_date DATE,
    revoked_by VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Onboarding feedback table
CREATE TABLE IF NOT EXISTS onboarding_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    onboarding_id UUID NOT NULL REFERENCES employee_onboarding(id) ON DELETE CASCADE,
    feedback_type VARCHAR(100) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    submitted_by VARCHAR(100) NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response TEXT,
    responded_by VARCHAR(100),
    responded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_employee_onboarding_status ON employee_onboarding(status);
CREATE INDEX idx_employee_onboarding_start_date ON employee_onboarding(start_date);
CREATE INDEX idx_employee_onboarding_department ON employee_onboarding(department);
CREATE INDEX idx_employee_onboarding_manager_id ON employee_onboarding(manager_id);
CREATE INDEX idx_onboarding_checklist_onboarding_id ON onboarding_checklist(onboarding_id);
CREATE INDEX idx_onboarding_checklist_completed ON onboarding_checklist(completed);
CREATE INDEX idx_onboarding_checklist_due_date ON onboarding_checklist(due_date);
CREATE INDEX idx_onboarding_documents_onboarding_id ON onboarding_documents(onboarding_id);
CREATE INDEX idx_onboarding_equipment_onboarding_id ON onboarding_equipment(onboarding_id);
CREATE INDEX idx_onboarding_training_onboarding_id ON onboarding_training(onboarding_id);
CREATE INDEX idx_onboarding_training_scheduled_date ON onboarding_training(scheduled_date);
CREATE INDEX idx_onboarding_access_onboarding_id ON onboarding_access(onboarding_id);
CREATE INDEX idx_onboarding_feedback_onboarding_id ON onboarding_feedback(onboarding_id);

-- Add comments
COMMENT ON TABLE employee_onboarding IS 'Main table for employee onboarding processes';
COMMENT ON TABLE onboarding_checklist IS 'Checklist items for each onboarding process';
COMMENT ON TABLE onboarding_documents IS 'Documents uploaded during onboarding';
COMMENT ON TABLE onboarding_equipment IS 'Equipment assigned to new employees';
COMMENT ON TABLE onboarding_training IS 'Training schedule and completion tracking';
COMMENT ON TABLE onboarding_access IS 'System access provisioning tracking';
COMMENT ON TABLE onboarding_feedback IS 'Feedback from new employees about onboarding';