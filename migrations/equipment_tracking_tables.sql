-- Equipment Tracking Tables
-- Task 41: Equipment tracking implementation

-- Equipment master table
CREATE TABLE IF NOT EXISTS equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    equipment_type VARCHAR(30) NOT NULL, -- vehicle, heavy_machinery, power_tool, hand_tool, safety_equipment, computer, communication, measurement, other
    status VARCHAR(20) DEFAULT 'available', -- available, in_use, maintenance, repair, reserved, retired, lost, stolen
    condition VARCHAR(20) DEFAULT 'good', -- excellent, good, fair, poor, unusable
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    year INT CHECK (year >= 1900 AND year <= 2100),
    purchase_date DATE,
    purchase_price DECIMAL(12,2),
    current_value DECIMAL(12,2),
    disposal_date DATE,
    disposal_value DECIMAL(12,2),
    location_id UUID REFERENCES inventory_locations(id),
    assigned_to VARCHAR(100),
    fuel_type VARCHAR(20), -- gasoline, diesel, electric, hybrid, propane, natural_gas, not_applicable
    capacity VARCHAR(100), -- Load capacity, passenger capacity, etc.
    license_plate VARCHAR(20),
    vin VARCHAR(50),
    insurance_policy VARCHAR(100),
    insurance_expiry DATE,
    registration_number VARCHAR(100),
    registration_expiry DATE,
    last_maintenance_date DATE,
    last_inspection_date DATE,
    specifications JSONB,
    image_url TEXT,
    qr_code VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment checkouts
CREATE TABLE IF NOT EXISTS equipment_checkouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    checked_out_to VARCHAR(100) NOT NULL,
    checkout_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expected_return_date DATE,
    return_time TIMESTAMPTZ,
    job_id UUID REFERENCES jobs(id),
    project_name VARCHAR(200),
    purpose TEXT,
    checkout_condition VARCHAR(20), -- excellent, good, fair, poor
    return_condition VARCHAR(20),
    meter_reading_out DECIMAL(10,2),
    meter_reading_return DECIMAL(10,2),
    fuel_level_out DECIMAL(5,2),
    fuel_level_return DECIMAL(5,2),
    damages TEXT,
    status VARCHAR(20) DEFAULT 'checked_out', -- checked_out, returned, overdue, damaged, lost
    notes TEXT,
    return_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Maintenance schedules
CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    maintenance_type VARCHAR(20) NOT NULL, -- preventive, corrective, inspection, calibration, cleaning, emergency
    scheduled_date DATE NOT NULL,
    frequency_days INT, -- For recurring maintenance
    last_performed DATE,
    next_due_date DATE,
    description TEXT NOT NULL,
    estimated_duration_hours DECIMAL(5,2),
    estimated_cost DECIMAL(10,2),
    actual_date DATE,
    actual_cost DECIMAL(10,2),
    assigned_technician VARCHAR(100),
    parts_required JSONB,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, in_progress, completed, overdue, cancelled
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Maintenance records
CREATE TABLE IF NOT EXISTS maintenance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    schedule_id UUID REFERENCES maintenance_schedules(id),
    maintenance_type VARCHAR(20) NOT NULL,
    performed_date DATE NOT NULL,
    performed_by VARCHAR(100) NOT NULL,
    duration_hours DECIMAL(5,2) NOT NULL,
    cost DECIMAL(10,2) NOT NULL,
    parts_used JSONB,
    labor_cost DECIMAL(10,2),
    parts_cost DECIMAL(10,2),
    issues_found TEXT,
    actions_taken TEXT NOT NULL,
    recommendations TEXT,
    next_maintenance_date DATE,
    warranty_claim BOOLEAN DEFAULT false,
    invoice_number VARCHAR(100),
    vendor VARCHAR(100),
    odometer_reading DECIMAL(10,2),
    hours_reading DECIMAL(10,2),
    attachments JSONB,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment inspections
