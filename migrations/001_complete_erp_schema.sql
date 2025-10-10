-- WeatherCraft ERP Complete Database Schema
-- Phase 1: Core Business Workflows

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- LEAD MANAGEMENT SYSTEM
-- ============================================================================

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Contact Information
    company_name VARCHAR(255),
    contact_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    mobile VARCHAR(20),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    location GEOMETRY(POINT, 4326),
    
    -- Lead Details
    source VARCHAR(50), -- website, referral, cold-call, trade-show, etc.
    source_details JSONB,
    lead_type VARCHAR(50), -- residential, commercial, industrial
    project_type VARCHAR(100), -- roof-replacement, repair, maintenance, new-construction
    urgency VARCHAR(20), -- immediate, 30-days, 60-days, planning
    estimated_value DECIMAL(12,2),
    
    -- Scoring and Classification
    lead_score INTEGER DEFAULT 0,
    lead_grade CHAR(1), -- A, B, C, D, F
    temperature VARCHAR(20), -- hot, warm, cold
    
    -- Assignment and Status
    status VARCHAR(50) DEFAULT 'new', -- new, contacted, qualified, proposal, won, lost
    assigned_to UUID REFERENCES users(id),
    assigned_at TIMESTAMPTZ,
    
    -- Conversion Tracking
    converted_to_customer BOOLEAN DEFAULT FALSE,
    customer_id UUID REFERENCES customers(id),
    converted_at TIMESTAMPTZ,
    lost_reason VARCHAR(255),
    competitor VARCHAR(255),
    
    -- Follow-up
    next_follow_up TIMESTAMPTZ,
    follow_up_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    
    -- Search
    search_vector tsvector,
    
    CONSTRAINT valid_lead_grade CHECK (lead_grade IN ('A', 'B', 'C', 'D', 'F'))
);

-- Lead Activities/Interactions
CREATE TABLE IF NOT EXISTS lead_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- call, email, meeting, site-visit, proposal-sent
    activity_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_minutes INTEGER,
    outcome VARCHAR(100),
    notes TEXT,
    next_action VARCHAR(255),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead Documents
CREATE TABLE IF NOT EXISTS lead_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    document_type VARCHAR(50),
    document_name VARCHAR(255),
    file_path VARCHAR(500),
    file_size INTEGER,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- COMPLETE ESTIMATION SYSTEM
-- ============================================================================

CREATE TABLE IF NOT EXISTS estimates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    estimate_number VARCHAR(20) UNIQUE NOT NULL,
    version INTEGER DEFAULT 1,
    parent_estimate_id UUID REFERENCES estimates(id), -- For versioning
    
    -- Customer/Lead Reference
    customer_id UUID REFERENCES customers(id),
    lead_id UUID REFERENCES leads(id),
    job_id UUID REFERENCES jobs(id),
    
    -- Project Details
    project_name VARCHAR(255),
    project_address VARCHAR(500),
    project_type VARCHAR(100),
    
    -- Estimate Details
    status VARCHAR(50) DEFAULT 'draft', -- draft, sent, viewed, approved, rejected, expired
    valid_until DATE,
    
    -- Pricing
    subtotal DECIMAL(12,2) DEFAULT 0,
    tax_rate DECIMAL(5,3) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Margins
    total_cost DECIMAL(12,2) DEFAULT 0,
    gross_profit DECIMAL(12,2) DEFAULT 0,
    gross_margin_percent DECIMAL(5,2) DEFAULT 0,
    
    -- Terms
    payment_terms VARCHAR(100),
    warranty_terms TEXT,
    scope_of_work TEXT,
    exclusions TEXT,
    notes TEXT,
    internal_notes TEXT,
    
    -- Approval
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    approval_notes TEXT,
    
    -- Conversion
    converted_to_job BOOLEAN DEFAULT FALSE,
    converted_at TIMESTAMPTZ,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    sent_at TIMESTAMPTZ,
    viewed_at TIMESTAMPTZ,
    
    CONSTRAINT valid_discount CHECK (discount_percent >= 0 AND discount_percent <= 100)
);

-- Estimate Line Items
CREATE TABLE IF NOT EXISTS estimate_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    estimate_id UUID NOT NULL REFERENCES estimates(id) ON DELETE CASCADE,
    
    -- Item Details
    item_order INTEGER NOT NULL,
    item_type VARCHAR(50), -- material, labor, equipment, subcontractor, other
    category VARCHAR(100),
    
    -- Description
    item_code VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Quantities and Pricing
    quantity DECIMAL(12,3) NOT NULL DEFAULT 1,
    unit_of_measure VARCHAR(20),
    unit_cost DECIMAL(12,4),
    unit_price DECIMAL(12,4) NOT NULL,
    
    -- Calculations
    total_cost DECIMAL(12,2),
    total_price DECIMAL(12,2),
    markup_percent DECIMAL(5,2),
    
    -- Optional/Alternative
    is_optional BOOLEAN DEFAULT FALSE,
    is_selected BOOLEAN DEFAULT TRUE,
    
    -- Tax
    taxable BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Estimate Templates
