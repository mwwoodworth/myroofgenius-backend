-- WeatherCraft ERP Financial & Service Management Schema
-- Phase 4 & 5: Financial Management, Service & Warranty

-- ============================================================================
-- FINANCIAL MANAGEMENT
-- ============================================================================

-- Invoices
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Customer & Job
    customer_id UUID NOT NULL REFERENCES customers(id),
    job_id UUID REFERENCES jobs(id),
    estimate_id UUID REFERENCES estimates(id),
    
    -- Invoice Details
    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE,
    terms VARCHAR(50) DEFAULT 'Net 30',
    
    -- Billing Type
    invoice_type VARCHAR(50) DEFAULT 'standard', -- standard, progress, final, credit-memo
    progress_percentage DECIMAL(5,2), -- For progress billing
    
    -- Amounts
    subtotal DECIMAL(12,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(12,2) DEFAULT 0,
    retainage_amount DECIMAL(12,2) DEFAULT 0, -- Amount held back
    amount_paid DECIMAL(12,2) DEFAULT 0,
    balance_due DECIMAL(12,2) DEFAULT 0,
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- draft, sent, viewed, partial, paid, overdue, cancelled
    sent_date TIMESTAMPTZ,
    viewed_date TIMESTAMPTZ,
    paid_date DATE,
    
    -- Notes
    notes TEXT,
    internal_notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Invoice Line Items
CREATE TABLE IF NOT EXISTS invoice_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    
    -- Item Details
    line_number INTEGER NOT NULL,
    item_type VARCHAR(50), -- material, labor, equipment, other
    
    -- Description
    item_code VARCHAR(50),
    description TEXT NOT NULL,
    
    -- Quantities & Pricing
    quantity DECIMAL(12,3) DEFAULT 1,
    unit_of_measure VARCHAR(20),
    unit_price DECIMAL(12,4) NOT NULL,
    total_price DECIMAL(12,2),
    
    -- Tax
    taxable BOOLEAN DEFAULT TRUE,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Job Costing
    cost_code VARCHAR(50),
    phase_code VARCHAR(50),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Customer
    customer_id UUID NOT NULL REFERENCES customers(id),
    
    -- Payment Details
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount DECIMAL(12,2) NOT NULL,
    
    -- Payment Method
    payment_method VARCHAR(50) NOT NULL, -- credit-card, ach, check, cash, wire
    
    -- Payment Processing
    processor VARCHAR(50), -- stripe, square, manual
    transaction_id VARCHAR(100),
    processing_fee DECIMAL(12,2) DEFAULT 0,
    
    -- Check Details
    check_number VARCHAR(50),
    
    -- Credit Card Details (encrypted/tokenized)
    card_last_four VARCHAR(4),
    card_brand VARCHAR(20),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed, refunded
    
    -- Reference
    reference_number VARCHAR(50),
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Payment Applications (which invoices a payment applies to)
CREATE TABLE IF NOT EXISTS payment_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES invoices(id),
    
    amount_applied DECIMAL(12,2) NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(payment_id, invoice_id)
);

-- Credit Memos
CREATE TABLE IF NOT EXISTS credit_memos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    credit_memo_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Customer
    customer_id UUID NOT NULL REFERENCES customers(id),
    original_invoice_id UUID REFERENCES invoices(id),
    
    -- Credit Details
    credit_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount DECIMAL(12,2) NOT NULL,
    
    -- Reason
    reason VARCHAR(100),
    description TEXT,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, applied, voided
    applied_amount DECIMAL(12,2) DEFAULT 0,
    balance DECIMAL(12,2),
    
    -- Approval
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- AR Aging
CREATE TABLE IF NOT EXISTS ar_aging (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Snapshot Date
    aging_date DATE NOT NULL DEFAULT CURRENT_DATE,
    customer_id UUID NOT NULL REFERENCES customers(id),
    
    -- Aging Buckets
    current_amount DECIMAL(12,2) DEFAULT 0,
    days_30 DECIMAL(12,2) DEFAULT 0,
    days_60 DECIMAL(12,2) DEFAULT 0,
    days_90 DECIMAL(12,2) DEFAULT 0,
    days_120_plus DECIMAL(12,2) DEFAULT 0,
    total_due DECIMAL(12,2) DEFAULT 0,
    
    -- Metrics
    oldest_invoice_date DATE,
    invoice_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(aging_date, customer_id)
);

-- Commissions
CREATE TABLE IF NOT EXISTS commissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Sales Rep
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Source
    source_type VARCHAR(50), -- job, invoice, payment
    source_id UUID,
    
    -- Commission Details
    commission_date DATE NOT NULL,
    base_amount DECIMAL(12,2) NOT NULL,
    commission_rate DECIMAL(5,2) NOT NULL,
    commission_amount DECIMAL(12,2) NOT NULL,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, paid
    
    -- Payment
    paid_date DATE,
    payment_method VARCHAR(50),
    check_number VARCHAR(50),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SERVICE & WARRANTY MANAGEMENT
-- ============================================================================

