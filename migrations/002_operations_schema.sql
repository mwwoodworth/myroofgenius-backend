-- WeatherCraft ERP Operations Management Schema
-- Phase 2: Operations Management

-- ============================================================================
-- CREW MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS crews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crew_name VARCHAR(100) NOT NULL,
    crew_type VARCHAR(50), -- roofing, repair, maintenance, inspection
    crew_code VARCHAR(20) UNIQUE,
    
    -- Lead/Foreman
    foreman_id UUID REFERENCES users(id),
    
    -- Capabilities
    max_jobs_per_day INTEGER DEFAULT 1,
    specialties TEXT[],
    certifications TEXT[],
    
    -- Location
    home_location_id UUID REFERENCES locations(id),
    current_location GEOMETRY(POINT, 4326),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(50) DEFAULT 'available', -- available, working, break, off-duty
    
    -- Performance
    efficiency_rating DECIMAL(3,2),
    safety_rating DECIMAL(3,2),
    quality_rating DECIMAL(3,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crew_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crew_id UUID REFERENCES crews(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Role
    role VARCHAR(50), -- foreman, roofer, helper, apprentice
    
    -- Employment
    employee_id VARCHAR(50),
    hire_date DATE,
    
    -- Pay
    pay_type VARCHAR(20), -- hourly, salary, piece-rate
    pay_rate DECIMAL(10,2),
    overtime_rate DECIMAL(10,2),
    
    -- Skills & Certs
    skills TEXT[],
    certifications JSONB,
    license_number VARCHAR(50),
    license_expiry DATE,
    
    -- Safety
    safety_training_date DATE,
    drug_test_date DATE,
    background_check_date DATE,
    
    -- Availability
    is_active BOOLEAN DEFAULT TRUE,
    available_days INTEGER DEFAULT 63, -- Bitmap for days (Mon=1, Tue=2, etc.)
    
    -- Performance
    total_hours_worked DECIMAL(10,2) DEFAULT 0,
    jobs_completed INTEGER DEFAULT 0,
    performance_score DECIMAL(3,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SCHEDULING & DISPATCH
-- ============================================================================

CREATE TABLE IF NOT EXISTS schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What
    schedulable_type VARCHAR(50) NOT NULL, -- job, task, inspection, service
    schedulable_id UUID NOT NULL,
    
    -- Who
    crew_id UUID REFERENCES crews(id),
    assigned_users UUID[],
    
    -- When
    scheduled_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    duration_hours DECIMAL(5,2),
    
    -- Recurrence
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule JSONB, -- RRULE format
    recurrence_end_date DATE,
    parent_schedule_id UUID REFERENCES schedules(id),
    
    -- Status
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, dispatched, en-route, on-site, completed, cancelled
    
    -- Priority
    priority VARCHAR(20) DEFAULT 'normal', -- emergency, high, normal, low
    
    -- Location
    location_name VARCHAR(255),
    address VARCHAR(500),
    location GEOMETRY(POINT, 4326),
    
    -- Route
    route_order INTEGER,
    travel_time_minutes INTEGER,
    distance_miles DECIMAL(6,2),
    
    -- Weather
    weather_dependent BOOLEAN DEFAULT TRUE,
    weather_status VARCHAR(50),
    
    -- Notes
    dispatch_notes TEXT,
    crew_notes TEXT,
    
    -- Completion
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    completed_by UUID REFERENCES users(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    CONSTRAINT valid_schedule_times CHECK (end_time > start_time)
);

-- Dispatch Queue
CREATE TABLE IF NOT EXISTS dispatch_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schedule_id UUID REFERENCES schedules(id),
    
    -- Dispatch Details
    dispatch_priority INTEGER DEFAULT 100,
    dispatch_status VARCHAR(50) DEFAULT 'pending',
    dispatched_at TIMESTAMPTZ,
    dispatched_by UUID REFERENCES users(id),
    
    -- Notifications
    crew_notified BOOLEAN DEFAULT FALSE,
    customer_notified BOOLEAN DEFAULT FALSE,
    
    -- ETA
    estimated_arrival TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- FIELD OPERATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS daily_field_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_date DATE NOT NULL,
    job_id UUID NOT NULL REFERENCES jobs(id),
    crew_id UUID REFERENCES crews(id),
    
    -- Weather
    weather_conditions VARCHAR(100),
    temperature_high INTEGER,
    temperature_low INTEGER,
    precipitation BOOLEAN DEFAULT FALSE,
    wind_speed INTEGER,
    
    -- Work Performed
    work_description TEXT,
    areas_completed TEXT,
    percent_complete DECIMAL(5,2),
    
    -- Materials Used
    materials_used JSONB,
    
    -- Equipment
    equipment_used JSONB,
    equipment_issues TEXT,
    
    -- Safety
    safety_incidents INTEGER DEFAULT 0,
    safety_notes TEXT,
    toolbox_talk_topic VARCHAR(255),
    
    -- Quality
    quality_issues TEXT,
    inspections_completed BOOLEAN DEFAULT FALSE,
    
    -- Photos
    photo_count INTEGER DEFAULT 0,
    
    -- Sign-off
    foreman_signature TEXT,
    signed_at TIMESTAMPTZ,
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft',
    submitted_at TIMESTAMPTZ,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Time Tracking
CREATE TABLE IF NOT EXISTS time_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Who
    user_id UUID NOT NULL REFERENCES users(id),
    crew_id UUID REFERENCES crews(id),
    
    -- What
    job_id UUID REFERENCES jobs(id),
    task_id UUID REFERENCES job_tasks(id),
    
    -- When
    entry_date DATE NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    break_minutes INTEGER DEFAULT 0,
    total_hours DECIMAL(5,2),
    
    -- Type
    work_type VARCHAR(50), -- regular, overtime, double-time, holiday
    billable BOOLEAN DEFAULT TRUE,
    
    -- Location
    clock_in_location GEOMETRY(POINT, 4326),
    clock_out_location GEOMETRY(POINT, 4326),
    
    -- Notes
    description TEXT,
    
    -- Approval
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Safety Incidents
CREATE TABLE IF NOT EXISTS safety_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_date TIMESTAMPTZ NOT NULL,
    job_id UUID REFERENCES jobs(id),
    
    -- People Involved
    reported_by UUID NOT NULL REFERENCES users(id),
    involved_users UUID[],
    crew_id UUID REFERENCES crews(id),
    
    -- Incident Details
    incident_type VARCHAR(100), -- injury, near-miss, property-damage, equipment-failure
    severity VARCHAR(50), -- minor, moderate, severe, critical
    description TEXT NOT NULL,
    
    -- Injury Details
    injury_type VARCHAR(100),
    body_part VARCHAR(100),
    medical_treatment BOOLEAN DEFAULT FALSE,
    lost_time BOOLEAN DEFAULT FALSE,
    
    -- Investigation
    root_cause TEXT,
    corrective_actions TEXT,
    preventive_measures TEXT,
    
    -- Reporting
    osha_recordable BOOLEAN DEFAULT FALSE,
    insurance_claim_number VARCHAR(50),
    
    -- Status
    status VARCHAR(50) DEFAULT 'open',
    closed_at TIMESTAMPTZ,
    closed_by UUID REFERENCES users(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quality Control Checklists
CREATE TABLE IF NOT EXISTS quality_checklists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    phase_id UUID REFERENCES job_phases(id),
    
    -- Checklist Details
    checklist_type VARCHAR(50), -- pre-job, in-progress, final, warranty
    checklist_date DATE NOT NULL,
    
    -- Inspector
    inspector_id UUID NOT NULL REFERENCES users(id),
    
    -- Items
    checklist_items JSONB NOT NULL,
    /* Format:
    [
        {
            "item": "Underlayment properly installed",
            "status": "pass/fail/na",
            "notes": "...",
            "photo_ids": []
        }
    ]
    */
    
    -- Results
    passed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    total_items INTEGER DEFAULT 0,
    overall_status VARCHAR(20), -- pass, fail, conditional
    
    -- Follow-up
    requires_reinspection BOOLEAN DEFAULT FALSE,
    reinspection_date DATE,
    corrective_actions TEXT,
    
    -- Sign-off
    customer_signature TEXT,
    customer_signed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Job Site Photos
CREATE TABLE IF NOT EXISTS job_photos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id),
    
    -- Context
    photo_type VARCHAR(50), -- before, during, after, issue, inspection
    phase VARCHAR(50),
    
    -- File
    file_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    file_size INTEGER,
    
    -- Metadata
    description TEXT,
    tags TEXT[],
    
    -- Location
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    
    -- Timestamp
    taken_at TIMESTAMPTZ NOT NULL,
    taken_by UUID REFERENCES users(id),
    
    -- Organization
    is_customer_visible BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment Tracking
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Details
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100), -- vehicle, tool, safety, machinery
    make VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    year INTEGER,
    
    -- Ownership
    ownership_type VARCHAR(50), -- owned, leased, rented
    purchase_date DATE,
    purchase_price DECIMAL(12,2),
    
    -- Location
    current_location VARCHAR(255),
    assigned_to_crew UUID REFERENCES crews(id),
    assigned_to_user UUID REFERENCES users(id),
    
    -- Maintenance
    last_service_date DATE,
    next_service_date DATE,
    service_interval_days INTEGER,
    service_interval_hours DECIMAL(10,2),
    current_hours DECIMAL(10,2),
    
    -- Status
    status VARCHAR(50) DEFAULT 'available', -- available, in-use, maintenance, repair, retired
    condition VARCHAR(50) DEFAULT 'good', -- excellent, good, fair, poor
    
    -- Insurance
    insurance_policy VARCHAR(100),
    insurance_expiry DATE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment Usage Log
CREATE TABLE IF NOT EXISTS equipment_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id UUID NOT NULL REFERENCES equipment(id),
    
    -- Usage
    job_id UUID REFERENCES jobs(id),
    used_by UUID REFERENCES users(id),
    crew_id UUID REFERENCES crews(id),
    
    -- Time
    checkout_time TIMESTAMPTZ NOT NULL,
    checkin_time TIMESTAMPTZ,
    usage_hours DECIMAL(8,2),
    
    -- Meter Reading
    start_hours DECIMAL(10,2),
    end_hours DECIMAL(10,2),
    
    -- Condition
    checkout_condition VARCHAR(50),
    checkin_condition VARCHAR(50),
    damage_noted TEXT,
    
    -- Notes
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Crew Indexes
CREATE INDEX idx_crews_active ON crews(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_crew_members_crew ON crew_members(crew_id);
CREATE INDEX idx_crew_members_user ON crew_members(user_id);

-- Schedule Indexes
CREATE INDEX idx_schedules_date ON schedules(scheduled_date);
CREATE INDEX idx_schedules_crew ON schedules(crew_id);
CREATE INDEX idx_schedules_status ON schedules(status);
CREATE INDEX idx_schedules_schedulable ON schedules(schedulable_type, schedulable_id);

-- Field Operations Indexes
CREATE INDEX idx_daily_reports_date ON daily_field_reports(report_date);
CREATE INDEX idx_daily_reports_job ON daily_field_reports(job_id);
CREATE INDEX idx_time_entries_user_date ON time_entries(user_id, entry_date);
CREATE INDEX idx_time_entries_job ON time_entries(job_id);
CREATE INDEX idx_job_photos_job ON job_photos(job_id);
CREATE INDEX idx_equipment_status ON equipment(status);
CREATE INDEX idx_equipment_usage_equipment ON equipment_usage(equipment_id);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Calculate time entry hours
CREATE OR REPLACE FUNCTION calculate_time_entry_hours() RETURNS trigger AS $$
BEGIN
    IF NEW.end_time IS NOT NULL AND NEW.start_time IS NOT NULL THEN
        NEW.total_hours := EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time)) / 3600.0 - (COALESCE(NEW.break_minutes, 0) / 60.0);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_time_entry_hours_trigger
    BEFORE INSERT OR UPDATE ON time_entries
    FOR EACH ROW
    EXECUTE FUNCTION calculate_time_entry_hours();

-- Update crew member stats
CREATE OR REPLACE FUNCTION update_crew_member_stats() RETURNS trigger AS $$
BEGIN
    IF NEW.status = 'approved' AND OLD.status != 'approved' THEN
        UPDATE crew_members
        SET 
            total_hours_worked = total_hours_worked + NEW.total_hours,
            updated_at = NOW()
        WHERE user_id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_crew_member_stats_trigger
    AFTER UPDATE ON time_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_crew_member_stats();

-- Auto-generate equipment numbers
CREATE OR REPLACE FUNCTION generate_equipment_number() RETURNS trigger AS $$
BEGIN
    IF NEW.equipment_number IS NULL THEN
        NEW.equipment_number := 'EQ-' || UPPER(SUBSTRING(NEW.type FROM 1 FOR 3)) || '-' || LPAD(nextval('equipment_number_seq')::text, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE IF NOT EXISTS equipment_number_seq START 1;

CREATE TRIGGER generate_equipment_number_trigger
    BEFORE INSERT ON equipment
    FOR EACH ROW
    EXECUTE FUNCTION generate_equipment_number();