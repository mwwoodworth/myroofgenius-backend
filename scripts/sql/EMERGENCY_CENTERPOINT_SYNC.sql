-- EMERGENCY: Complete Centerpoint data sync
-- Must capture ALL data before losing access
-- Over 1 million data points

-- Create landing tables for all Centerpoint data

-- Centerpoint files and attachments
CREATE TABLE IF NOT EXISTS centerpoint_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    file_name VARCHAR(500) NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT,
    file_url TEXT,
    file_data BYTEA, -- Store actual file content
    entity_type VARCHAR(100), -- customer, job, invoice, etc.
    entity_id VARCHAR(255),
    uploaded_date TIMESTAMPTZ,
    uploaded_by VARCHAR(255),
    tags JSONB,
    metadata JSONB,
    is_synced BOOLEAN DEFAULT false,
    synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Centerpoint service tickets
CREATE TABLE IF NOT EXISTS centerpoint_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    ticket_number VARCHAR(100),
    customer_id VARCHAR(255),
    job_id VARCHAR(255),
    title VARCHAR(500),
    description TEXT,
    priority VARCHAR(50),
    status VARCHAR(100),
    category VARCHAR(100),
    assigned_to VARCHAR(255),
    created_date TIMESTAMPTZ,
    updated_date TIMESTAMPTZ,
    resolved_date TIMESTAMPTZ,
    resolution TEXT,
    time_spent_hours DECIMAL(10,2),
    attachments JSONB,
    comments JSONB,
    custom_fields JSONB,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Centerpoint invoices with all details
CREATE TABLE IF NOT EXISTS centerpoint_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    invoice_number VARCHAR(100),
    customer_id VARCHAR(255),
    job_id VARCHAR(255),
    invoice_date DATE,
    due_date DATE,
    subtotal DECIMAL(12,2),
    tax_amount DECIMAL(12,2),
    total_amount DECIMAL(12,2),
    paid_amount DECIMAL(12,2),
    balance_due DECIMAL(12,2),
    status VARCHAR(50),
    payment_terms VARCHAR(100),
    line_items JSONB,
    payments JSONB,
    notes TEXT,
    attachments JSONB,
    custom_fields JSONB,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Centerpoint estimates
CREATE TABLE IF NOT EXISTS centerpoint_estimates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    estimate_number VARCHAR(100),
    customer_id VARCHAR(255),
    estimate_date DATE,
    expiry_date DATE,
    total_amount DECIMAL(12,2),
    status VARCHAR(50),
    converted_to_job BOOLEAN DEFAULT false,
    job_id VARCHAR(255),
    line_items JSONB,
    sections JSONB,
    terms TEXT,
    notes TEXT,
    attachments JSONB,
    custom_fields JSONB,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Centerpoint job history
CREATE TABLE IF NOT EXISTS centerpoint_job_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    job_number VARCHAR(100),
    customer_id VARCHAR(255),
    job_type VARCHAR(100),
    status VARCHAR(100),
    start_date DATE,
    end_date DATE,
    address TEXT,
    description TEXT,
    crew_assigned JSONB,
    materials_used JSONB,
    total_cost DECIMAL(12,2),
    total_revenue DECIMAL(12,2),
    profit_margin DECIMAL(5,2),
    hours_worked DECIMAL(10,2),
    weather_conditions JSONB,
    photos JSONB,
    documents JSONB,
    notes TEXT,
    quality_score INTEGER,
    customer_feedback TEXT,
    warranty_info JSONB,
    custom_fields JSONB,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Centerpoint communications log
CREATE TABLE IF NOT EXISTS centerpoint_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255),
    job_id VARCHAR(255),
    communication_type VARCHAR(50), -- email, phone, sms, meeting
    direction VARCHAR(20), -- inbound, outbound
    subject VARCHAR(500),
    content TEXT,
    from_address VARCHAR(255),
    to_address VARCHAR(255),
    date_time TIMESTAMPTZ,
    duration_minutes INTEGER,
    attachments JSONB,
    tags JSONB,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Centerpoint equipment/assets
