-- =============================================================================
-- RELATIONSHIP AWARENESS SYSTEM TABLES
-- Makes the ERP intricately aware of how all entities connect
-- =============================================================================

-- Track entity relationships and their state
CREATE TABLE IF NOT EXISTS entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,  -- customers, jobs, employees, etc
    entity_id UUID NOT NULL,
    relationship_graph JSONB,  -- Complete graph of all connections
    parent_entities JSONB,     -- All parent relationships
    child_entities JSONB,      -- All child relationships
    computed_fields JSONB,     -- Cached computed field values
    last_computed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_type, entity_id)
);

CREATE INDEX idx_entity_relationships_type_id ON entity_relationships(entity_type, entity_id);
CREATE INDEX idx_entity_relationships_graph ON entity_relationships USING GIN(relationship_graph);

-- Track relationship changes for audit trail
CREATE TABLE IF NOT EXISTS relationship_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,  -- link_created, link_removed, relationship_updated
    related_entity_type VARCHAR(50),
    related_entity_id UUID,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_relationship_audit_entity ON relationship_audit_log(entity_type, entity_id);
CREATE INDEX idx_relationship_audit_created ON relationship_audit_log(created_at DESC);

-- =============================================================================
-- JUNCTION TABLES FOR MANY-TO-MANY RELATIONSHIPS
-- =============================================================================

-- Jobs ↔ Employees (crew assignments)
CREATE TABLE IF NOT EXISTS job_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    role VARCHAR(50),  -- foreman, crew_member, specialist
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, removed
    assigned_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(job_id, employee_id)
);

CREATE INDEX idx_job_assignments_job ON job_assignments(job_id);
CREATE INDEX idx_job_assignments_employee ON job_assignments(employee_id);

-- Jobs ↔ Equipment (equipment used on job)
CREATE TABLE IF NOT EXISTS job_equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'reserved',  -- reserved, in_use, returned
    hours_used DECIMAL(10,2) DEFAULT 0,
    reserved_at TIMESTAMP DEFAULT NOW(),
    returned_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_job_equipment_job ON job_equipment(job_id);
CREATE INDEX idx_job_equipment_equipment ON job_equipment(equipment_id);

-- Jobs ↔ Inventory (materials used on job)
CREATE TABLE IF NOT EXISTS job_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    inventory_item_id UUID NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    quantity DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2),
    allocated_at TIMESTAMP DEFAULT NOW(),
    used_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_job_materials_job ON job_materials(job_id);
CREATE INDEX idx_job_materials_inventory ON job_materials(inventory_item_id);

-- Estimate ↔ Line Items
CREATE TABLE IF NOT EXISTS estimate_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estimate_id UUID NOT NULL REFERENCES estimates(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    category VARCHAR(50),  -- labor, materials, equipment
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_estimate_line_items_estimate ON estimate_line_items(estimate_id);

-- Invoice ↔ Line Items
CREATE TABLE IF NOT EXISTS invoice_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    category VARCHAR(50),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_invoice_line_items_invoice ON invoice_line_items(invoice_id);

-- =============================================================================
-- SUPPORTING TABLES
-- =============================================================================

-- Payments (Customer → Invoice)
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id) ON DELETE SET NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),  -- credit_card, check, cash, ach
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    reference_number VARCHAR(100),
    notes TEXT,
    tenant_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_payments_customer ON payments(customer_id);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);

-- Communications (Customer relationship)
CREATE TABLE IF NOT EXISTS communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    communication_type VARCHAR(50),  -- email, phone, sms, in_person
    subject TEXT,
    content TEXT,
    direction VARCHAR(20),  -- inbound, outbound
    status VARCHAR(20),  -- sent, delivered, read, bounced
    occurred_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,
    tenant_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_communications_customer ON communications(customer_id);
CREATE INDEX idx_communications_occurred ON communications(occurred_at DESC);

-- HR Records (Employee ↔ HR)
CREATE TABLE IF NOT EXISTS hr_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    hire_date DATE,
    termination_date DATE,
    employment_status VARCHAR(50),  -- active, terminated, on_leave
    employee_type VARCHAR(50),  -- full_time, part_time, contractor
    salary DECIMAL(10,2),
    pay_frequency VARCHAR(20),  -- hourly, salary, per_job
    benefits_eligible BOOLEAN DEFAULT false,
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(employee_id)
);

CREATE INDEX idx_hr_records_employee ON hr_records(employee_id);

-- Certifications (Employee has many)
CREATE TABLE IF NOT EXISTS certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    certification_name VARCHAR(200) NOT NULL,
    issuing_organization VARCHAR(200),
    issue_date DATE,
    expiration_date DATE,
    certification_number VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',  -- active, expired, suspended
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_certifications_employee ON certifications(employee_id);
CREATE INDEX idx_certifications_expiration ON certifications(expiration_date);