CREATE TABLE IF NOT EXISTS estimate_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(255) NOT NULL,
    template_type VARCHAR(50),
    description TEXT,
    
    -- Default Values
    default_payment_terms VARCHAR(100),
    default_warranty_terms TEXT,
    default_scope TEXT,
    default_exclusions TEXT,
    
    -- Markup Rules
    material_markup_percent DECIMAL(5,2),
    labor_markup_percent DECIMAL(5,2),
    subcontractor_markup_percent DECIMAL(5,2),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Template Items
CREATE TABLE IF NOT EXISTS estimate_template_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES estimate_templates(id) ON DELETE CASCADE,
    
    item_order INTEGER NOT NULL,
    item_type VARCHAR(50),
    category VARCHAR(100),
    item_code VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    default_quantity DECIMAL(12,3),
    unit_of_measure VARCHAR(20),
    unit_cost DECIMAL(12,4),
    unit_price DECIMAL(12,4),
    
    is_optional BOOLEAN DEFAULT FALSE,
    taxable BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ENHANCED JOB MANAGEMENT
-- ============================================================================

-- Job Phases (SD/DD/CD)
CREATE TABLE IF NOT EXISTS job_phases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    phase_type VARCHAR(20) NOT NULL, -- SD, DD, CD, closeout
    phase_name VARCHAR(100),
    
    -- Timeline
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,
    
    -- Progress
    percent_complete DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'not_started',
    
    -- Budget
    budgeted_amount DECIMAL(12,2),
    actual_amount DECIMAL(12,2),
    
    -- Deliverables
    deliverables JSONB,
    
    -- Sign-offs
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_phase CHECK (phase_type IN ('SD', 'DD', 'CD', 'closeout'))
);

-- Job Tasks
CREATE TABLE IF NOT EXISTS job_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES job_phases(id),
    
    task_name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50),
    
    -- Assignment
    assigned_to UUID REFERENCES users(id),
    assigned_crew_id UUID REFERENCES crews(id),
    
    -- Timeline
    planned_start TIMESTAMPTZ,
    planned_end TIMESTAMPTZ,
    actual_start TIMESTAMPTZ,
    actual_end TIMESTAMPTZ,
    duration_hours DECIMAL(8,2),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'normal',
    percent_complete DECIMAL(5,2) DEFAULT 0,
    
    -- Dependencies
    depends_on UUID REFERENCES job_tasks(id),
    
    -- Checklist
    checklist_items JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Job Documents
CREATE TABLE IF NOT EXISTS job_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES job_phases(id),
    
    document_type VARCHAR(50), -- contract, permit, inspection, photo, plan, etc.
    document_name VARCHAR(255),
    description TEXT,
    
    file_path VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- Versioning
    version INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- For photos
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    taken_at TIMESTAMPTZ
);

-- Job Notes/History
CREATE TABLE IF NOT EXISTS job_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    
    note_type VARCHAR(50), -- general, safety, quality, customer, internal
    note_text TEXT NOT NULL,
    
    is_pinned BOOLEAN DEFAULT FALSE,
    is_customer_visible BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Job Costs
CREATE TABLE IF NOT EXISTS job_costs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    phase_id UUID REFERENCES job_phases(id),
    
    cost_type VARCHAR(50), -- material, labor, equipment, subcontractor, other
    description VARCHAR(255),
    
    -- Reference
    purchase_order_id UUID REFERENCES purchase_orders(id),
    invoice_id UUID REFERENCES vendor_invoices(id),
    time_entry_id UUID REFERENCES time_entries(id),
    
    -- Amount
    quantity DECIMAL(12,3),
    unit_cost DECIMAL(12,4),
    total_cost DECIMAL(12,2),
    
    -- Accounting
    cost_code VARCHAR(50),
    is_billable BOOLEAN DEFAULT TRUE,
    
    incurred_date DATE,
    entered_at TIMESTAMPTZ DEFAULT NOW(),
    entered_by UUID REFERENCES users(id)
);