CREATE TABLE IF NOT EXISTS centerpoint_equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    equipment_name VARCHAR(255),
    equipment_type VARCHAR(100),
    serial_number VARCHAR(255),
    purchase_date DATE,
    purchase_price DECIMAL(12,2),
    current_value DECIMAL(12,2),
    status VARCHAR(50),
    location VARCHAR(255),
    assigned_to VARCHAR(255),
    maintenance_schedule JSONB,
    maintenance_history JSONB,
    specifications JSONB,
    documents JSONB,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Centerpoint inventory transactions
CREATE TABLE IF NOT EXISTS centerpoint_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    item_name VARCHAR(255),
    item_code VARCHAR(100),
    category VARCHAR(100),
    quantity_on_hand DECIMAL(12,2),
    unit_of_measure VARCHAR(50),
    unit_cost DECIMAL(12,2),
    total_value DECIMAL(12,2),
    reorder_point DECIMAL(12,2),
    supplier VARCHAR(255),
    location VARCHAR(255),
    transactions JSONB,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Centerpoint employee records
CREATE TABLE IF NOT EXISTS centerpoint_employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    employee_number VARCHAR(100),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(100),
    department VARCHAR(100),
    hire_date DATE,
    hourly_rate DECIMAL(10,2),
    skills JSONB,
    certifications JSONB,
    emergency_contact JSONB,
    documents JSONB,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Centerpoint photos/images
CREATE TABLE IF NOT EXISTS centerpoint_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    centerpoint_id VARCHAR(255) UNIQUE NOT NULL,
    photo_url TEXT,
    photo_data BYTEA, -- Store actual image
    thumbnail_data BYTEA,
    entity_type VARCHAR(100),
    entity_id VARCHAR(255),
    caption TEXT,
    taken_date TIMESTAMPTZ,
    taken_by VARCHAR(255),
    location JSONB,
    tags JSONB,
    metadata JSONB,
    is_synced BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create sync status tracking
CREATE TABLE IF NOT EXISTS centerpoint_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL,
    total_records INTEGER DEFAULT 0,
    synced_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,
    last_sync_at TIMESTAMPTZ,
    last_error TEXT,
    sync_status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type)
);

-- Initialize sync status for all entities
INSERT INTO centerpoint_sync_status (entity_type, sync_status) VALUES
('customers', 'pending'),
('jobs', 'pending'),
('invoices', 'pending'),
('estimates', 'pending'),
('tickets', 'pending'),
('files', 'pending'),
('photos', 'pending'),
('communications', 'pending'),
('equipment', 'pending'),
('inventory', 'pending'),
('employees', 'pending')
ON CONFLICT (entity_type) DO NOTHING;

-- Create indexes for performance
CREATE INDEX idx_cp_files_entity ON centerpoint_files(entity_type, entity_id);
CREATE INDEX idx_cp_files_synced ON centerpoint_files(is_synced);
CREATE INDEX idx_cp_tickets_customer ON centerpoint_tickets(customer_id);
CREATE INDEX idx_cp_tickets_status ON centerpoint_tickets(status);
CREATE INDEX idx_cp_invoices_customer ON centerpoint_invoices(customer_id);
CREATE INDEX idx_cp_invoices_status ON centerpoint_invoices(status);
CREATE INDEX idx_cp_estimates_customer ON centerpoint_estimates(customer_id);
CREATE INDEX idx_cp_jobs_customer ON centerpoint_job_history(customer_id);
CREATE INDEX idx_cp_photos_entity ON centerpoint_photos(entity_type, entity_id);
CREATE INDEX idx_cp_communications_customer ON centerpoint_communications(customer_id);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Summary
SELECT 
    'Centerpoint Sync Tables' as component,
    COUNT(*) as tables_created
FROM information_schema.tables
WHERE table_name LIKE 'centerpoint_%'
AND table_schema = 'public';