-- Training Records (Employee has many)
CREATE TABLE IF NOT EXISTS training_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    training_name VARCHAR(200) NOT NULL,
    training_type VARCHAR(50),  -- safety, technical, compliance
    completion_date DATE,
    instructor VARCHAR(200),
    hours DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'completed',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_training_records_employee ON training_records(employee_id);

-- Equipment Maintenance
CREATE TABLE IF NOT EXISTS equipment_maintenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    maintenance_type VARCHAR(50),  -- routine, repair, inspection
    performed_by UUID,
    maintenance_date DATE NOT NULL,
    hours_at_maintenance DECIMAL(10,2),
    cost DECIMAL(10,2),
    description TEXT,
    next_maintenance_due DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_equipment_maintenance_equipment ON equipment_maintenance(equipment_id);
CREATE INDEX idx_equipment_maintenance_due ON equipment_maintenance(next_maintenance_due);

-- Change Orders (Job has many)
CREATE TABLE IF NOT EXISTS change_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    change_order_number VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected
    requested_by VARCHAR(200),
    requested_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by UUID,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_change_orders_job ON change_orders(job_id);

-- =============================================================================
-- RELATIONSHIP AWARENESS VIEWS
-- =============================================================================

-- Complete customer view with all relationships
CREATE OR REPLACE VIEW customer_complete_view AS
SELECT
    c.*,
    COUNT(DISTINCT j.id) as total_jobs,
    COUNT(DISTINCT e.id) as total_estimates,
    COUNT(DISTINCT i.id) as total_invoices,
    COALESCE(SUM(i.total_amount), 0) as lifetime_value,
    COALESCE(SUM(p.amount), 0) as total_payments,
    COALESCE(SUM(i.total_amount) - SUM(p.amount), 0) as balance_due,
    MAX(j.completed_at) as last_job_date,
    COUNT(DISTINCT comm.id) as total_communications
FROM customers c
LEFT JOIN jobs j ON c.id = j.customer_id
LEFT JOIN estimates e ON c.id = e.customer_id
LEFT JOIN invoices i ON c.id = i.customer_id
LEFT JOIN payments p ON c.id = p.customer_id
LEFT JOIN communications comm ON c.id = comm.customer_id
GROUP BY c.id;

-- Complete job view with all relationships
CREATE OR REPLACE VIEW job_complete_view AS
SELECT
    j.*,
    c.name as customer_name,
    COUNT(DISTINCT ja.employee_id) as crew_size,
    COUNT(DISTINCT je.equipment_id) as equipment_count,
    COUNT(DISTINCT jm.inventory_item_id) as material_count,
    COALESCE(SUM(t.hours), 0) as total_labor_hours,
    COALESCE(SUM(jm.quantity * jm.unit_cost), 0) as total_material_cost
FROM jobs j
LEFT JOIN customers c ON j.customer_id = c.id
LEFT JOIN job_assignments ja ON j.id = ja.job_id
LEFT JOIN job_equipment je ON j.id = je.job_id
LEFT JOIN job_materials jm ON j.id = jm.job_id
LEFT JOIN timesheets t ON j.id = t.job_id
GROUP BY j.id, c.name;

-- Complete employee view with all relationships
CREATE OR REPLACE VIEW employee_complete_view AS
SELECT
    e.*,
    hr.employment_status,
    hr.employee_type,
    hr.hire_date,
    COUNT(DISTINCT ja.job_id) as total_jobs_assigned,
    COUNT(DISTINCT c.id) as total_certifications,
    COUNT(DISTINCT tr.id) as total_training_completed,
    COALESCE(SUM(t.hours), 0) as total_hours_worked
FROM employees e
LEFT JOIN hr_records hr ON e.id = hr.employee_id
LEFT JOIN job_assignments ja ON e.id = ja.employee_id
LEFT JOIN certifications c ON e.id = c.employee_id
LEFT JOIN training_records tr ON e.id = tr.employee_id
LEFT JOIN timesheets t ON e.id = t.employee_id
GROUP BY e.id, hr.employment_status, hr.employee_type, hr.hire_date;

-- Grant access
GRANT SELECT ON customer_complete_view TO postgres;
GRANT SELECT ON job_complete_view TO postgres;
GRANT SELECT ON employee_complete_view TO postgres;

COMMENT ON TABLE entity_relationships IS 'Tracks complete relationship graph for all entities - enables deep intricate awareness';
COMMENT ON TABLE job_assignments IS 'Links employees to jobs - tracks crew assignments';
COMMENT ON TABLE job_equipment IS 'Links equipment to jobs - tracks equipment usage';
COMMENT ON TABLE job_materials IS 'Links inventory to jobs - tracks material consumption';
