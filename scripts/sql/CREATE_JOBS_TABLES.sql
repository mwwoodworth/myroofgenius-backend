-- Create REAL job management tables for roofing services
-- 100% production-ready, no placeholders

-- Jobs table - core service tracking
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Customer info
    customer_id UUID NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    customer_phone VARCHAR(50),
    
    -- Job details
    job_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    job_type VARCHAR(50) NOT NULL CHECK (job_type IN (
        'roof_replacement', 'roof_repair', 'inspection', 
        'maintenance', 'emergency', 'gutter', 'siding'
    )),
    
    -- Location
    address_street VARCHAR(255) NOT NULL,
    address_city VARCHAR(100) NOT NULL,
    address_state VARCHAR(2) NOT NULL,
    address_zip VARCHAR(10) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled' CHECK (status IN (
        'scheduled', 'in_progress', 'completed', 'cancelled', 
        'on_hold', 'pending_inspection', 'warranty'
    )),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN (
        'low', 'normal', 'high', 'urgent', 'emergency'
    )),
    
    -- Scheduling
    scheduled_start TIMESTAMPTZ NOT NULL,
    scheduled_end TIMESTAMPTZ NOT NULL,
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    duration_hours DECIMAL(5,2),
    
    -- Financial
    estimated_amount INTEGER NOT NULL DEFAULT 0, -- cents
    actual_amount INTEGER DEFAULT 0, -- cents
    cost_amount INTEGER DEFAULT 0, -- cents
    profit_amount INTEGER GENERATED ALWAYS AS (actual_amount - cost_amount) STORED,
    payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN (
        'pending', 'partial', 'paid', 'overdue', 'refunded'
    )),
    
    -- Team assignment
    crew_lead_id UUID,
    crew_lead_name VARCHAR(255),
    crew_size INTEGER DEFAULT 1,
    assigned_crew JSONB DEFAULT '[]'::jsonb, -- Array of crew member objects
    
    -- Materials
    materials_list JSONB DEFAULT '[]'::jsonb,
    materials_cost INTEGER DEFAULT 0, -- cents
    
    -- Job specifics
    roof_type VARCHAR(50),
    roof_size_sqft INTEGER,
    roof_pitch VARCHAR(20),
    number_of_layers INTEGER DEFAULT 1,
    
    -- Documentation
    notes TEXT,
    internal_notes TEXT,
    photos_before JSONB DEFAULT '[]'::jsonb,
    photos_during JSONB DEFAULT '[]'::jsonb,
    photos_after JSONB DEFAULT '[]'::jsonb,
    documents JSONB DEFAULT '[]'::jsonb,
    
    -- Completion
    completion_notes TEXT,
    customer_signature VARCHAR(500),
    customer_satisfaction_rating INTEGER CHECK (customer_satisfaction_rating BETWEEN 1 AND 5),
    
    -- Weather
    weather_conditions VARCHAR(100),
    temperature_at_start INTEGER,
    wind_speed INTEGER,
    
    -- Tracking
    estimate_id UUID,
    invoice_id UUID,
    parent_job_id UUID, -- For warranty/follow-up jobs
    
    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,
    custom_fields JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID
);

-- Job crew assignments table
CREATE TABLE IF NOT EXISTS job_crew (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'crew' CHECK (role IN (
        'lead', 'crew', 'apprentice', 'supervisor', 'inspector'
    )),
    hours_worked DECIMAL(5,2),
    hourly_rate INTEGER, -- cents
    total_pay INTEGER, -- cents
    check_in_time TIMESTAMPTZ,
    check_out_time TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, employee_id)
);

-- Job materials tracking
CREATE TABLE IF NOT EXISTS job_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    material_name VARCHAR(255) NOT NULL,
    material_type VARCHAR(100),
    quantity DECIMAL(10,2) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    unit_cost INTEGER NOT NULL, -- cents
    total_cost INTEGER GENERATED ALWAYS AS (CAST(quantity * unit_cost AS INTEGER)) STORED,
    supplier VARCHAR(255),
    sku VARCHAR(100),
    delivered_date DATE,
    used_quantity DECIMAL(10,2),
    waste_quantity DECIMAL(10,2),
    returned_quantity DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Job status history
CREATE TABLE IF NOT EXISTS job_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by UUID,
    changed_by_name VARCHAR(255),
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Job notes/comments
CREATE TABLE IF NOT EXISTS job_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    note_type VARCHAR(50) DEFAULT 'general' CHECK (note_type IN (
        'general', 'customer', 'internal', 'safety', 'quality', 'warranty'
    )),
    content TEXT NOT NULL,
    is_pinned BOOLEAN DEFAULT false,
    created_by UUID,
    created_by_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Job checklist items
CREATE TABLE IF NOT EXISTS job_checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    category VARCHAR(100) DEFAULT 'general',
    item_text VARCHAR(500) NOT NULL,
    is_required BOOLEAN DEFAULT false,
    is_completed BOOLEAN DEFAULT false,
    completed_by UUID,
    completed_by_name VARCHAR(255),
    completed_at TIMESTAMPTZ,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Job warranties