CREATE TABLE IF NOT EXISTS equipment_inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    inspection_date DATE NOT NULL,
    inspector VARCHAR(100) NOT NULL,
    inspection_type VARCHAR(50) NOT NULL, -- safety, compliance, condition, pre-use, post-use, annual
    checklist_items JSONB NOT NULL, -- Array of {item, status, notes}
    overall_condition VARCHAR(20) NOT NULL, -- excellent, good, fair, poor, unusable
    pass_fail BOOLEAN NOT NULL,
    issues_found JSONB,
    corrective_actions JSONB,
    recommendations TEXT,
    next_inspection_date DATE,
    certification_number VARCHAR(100),
    regulatory_compliance BOOLEAN DEFAULT true,
    photos JSONB,
    signature VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment usage logs
CREATE TABLE IF NOT EXISTS equipment_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    checkout_id UUID REFERENCES equipment_checkouts(id),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    operator VARCHAR(100) NOT NULL,
    job_id UUID REFERENCES jobs(id),
    location VARCHAR(200),
    hours_used DECIMAL(8,2) NOT NULL,
    meter_start DECIMAL(10,2),
    meter_end DECIMAL(10,2),
    fuel_used DECIMAL(8,2),
    distance_traveled DECIMAL(10,2),
    idle_time DECIMAL(8,2),
    productive_time DECIMAL(8,2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment costs
CREATE TABLE IF NOT EXISTS equipment_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    cost_type VARCHAR(30) NOT NULL, -- maintenance, repair, fuel, insurance, registration, depreciation, other
    amount DECIMAL(12,2) NOT NULL,
    date DATE NOT NULL,
    description TEXT NOT NULL,
    vendor VARCHAR(100),
    invoice_number VARCHAR(100),
    job_id UUID REFERENCES jobs(id),
    is_billable BOOLEAN DEFAULT false,
    approved_by VARCHAR(100),
    payment_status VARCHAR(20) DEFAULT 'pending', -- pending, paid, cancelled
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment certifications
CREATE TABLE IF NOT EXISTS equipment_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    certification_type VARCHAR(100) NOT NULL,
    certification_number VARCHAR(100),
    issuing_authority VARCHAR(100) NOT NULL,
    issue_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    inspection_required BOOLEAN DEFAULT true,
    document_url TEXT,
    reminder_days INT DEFAULT 30,
    status VARCHAR(20) DEFAULT 'valid', -- valid, expiring, expired, suspended
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment operators
CREATE TABLE IF NOT EXISTS equipment_operators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    operator_name VARCHAR(100) NOT NULL,
    employee_id VARCHAR(50),
    certification_required BOOLEAN DEFAULT false,
    certification_number VARCHAR(100),
    certification_expiry DATE,
    training_date DATE,
    authorized_from DATE NOT NULL,
    authorized_until DATE,
    restrictions TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(equipment_id, operator_name)
);

-- Equipment GPS tracking
CREATE TABLE IF NOT EXISTS equipment_gps_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    altitude DECIMAL(8,2),
    speed DECIMAL(6,2),
    heading DECIMAL(5,2),
    accuracy DECIMAL(6,2),
    satellite_count INT,
    battery_level DECIMAL(5,2),
    engine_status VARCHAR(20),
    address TEXT,
    geofence_status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment warranties
CREATE TABLE IF NOT EXISTS equipment_warranties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    warranty_type VARCHAR(50) NOT NULL, -- manufacturer, extended, parts, labor
    provider VARCHAR(100) NOT NULL,
    warranty_number VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    coverage_details TEXT,
    max_claim_amount DECIMAL(12,2),
    claims_made DECIMAL(12,2) DEFAULT 0,
    contact_info TEXT,
    document_url TEXT,
    status VARCHAR(20) DEFAULT 'active', -- active, expired, void
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment attachments/accessories
CREATE TABLE IF NOT EXISTS equipment_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    attachment_name VARCHAR(100) NOT NULL,
    attachment_type VARCHAR(50),
    serial_number VARCHAR(100),
    value DECIMAL(10,2),
    is_attached BOOLEAN DEFAULT false,
    compatibility_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Equipment activity log
