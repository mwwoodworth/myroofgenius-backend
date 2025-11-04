-- Employee Scheduling Tables - Task 46
-- Complete scheduling and shift management

-- Shift templates table
CREATE TABLE IF NOT EXISTS shift_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    shift_type VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    break_duration_minutes INTEGER DEFAULT 0,
    description TEXT,
    required_staff INTEGER DEFAULT 1,
    skills_required JSONB DEFAULT '[]',
    location VARCHAR(200),
    department VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Employee schedules table
CREATE TABLE IF NOT EXISTS employee_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(100) NOT NULL,
    schedule_date DATE NOT NULL,
    shift_start TIMESTAMP WITH TIME ZONE NOT NULL,
    shift_end TIMESTAMP WITH TIME ZONE NOT NULL,
    shift_type VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    position VARCHAR(200),
    break_duration_minutes INTEGER DEFAULT 0,
    template_id UUID REFERENCES shift_templates(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    actual_clock_in TIMESTAMP WITH TIME ZONE,
    actual_clock_out TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    CONSTRAINT unique_employee_schedule UNIQUE(employee_id, schedule_date, shift_start)
);

-- Schedule requests table
CREATE TABLE IF NOT EXISTS schedule_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(100) NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    reason TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Employee availability table
CREATE TABLE IF NOT EXISTS employee_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(100) NOT NULL,
    day_of_week VARCHAR(20) NOT NULL,
    available_start TIME NOT NULL,
    available_end TIME NOT NULL,
    is_available BOOLEAN DEFAULT true,
    preferred BOOLEAN DEFAULT false,
    notes TEXT,
    effective_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_availability UNIQUE(employee_id, day_of_week, effective_date)
);

-- Shift swaps table
CREATE TABLE IF NOT EXISTS shift_swaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_employee_id VARCHAR(100) NOT NULL,
    to_employee_id VARCHAR(100) NOT NULL,
    schedule_id UUID REFERENCES employee_schedules(id) ON DELETE CASCADE,
    reciprocal_schedule_id UUID REFERENCES employee_schedules(id) ON DELETE SET NULL,
    swap_date DATE NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_shift_templates_department ON shift_templates(department);
CREATE INDEX idx_shift_templates_shift_type ON shift_templates(shift_type);
CREATE INDEX idx_employee_schedules_employee_id ON employee_schedules(employee_id);
CREATE INDEX idx_employee_schedules_schedule_date ON employee_schedules(schedule_date);
CREATE INDEX idx_employee_schedules_department ON employee_schedules(department);
CREATE INDEX idx_employee_schedules_status ON employee_schedules(status);
CREATE INDEX idx_schedule_requests_employee_id ON schedule_requests(employee_id);
CREATE INDEX idx_schedule_requests_status ON schedule_requests(status);
CREATE INDEX idx_employee_availability_employee_id ON employee_availability(employee_id);
CREATE INDEX idx_shift_swaps_from_employee ON shift_swaps(from_employee_id);
CREATE INDEX idx_shift_swaps_to_employee ON shift_swaps(to_employee_id);
CREATE INDEX idx_shift_swaps_status ON shift_swaps(status);

-- Add comments
COMMENT ON TABLE shift_templates IS 'Reusable shift templates for scheduling';
COMMENT ON TABLE employee_schedules IS 'Employee work schedules and time tracking';
COMMENT ON TABLE schedule_requests IS 'Employee scheduling change requests';
COMMENT ON TABLE employee_availability IS 'Employee availability preferences';
COMMENT ON TABLE shift_swaps IS 'Shift swap requests between employees';