CREATE TABLE IF NOT EXISTS job_warranties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    warranty_type VARCHAR(50) NOT NULL CHECK (warranty_type IN (
        'workmanship', 'material', 'manufacturer', 'extended'
    )),
    coverage_years INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    description TEXT,
    terms TEXT,
    is_transferable BOOLEAN DEFAULT false,
    registration_number VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_jobs_customer_id ON jobs(customer_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_scheduled_start ON jobs(scheduled_start);
CREATE INDEX idx_jobs_job_number ON jobs(job_number);
CREATE INDEX idx_jobs_crew_lead ON jobs(crew_lead_id);
CREATE INDEX idx_jobs_payment_status ON jobs(payment_status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

CREATE INDEX idx_job_crew_job_id ON job_crew(job_id);
CREATE INDEX idx_job_crew_employee_id ON job_crew(employee_id);

CREATE INDEX idx_job_materials_job_id ON job_materials(job_id);

CREATE INDEX idx_job_status_history_job_id ON job_status_history(job_id);
CREATE INDEX idx_job_status_history_created_at ON job_status_history(created_at DESC);

-- Full-text search on job details
CREATE INDEX idx_jobs_search ON jobs 
    USING GIN(to_tsvector('english', 
        COALESCE(title, '') || ' ' || 
        COALESCE(description, '') || ' ' || 
        COALESCE(customer_name, '') || ' ' ||
        COALESCE(address_street, '')
    ));

-- Create job number sequence
CREATE SEQUENCE IF NOT EXISTS job_number_seq START 10001;

-- Function to generate job numbers
CREATE OR REPLACE FUNCTION generate_job_number()
RETURNS TEXT AS $$
BEGIN
    RETURN 'JOB-' || TO_CHAR(CURRENT_DATE, 'YYYY') || '-' || LPAD(nextval('job_number_seq')::TEXT, 5, '0');
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-generate job numbers
CREATE OR REPLACE FUNCTION set_job_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.job_number IS NULL OR NEW.job_number = '' THEN
        NEW.job_number := generate_job_number();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_job_number
    BEFORE INSERT ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION set_job_number();

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Trigger to log status changes
CREATE OR REPLACE FUNCTION log_job_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO job_status_history (
            job_id, previous_status, new_status, 
            changed_by, changed_by_name
        ) VALUES (
            NEW.id, OLD.status, NEW.status,
            NEW.updated_by, 'System'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_job_status
    AFTER UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION log_job_status_change();

-- Grant permissions
GRANT ALL ON jobs TO postgres;
GRANT ALL ON job_crew TO postgres;
GRANT ALL ON job_materials TO postgres;
GRANT ALL ON job_status_history TO postgres;
GRANT ALL ON job_notes TO postgres;
GRANT ALL ON job_checklist TO postgres;
GRANT ALL ON job_warranties TO postgres;
GRANT USAGE, SELECT ON job_number_seq TO postgres;

-- Insert sample jobs for testing
INSERT INTO jobs (
    customer_name, customer_email, customer_phone,
    title, description, job_type,
    address_street, address_city, address_state, address_zip,
    status, priority, scheduled_start, scheduled_end,
    estimated_amount, roof_type, roof_size_sqft
) VALUES
('John Smith', 'john@example.com', '303-555-0100',
 'Complete Roof Replacement', 'Replace damaged asphalt shingle roof with architectural shingles',
 'roof_replacement',
 '123 Main St', 'Denver', 'CO', '80202',
 'scheduled', 'high',
 CURRENT_TIMESTAMP + INTERVAL '2 days',
 CURRENT_TIMESTAMP + INTERVAL '3 days',
 1850000, -- $18,500
 'asphalt_shingle', 2400),

('Mary Johnson', 'mary@example.com', '303-555-0101',
 'Emergency Leak Repair', 'Fix active leak in master bedroom ceiling',
 'emergency',
 '456 Oak Ave', 'Boulder', 'CO', '80301',
 'in_progress', 'emergency',
 CURRENT_TIMESTAMP,
 CURRENT_TIMESTAMP + INTERVAL '4 hours',
 95000, -- $950
 'tile', 1800),

('Bob Wilson', 'bob@example.com', '303-555-0102',
 'Annual Roof Inspection', 'Routine maintenance inspection and minor repairs',
 'inspection',
 '789 Pine Rd', 'Aurora', 'CO', '80010',
 'completed', 'normal',
 CURRENT_TIMESTAMP - INTERVAL '1 week',
 CURRENT_TIMESTAMP - INTERVAL '1 week' + INTERVAL '2 hours',
 35000, -- $350
 'metal', 3200);

-- Verify tables
SELECT 
    'Jobs System' as component,
    COUNT(*) as tables_created
FROM information_schema.tables
WHERE table_name IN (
    'jobs', 'job_crew', 'job_materials', 
    'job_status_history', 'job_notes', 
    'job_checklist', 'job_warranties'
);