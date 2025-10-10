-- HR Management Tables
-- Task 43: HR management implementation

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_code VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(30),
    department VARCHAR(50) NOT NULL, -- sales, operations, finance, hr, it, marketing, customer_service, warehouse, field_service, management
    position VARCHAR(100) NOT NULL,
    employment_type VARCHAR(20) NOT NULL, -- full_time, part_time, contract, intern, temporary, seasonal
    employment_status VARCHAR(20) DEFAULT 'active', -- active, on_leave, terminated, retired, suspended
    hire_date DATE NOT NULL,
    termination_date DATE,
    birth_date DATE,
    ssn_last4 VARCHAR(4),
    manager_id UUID REFERENCES employees(id),
    salary DECIMAL(12,2),
    hourly_rate DECIMAL(8,2),
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(30),
    emergency_contact_relationship VARCHAR(50),
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    work_location VARCHAR(100),
    remote_work BOOLEAN DEFAULT false,
    profile_photo_url TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payroll records
CREATE TABLE IF NOT EXISTS payroll (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_number VARCHAR(50) UNIQUE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id),
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    regular_hours DECIMAL(8,2) DEFAULT 0,
    overtime_hours DECIMAL(8,2) DEFAULT 0,
    holiday_hours DECIMAL(8,2) DEFAULT 0,
    sick_hours DECIMAL(8,2) DEFAULT 0,
    vacation_hours DECIMAL(8,2) DEFAULT 0,
    other_hours DECIMAL(8,2) DEFAULT 0,
    gross_pay DECIMAL(12,2) NOT NULL,
    deductions JSONB, -- {federal_tax: 100, state_tax: 50, etc}
    net_pay DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(30) DEFAULT 'direct_deposit', -- direct_deposit, check, cash
    payment_date DATE NOT NULL,
    bank_account_last4 VARCHAR(4),
    check_number VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, processed, paid, cancelled
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leave requests
CREATE TABLE IF NOT EXISTS leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_number VARCHAR(50) UNIQUE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id),
    leave_type VARCHAR(20) NOT NULL, -- vacation, sick, personal, maternity, paternity, bereavement, jury_duty, military, unpaid, sabbatical
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days INT NOT NULL,
    reason TEXT,
    supporting_docs JSONB, -- Array of document URLs
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, denied, cancelled, in_progress, completed
    approved_by VARCHAR(100),
    approval_date TIMESTAMPTZ,
    approval_notes TEXT,
    return_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leave entitlements
CREATE TABLE IF NOT EXISTS leave_entitlements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    year INT NOT NULL,
    leave_type VARCHAR(20) NOT NULL,
    days_entitled DECIMAL(5,2) NOT NULL,
    days_carried_forward DECIMAL(5,2) DEFAULT 0,
    days_used DECIMAL(5,2) DEFAULT 0,
    days_remaining DECIMAL(5,2) GENERATED ALWAYS AS (days_entitled + days_carried_forward - days_used) STORED,
    max_carryforward DECIMAL(5,2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(employee_id, year, leave_type)
);

-- Benefits enrollment
CREATE TABLE IF NOT EXISTS benefit_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    benefit_type VARCHAR(30) NOT NULL, -- health, dental, vision, life, disability, 401k, fsa, hsa, commuter, other
    plan_name VARCHAR(100) NOT NULL,
    provider VARCHAR(100),
    coverage_level VARCHAR(20) NOT NULL, -- self, spouse, family, self_plus_one
    effective_date DATE NOT NULL,
    termination_date DATE,
    employee_cost DECIMAL(10,2) NOT NULL,
    employer_cost DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(20) DEFAULT 'monthly', -- weekly, biweekly, monthly, annual
    dependents JSONB, -- Array of dependent information
    enrollment_status VARCHAR(20) DEFAULT 'active', -- active, pending, terminated, waived
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Time entries
CREATE TABLE IF NOT EXISTS time_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    work_date DATE NOT NULL,
    clock_in TIME NOT NULL,
    clock_out TIME,
    break_start TIME,
    break_end TIME,
    break_minutes INT DEFAULT 0,
    total_hours DECIMAL(5,2),
    overtime_hours DECIMAL(5,2) DEFAULT 0,
    project_id UUID,
    job_id UUID REFERENCES jobs(id),
    location VARCHAR(200),
    work_type VARCHAR(50), -- regular, overtime, training, meeting, travel
    billable BOOLEAN DEFAULT true,
    approved BOOLEAN DEFAULT false,
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(employee_id, work_date, clock_in)
);