-- Service Tickets
CREATE TABLE IF NOT EXISTS service_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Customer & Job
    customer_id UUID NOT NULL REFERENCES customers(id),
    job_id UUID REFERENCES jobs(id),
    property_id UUID REFERENCES properties(id),
    
    -- Issue Details
    issue_type VARCHAR(100), -- leak, damage, maintenance, inspection
    severity VARCHAR(20) DEFAULT 'normal', -- emergency, high, normal, low
    description TEXT NOT NULL,
    
    -- Location
    location_description TEXT,
    
    -- Assignment
    assigned_to UUID REFERENCES users(id),
    crew_id UUID REFERENCES crews(id),
    
    -- Scheduling
    scheduled_date DATE,
    scheduled_time TIME,
    
    -- SLA
    sla_response_hours INTEGER,
    sla_resolution_hours INTEGER,
    response_due TIMESTAMPTZ,
    resolution_due TIMESTAMPTZ,
    
    -- Status
    status VARCHAR(50) DEFAULT 'new', -- new, assigned, scheduled, in-progress, resolved, closed, cancelled
    
    -- Resolution
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    
    -- Satisfaction
    satisfaction_rating INTEGER CHECK (satisfaction_rating BETWEEN 1 AND 5),
    satisfaction_comments TEXT,
    
    -- Warranty
    is_warranty BOOLEAN DEFAULT FALSE,
    warranty_id UUID REFERENCES warranties(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Service History
CREATE TABLE IF NOT EXISTS service_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES service_tickets(id) ON DELETE CASCADE,
    
    -- Action
    action_type VARCHAR(50), -- created, assigned, scheduled, started, completed, note
    action_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Details
    description TEXT,
    
    -- Work Performed
    work_performed TEXT,
    materials_used JSONB,
    time_spent_hours DECIMAL(5,2),
    
    -- User
    performed_by UUID REFERENCES users(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Warranties
CREATE TABLE IF NOT EXISTS warranties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    warranty_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Coverage
    job_id UUID REFERENCES jobs(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    property_id UUID REFERENCES properties(id),
    
    -- Warranty Details
    warranty_type VARCHAR(50), -- workmanship, material, manufacturer, extended
    coverage_description TEXT,
    
    -- Duration
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_years INTEGER,
    
    -- Terms
    terms_conditions TEXT,
    exclusions TEXT,
    
    -- Transferability
    is_transferable BOOLEAN DEFAULT FALSE,
    transfer_fee DECIMAL(12,2),
    
    -- Registration
    registration_date DATE,
    registered_by UUID REFERENCES users(id),
    
    -- Manufacturer
    manufacturer_name VARCHAR(100),
    manufacturer_warranty_id VARCHAR(100),
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, expired, voided, transferred
    
    -- Claims
    claims_count INTEGER DEFAULT 0,
    total_claim_amount DECIMAL(12,2) DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Warranty Claims
CREATE TABLE IF NOT EXISTS warranty_claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_number VARCHAR(20) UNIQUE NOT NULL,
    warranty_id UUID NOT NULL REFERENCES warranties(id),
    
    -- Claim Details
    claim_date DATE NOT NULL DEFAULT CURRENT_DATE,
    issue_description TEXT NOT NULL,
    
    -- Investigation
    inspection_date DATE,
    inspector_id UUID REFERENCES users(id),
    inspection_notes TEXT,
    
    -- Decision
    status VARCHAR(50) DEFAULT 'submitted', -- submitted, investigating, approved, denied, completed
    decision_date DATE,
    decision_by UUID REFERENCES users(id),
    denial_reason TEXT,
    
    -- Resolution
    resolution_type VARCHAR(50), -- repair, replacement, refund
    estimated_cost DECIMAL(12,2),
    actual_cost DECIMAL(12,2),
    
    -- Work Order
    service_ticket_id UUID REFERENCES service_tickets(id),
    
    -- Documentation
    documentation JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Preventive Maintenance Schedules
CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Property
    property_id UUID NOT NULL REFERENCES properties(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    
    -- Schedule
    maintenance_type VARCHAR(100), -- inspection, cleaning, minor-repair
    frequency VARCHAR(50), -- monthly, quarterly, semi-annual, annual
    
    -- Next Service
    last_service_date DATE,
    next_service_date DATE,
    
    -- Contract
    contract_start DATE,
    contract_end DATE,
    contract_value DECIMAL(12,2),
    
    -- Auto-scheduling
    auto_schedule BOOLEAN DEFAULT TRUE,
    days_advance_notice INTEGER DEFAULT 7,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Financial Indexes
CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_payments_customer ON payments(customer_id);
CREATE INDEX idx_payments_date ON payments(payment_date DESC);
CREATE INDEX idx_payment_applications_invoice ON payment_applications(invoice_id);
CREATE INDEX idx_ar_aging_date ON ar_aging(aging_date DESC);
CREATE INDEX idx_commissions_user ON commissions(user_id);

-- Service Indexes
CREATE INDEX idx_service_tickets_customer ON service_tickets(customer_id);
CREATE INDEX idx_service_tickets_status ON service_tickets(status);
CREATE INDEX idx_service_tickets_severity ON service_tickets(severity);
CREATE INDEX idx_warranties_customer ON warranties(customer_id);
CREATE INDEX idx_warranties_end_date ON warranties(end_date);
CREATE INDEX idx_warranty_claims_warranty ON warranty_claims(warranty_id);
CREATE INDEX idx_maintenance_schedules_next_date ON maintenance_schedules(next_service_date);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Calculate invoice totals
CREATE OR REPLACE FUNCTION calculate_invoice_totals() RETURNS trigger AS $$
DECLARE
    v_subtotal DECIMAL(12,2);
    v_tax_amount DECIMAL(12,2);
BEGIN
    -- Calculate subtotal from line items
    SELECT COALESCE(SUM(total_price), 0)
    INTO v_subtotal
    FROM invoice_items
    WHERE invoice_id = COALESCE(NEW.invoice_id, OLD.invoice_id);
    
    -- Get tax amount
    SELECT COALESCE(SUM(tax_amount), 0)
    INTO v_tax_amount
    FROM invoice_items
    WHERE invoice_id = COALESCE(NEW.invoice_id, OLD.invoice_id)
    AND taxable = TRUE;
    
    -- Update invoice totals
    UPDATE invoices
    SET 
        subtotal = v_subtotal,
        tax_amount = v_tax_amount,
        total_amount = v_subtotal + v_tax_amount - COALESCE(discount_amount, 0),
        balance_due = v_subtotal + v_tax_amount - COALESCE(discount_amount, 0) - COALESCE(amount_paid, 0),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.invoice_id, OLD.invoice_id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_invoice_totals_trigger
    AFTER INSERT OR UPDATE OR DELETE ON invoice_items
    FOR EACH ROW
    EXECUTE FUNCTION calculate_invoice_totals();

-- Update invoice payment status
CREATE OR REPLACE FUNCTION update_invoice_payment_status() RETURNS trigger AS $$
DECLARE
    v_total_paid DECIMAL(12,2);
    v_invoice_total DECIMAL(12,2);
BEGIN
    -- Calculate total paid for this invoice
    SELECT COALESCE(SUM(amount_applied), 0)
    INTO v_total_paid
    FROM payment_applications
    WHERE invoice_id = NEW.invoice_id;
    
    -- Get invoice total
    SELECT total_amount
    INTO v_invoice_total
    FROM invoices
    WHERE id = NEW.invoice_id;
    
    -- Update invoice
    UPDATE invoices
    SET 
        amount_paid = v_total_paid,
        balance_due = total_amount - v_total_paid,
        status = CASE
            WHEN v_total_paid >= v_invoice_total THEN 'paid'
            WHEN v_total_paid > 0 THEN 'partial'
            ELSE status
        END,
        paid_date = CASE
            WHEN v_total_paid >= v_invoice_total THEN CURRENT_DATE
            ELSE paid_date
        END,
        updated_at = NOW()
    WHERE id = NEW.invoice_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_invoice_payment_status_trigger
    AFTER INSERT OR UPDATE ON payment_applications
    FOR EACH ROW
    EXECUTE FUNCTION update_invoice_payment_status();

-- Generate invoice numbers
CREATE OR REPLACE FUNCTION generate_invoice_number() RETURNS trigger AS $$
BEGIN
    IF NEW.invoice_number IS NULL THEN
        NEW.invoice_number := 'INV-' || TO_CHAR(NOW(), 'YYYY') || '-' || LPAD(nextval('invoice_number_seq')::text, 5, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE IF NOT EXISTS invoice_number_seq START 1;

CREATE TRIGGER generate_invoice_number_trigger
    BEFORE INSERT ON invoices
    FOR EACH ROW
    EXECUTE FUNCTION generate_invoice_number();

-- Generate service ticket numbers
CREATE OR REPLACE FUNCTION generate_ticket_number() RETURNS trigger AS $$
BEGIN
    IF NEW.ticket_number IS NULL THEN
        NEW.ticket_number := 'TKT-' || TO_CHAR(NOW(), 'YYYYMM') || '-' || LPAD(nextval('ticket_number_seq')::text, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE IF NOT EXISTS ticket_number_seq START 1;

CREATE TRIGGER generate_ticket_number_trigger
    BEFORE INSERT ON service_tickets
    FOR EACH ROW
    EXECUTE FUNCTION generate_ticket_number();

-- Update warranty claims count
CREATE OR REPLACE FUNCTION update_warranty_claims_count() RETURNS trigger AS $$
BEGIN
    UPDATE warranties
    SET 
        claims_count = (
            SELECT COUNT(*) 
            FROM warranty_claims 
            WHERE warranty_id = NEW.warranty_id
        ),
        total_claim_amount = (
            SELECT COALESCE(SUM(actual_cost), 0)
            FROM warranty_claims
            WHERE warranty_id = NEW.warranty_id
            AND status = 'completed'
        ),
        updated_at = NOW()
    WHERE id = NEW.warranty_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_warranty_claims_count_trigger
    AFTER INSERT OR UPDATE ON warranty_claims
    FOR EACH ROW
    EXECUTE FUNCTION update_warranty_claims_count();