-- Change Orders
CREATE TABLE IF NOT EXISTS change_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    change_order_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Details
    title VARCHAR(255),
    description TEXT,
    reason VARCHAR(100), -- customer-request, unforeseen-condition, design-change, etc.
    
    -- Pricing
    amount DECIMAL(12,2),
    cost_impact DECIMAL(12,2),
    margin_impact DECIMAL(12,2),
    
    -- Schedule Impact
    schedule_impact_days INTEGER,
    
    -- Approval
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected
    customer_approved BOOLEAN DEFAULT FALSE,
    customer_approved_at TIMESTAMPTZ,
    internal_approved_by UUID REFERENCES users(id),
    internal_approved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Lead Indexes
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_assigned_to ON leads(assigned_to);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_leads_next_follow_up ON leads(next_follow_up);
CREATE INDEX idx_leads_search ON leads USING gin(search_vector);

-- Estimate Indexes
CREATE INDEX idx_estimates_customer ON estimates(customer_id);
CREATE INDEX idx_estimates_status ON estimates(status);
CREATE INDEX idx_estimates_created_at ON estimates(created_at DESC);
CREATE INDEX idx_estimate_items_estimate ON estimate_items(estimate_id);

-- Job Indexes
CREATE INDEX idx_job_phases_job ON job_phases(job_id);
CREATE INDEX idx_job_tasks_job ON job_tasks(job_id);
CREATE INDEX idx_job_tasks_assigned ON job_tasks(assigned_to);
CREATE INDEX idx_job_tasks_status ON job_tasks(status);
CREATE INDEX idx_job_documents_job ON job_documents(job_id);
CREATE INDEX idx_job_costs_job ON job_costs(job_id);
CREATE INDEX idx_change_orders_job ON change_orders(job_id);

-- ============================================================================
-- TRIGGERS FOR AUTOMATION
-- ============================================================================

-- Update search vectors
CREATE OR REPLACE FUNCTION update_lead_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', coalesce(NEW.company_name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.contact_name, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.email, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(NEW.city, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_lead_search_vector_trigger
    BEFORE INSERT OR UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_lead_search_vector();

-- Auto-generate lead numbers
CREATE OR REPLACE FUNCTION generate_lead_number() RETURNS trigger AS $$
BEGIN
    IF NEW.lead_number IS NULL THEN
        NEW.lead_number := 'L-' || TO_CHAR(NOW(), 'YYYY') || '-' || LPAD(nextval('lead_number_seq')::text, 5, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE IF NOT EXISTS lead_number_seq START 1;

CREATE TRIGGER generate_lead_number_trigger
    BEFORE INSERT ON leads
    FOR EACH ROW
    EXECUTE FUNCTION generate_lead_number();

-- Auto-generate estimate numbers
CREATE OR REPLACE FUNCTION generate_estimate_number() RETURNS trigger AS $$
BEGIN
    IF NEW.estimate_number IS NULL THEN
        NEW.estimate_number := 'EST-' || TO_CHAR(NOW(), 'YYYY') || '-' || LPAD(nextval('estimate_number_seq')::text, 5, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE IF NOT EXISTS estimate_number_seq START 1;

CREATE TRIGGER generate_estimate_number_trigger
    BEFORE INSERT ON estimates
    FOR EACH ROW
    EXECUTE FUNCTION generate_estimate_number();

-- Calculate estimate totals
CREATE OR REPLACE FUNCTION calculate_estimate_totals() RETURNS trigger AS $$
DECLARE
    v_subtotal DECIMAL(12,2);
    v_total_cost DECIMAL(12,2);
BEGIN
    -- Calculate subtotal from line items
    SELECT 
        COALESCE(SUM(total_price), 0),
        COALESCE(SUM(total_cost), 0)
    INTO v_subtotal, v_total_cost
    FROM estimate_items
    WHERE estimate_id = NEW.estimate_id AND is_selected = TRUE;
    
    -- Update estimate totals
    UPDATE estimates
    SET 
        subtotal = v_subtotal,
        total_cost = v_total_cost,
        tax_amount = v_subtotal * (tax_rate / 100),
        discount_amount = v_subtotal * (discount_percent / 100),
        total_amount = v_subtotal + (v_subtotal * (tax_rate / 100)) - (v_subtotal * (discount_percent / 100)),
        gross_profit = v_subtotal - v_total_cost,
        gross_margin_percent = CASE 
            WHEN v_subtotal > 0 THEN ((v_subtotal - v_total_cost) / v_subtotal) * 100
            ELSE 0
        END,
        updated_at = NOW()
    WHERE id = NEW.estimate_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_estimate_totals_trigger
    AFTER INSERT OR UPDATE OR DELETE ON estimate_items
    FOR EACH ROW
    EXECUTE FUNCTION calculate_estimate_totals();

-- Update timestamps
CREATE OR REPLACE FUNCTION update_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_estimates_updated_at BEFORE UPDATE ON estimates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_job_phases_updated_at BEFORE UPDATE ON job_phases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_job_tasks_updated_at BEFORE UPDATE ON job_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();