-- Performance reviews
CREATE TABLE IF NOT EXISTS performance_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    reviewer_id UUID NOT NULL REFERENCES employees(id),
    review_type VARCHAR(20) NOT NULL, -- annual, quarterly, probation, promotion, improvement, exit
    review_period_start DATE NOT NULL,
    review_period_end DATE NOT NULL,
    overall_rating INT CHECK (overall_rating >= 1 AND overall_rating <= 5),
    ratings JSONB, -- {communication: 4, teamwork: 5, etc}
    strengths TEXT,
    improvements TEXT,
    goals JSONB, -- Array of goals
    accomplishments TEXT,
    comments TEXT,
    employee_comments TEXT,
    next_review_date DATE,
    salary_increase_percentage DECIMAL(5,2),
    bonus_amount DECIMAL(10,2),
    promotion_recommended BOOLEAN DEFAULT false,
    improvement_plan_required BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'draft', -- draft, submitted, acknowledged, disputed
    submitted_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Training records
CREATE TABLE IF NOT EXISTS training_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    training_name VARCHAR(200) NOT NULL,
    training_type VARCHAR(50) NOT NULL, -- online, classroom, on_the_job, conference, certification
    provider VARCHAR(100),
    description TEXT,
    start_date DATE NOT NULL,
    completion_date DATE,
    expiry_date DATE,
    duration_hours DECIMAL(6,2),
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, in_progress, completed, failed, cancelled
    score DECIMAL(5,2),
    passing_score DECIMAL(5,2),
    certificate_number VARCHAR(100),
    certificate_url TEXT,
    cost DECIMAL(10,2),
    reimbursable BOOLEAN DEFAULT false,
    reimbursement_amount DECIMAL(10,2),
    mandatory BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Employee documents
CREATE TABLE IF NOT EXISTS employee_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    document_type VARCHAR(50) NOT NULL, -- resume, contract, nda, id, tax_form, certification, review, warning, other
    document_name VARCHAR(200) NOT NULL,
    file_url TEXT NOT NULL,
    file_size INT,
    mime_type VARCHAR(100),
    description TEXT,
    valid_from DATE,
    valid_until DATE,
    is_confidential BOOLEAN DEFAULT false,
    uploaded_by VARCHAR(100),
    verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(100),
    verified_at TIMESTAMPTZ,
    tags JSONB, -- Array of tags
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Disciplinary actions
CREATE TABLE IF NOT EXISTS disciplinary_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    action_type VARCHAR(50) NOT NULL, -- verbal_warning, written_warning, suspension, termination, other
    incident_date DATE NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL, -- minor, moderate, major, critical
    issued_by UUID NOT NULL REFERENCES employees(id),
    witnessed_by VARCHAR(100),
    employee_response TEXT,
    corrective_actions TEXT,
    follow_up_date DATE,
    follow_up_notes TEXT,
    documents JSONB, -- Array of supporting document URLs
    status VARCHAR(20) DEFAULT 'active', -- active, resolved, appealed, overturned
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Employee compensation history
CREATE TABLE IF NOT EXISTS compensation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    effective_date DATE NOT NULL,
    salary DECIMAL(12,2),
    hourly_rate DECIMAL(8,2),
    bonus DECIMAL(10,2),
    commission_rate DECIMAL(5,2),
    change_type VARCHAR(50) NOT NULL, -- hire, raise, promotion, adjustment, bonus
    change_percentage DECIMAL(5,2),
    change_amount DECIMAL(10,2),
    reason TEXT,
    approved_by UUID REFERENCES employees(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Employee emergency contacts
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    contact_name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    phone_primary VARCHAR(30) NOT NULL,
    phone_secondary VARCHAR(30),
    email VARCHAR(255),
    address VARCHAR(500),
    is_primary BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Employee skills
CREATE TABLE IF NOT EXISTS employee_skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    skill_category VARCHAR(50) NOT NULL, -- technical, language, certification, software, management
    skill_name VARCHAR(100) NOT NULL,
    proficiency_level VARCHAR(20), -- beginner, intermediate, advanced, expert
    years_experience DECIMAL(4,1),
    last_used_date DATE,
    verified BOOLEAN DEFAULT false,
    verified_by UUID REFERENCES employees(id),
    verified_date DATE,
    certificate_number VARCHAR(100),
    expiry_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(employee_id, skill_name)
);