CREATE TABLE IF NOT EXISTS equipment_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- checkout, return, maintenance, inspection, repair, relocation, status_change
    performed_by VARCHAR(100),
    description TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    activity_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_equipment_code ON equipment(equipment_code);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);
CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment(equipment_type);
CREATE INDEX IF NOT EXISTS idx_equipment_location ON equipment(location_id);
CREATE INDEX IF NOT EXISTS idx_equipment_assigned_to ON equipment(assigned_to);
CREATE INDEX IF NOT EXISTS idx_checkouts_equipment_id ON equipment_checkouts(equipment_id);
CREATE INDEX IF NOT EXISTS idx_checkouts_checked_out_to ON equipment_checkouts(checked_out_to);
CREATE INDEX IF NOT EXISTS idx_checkouts_status ON equipment_checkouts(status);
CREATE INDEX IF NOT EXISTS idx_checkouts_checkout_time ON equipment_checkouts(checkout_time);
CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_equipment_id ON maintenance_schedules(equipment_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_scheduled_date ON maintenance_schedules(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_maintenance_schedules_status ON maintenance_schedules(status);
CREATE INDEX IF NOT EXISTS idx_maintenance_records_equipment_id ON maintenance_records(equipment_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_records_performed_date ON maintenance_records(performed_date);
CREATE INDEX IF NOT EXISTS idx_inspections_equipment_id ON equipment_inspections(equipment_id);
CREATE INDEX IF NOT EXISTS idx_inspections_inspection_date ON equipment_inspections(inspection_date);
CREATE INDEX IF NOT EXISTS idx_usage_logs_equipment_id ON equipment_usage_logs(equipment_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_start_time ON equipment_usage_logs(start_time);
CREATE INDEX IF NOT EXISTS idx_costs_equipment_id ON equipment_costs(equipment_id);
CREATE INDEX IF NOT EXISTS idx_costs_date ON equipment_costs(date);
CREATE INDEX IF NOT EXISTS idx_gps_tracking_equipment_id ON equipment_gps_tracking(equipment_id);
CREATE INDEX IF NOT EXISTS idx_gps_tracking_timestamp ON equipment_gps_tracking(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_log_equipment_id ON equipment_activity_log(equipment_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_activity_date ON equipment_activity_log(activity_date);

-- Functions
CREATE OR REPLACE FUNCTION calculate_equipment_age(purchase_date DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(CURRENT_DATE, purchase_date));
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_depreciation(purchase_price DECIMAL, purchase_date DATE, useful_life_years INT)
RETURNS DECIMAL AS $$
DECLARE
    age_years INT;
    annual_depreciation DECIMAL;
    current_value DECIMAL;
BEGIN
    age_years := calculate_equipment_age(purchase_date);
    IF age_years >= useful_life_years THEN
        RETURN 0;
    END IF;
    annual_depreciation := purchase_price / useful_life_years;
    current_value := purchase_price - (annual_depreciation * age_years);
    RETURN GREATEST(current_value, 0);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_equipment_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Log status change
    IF OLD.status != NEW.status THEN
        INSERT INTO equipment_activity_log (
            equipment_id, activity_type, description,
            old_value, new_value
        ) VALUES (
            NEW.id, 'status_change',
            'Equipment status changed',
            OLD.status, NEW.status
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_equipment_status_change
AFTER UPDATE ON equipment
FOR EACH ROW
EXECUTE FUNCTION update_equipment_status();

-- Update triggers
CREATE TRIGGER set_equipment_updated_at
BEFORE UPDATE ON equipment
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_equipment_checkouts_updated_at
BEFORE UPDATE ON equipment_checkouts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_maintenance_schedules_updated_at
BEFORE UPDATE ON maintenance_schedules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_equipment_certifications_updated_at
BEFORE UPDATE ON equipment_certifications
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_equipment_operators_updated_at
BEFORE UPDATE ON equipment_operators
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_equipment_warranties_updated_at
BEFORE UPDATE ON equipment_warranties
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();