-- Organizational structure
CREATE TABLE IF NOT EXISTS org_structure (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id VARCHAR(50) UNIQUE NOT NULL,
    position_title VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    reports_to_position_id VARCHAR(50),
    level INT NOT NULL, -- 1=C-level, 2=VP, 3=Director, 4=Manager, 5=Individual
    headcount_budget INT,
    current_headcount INT DEFAULT 0,
    min_salary DECIMAL(12,2),
    max_salary DECIMAL(12,2),
    job_description TEXT,
    requirements TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- HR policies
CREATE TABLE IF NOT EXISTS hr_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_code VARCHAR(50) UNIQUE NOT NULL,
    policy_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL, -- conduct, leave, benefits, safety, compliance, other
    description TEXT,
    full_text TEXT,
    document_url TEXT,
    effective_date DATE NOT NULL,
    revision_date DATE,
    version VARCHAR(20),
    requires_acknowledgment BOOLEAN DEFAULT false,
    mandatory_review_days INT,
    owner VARCHAR(100),
    approved_by VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Policy acknowledgments
CREATE TABLE IF NOT EXISTS policy_acknowledgments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID NOT NULL REFERENCES hr_policies(id),
    employee_id UUID NOT NULL REFERENCES employees(id),
    acknowledged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(policy_id, employee_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);
CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(employment_status);
CREATE INDEX IF NOT EXISTS idx_employees_manager ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
CREATE INDEX IF NOT EXISTS idx_payroll_employee ON payroll(employee_id);
CREATE INDEX IF NOT EXISTS idx_payroll_period ON payroll(pay_period_start, pay_period_end);
CREATE INDEX IF NOT EXISTS idx_payroll_status ON payroll(status);
CREATE INDEX IF NOT EXISTS idx_leave_requests_employee ON leave_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_dates ON leave_requests(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status);
CREATE INDEX IF NOT EXISTS idx_time_entries_employee ON time_entries(employee_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_date ON time_entries(work_date);
CREATE INDEX IF NOT EXISTS idx_performance_reviews_employee ON performance_reviews(employee_id);
CREATE INDEX IF NOT EXISTS idx_performance_reviews_reviewer ON performance_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_training_employee ON training_records(employee_id);
CREATE INDEX IF NOT EXISTS idx_training_status ON training_records(status);
CREATE INDEX IF NOT EXISTS idx_benefits_employee ON benefit_enrollments(employee_id);
CREATE INDEX IF NOT EXISTS idx_benefits_effective ON benefit_enrollments(effective_date);

-- Functions
CREATE OR REPLACE FUNCTION calculate_tenure(hire_date DATE)
RETURNS INTERVAL AS $$
BEGIN
    RETURN AGE(CURRENT_DATE, hire_date);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_leave_balance(emp_id UUID, leave_type VARCHAR, year INT)
RETURNS DECIMAL AS $$
DECLARE
    entitlement DECIMAL;
    used DECIMAL;
BEGIN
    SELECT days_entitled + COALESCE(days_carried_forward, 0)
    INTO entitlement
    FROM leave_entitlements
    WHERE employee_id = emp_id
        AND leave_type = leave_type
        AND year = year;

    SELECT COALESCE(SUM(total_days), 0)
    INTO used
    FROM leave_requests
    WHERE employee_id = emp_id
        AND leave_type = leave_type
        AND status = 'approved'
        AND EXTRACT(YEAR FROM start_date) = year;

    RETURN COALESCE(entitlement, 0) - used;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER set_employees_updated_at
BEFORE UPDATE ON employees
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_payroll_updated_at
BEFORE UPDATE ON payroll
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_leave_requests_updated_at
BEFORE UPDATE ON leave_requests
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_leave_entitlements_updated_at
BEFORE UPDATE ON leave_entitlements
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_benefit_enrollments_updated_at
BEFORE UPDATE ON benefit_enrollments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_time_entries_updated_at
BEFORE UPDATE ON time_entries
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_performance_reviews_updated_at
BEFORE UPDATE ON performance_reviews
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_training_records_updated_at
BEFORE UPDATE ON training_records
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_employee_documents_updated_at
BEFORE UPDATE ON employee_documents
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_emergency_contacts_updated_at
BEFORE UPDATE ON emergency_contacts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_hr_policies_updated_at
BEFORE UPDATE ON hr_policies
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();