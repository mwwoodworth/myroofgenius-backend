-- Collections Workflow Tables
-- Task 37: Collections workflow implementation

-- Collection cases
CREATE TABLE IF NOT EXISTS collection_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    case_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- active, on_hold, closed, settled, written_off
    stage VARCHAR(30) DEFAULT 'pre_collection', -- pre_collection, early_stage, mid_stage, late_stage, legal, closed
    total_amount DECIMAL(12,2) NOT NULL,
    collected_amount DECIMAL(12,2) DEFAULT 0,
    remaining_amount DECIMAL(12,2) NOT NULL,
    oldest_invoice_date DATE,
    assigned_to VARCHAR(100),
    priority VARCHAR(10) DEFAULT 'medium', -- low, medium, high, critical
    escalation_date DATE,
    settlement_amount DECIMAL(12,2),
    settlement_date DATE,
    close_reason VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

-- Collection case invoices
CREATE TABLE IF NOT EXISTS collection_case_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES collection_cases(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES invoices(id),
    invoice_number VARCHAR(50),
    amount DECIMAL(12,2) NOT NULL,
    days_overdue INT,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(case_id, invoice_id)
);

-- Collection contacts
CREATE TABLE IF NOT EXISTS collection_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES collection_cases(id) ON DELETE CASCADE,
    contact_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    contact_method VARCHAR(20) NOT NULL, -- phone, email, sms, mail, in_person, automated
    contact_type VARCHAR(30) NOT NULL, -- initial, follow_up, promise_to_pay, dispute, settlement, final
    contacted_by VARCHAR(100),
    contact_person VARCHAR(100),
    result VARCHAR(30), -- no_answer, left_message, spoke_customer, promise_to_pay, dispute, payment_made, refused
    promise_amount DECIMAL(12,2),
    promise_date DATE,
    notes TEXT,
    recording_url TEXT,
    email_id VARCHAR(100),
    next_action VARCHAR(50),
    next_contact_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collection payment arrangements
CREATE TABLE IF NOT EXISTS collection_payment_arrangements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES collection_cases(id) ON DELETE CASCADE,
    arrangement_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    down_payment DECIMAL(12,2) DEFAULT 0,
    number_of_payments INT NOT NULL,
    payment_amount DECIMAL(12,2) NOT NULL,
    frequency VARCHAR(20) NOT NULL, -- weekly, bi_weekly, monthly
    start_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- pending, active, completed, defaulted, cancelled
    payments_made INT DEFAULT 0,
    amount_paid DECIMAL(12,2) DEFAULT 0,
    last_payment_date DATE,
    next_payment_date DATE,
    default_reason TEXT,
    approved_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collection arrangement payments
CREATE TABLE IF NOT EXISTS collection_arrangement_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arrangement_id UUID NOT NULL REFERENCES collection_payment_arrangements(id) ON DELETE CASCADE,
    payment_number INT NOT NULL,
    due_date DATE NOT NULL,
    payment_date DATE,
    due_amount DECIMAL(12,2) NOT NULL,
    paid_amount DECIMAL(12,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending', -- pending, paid, partial, missed, waived
    payment_method VARCHAR(20),
    reference_number VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(arrangement_id, payment_number)
);

-- Collection letters
CREATE TABLE IF NOT EXISTS collection_letters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES collection_cases(id) ON DELETE CASCADE,
    letter_type VARCHAR(30) NOT NULL, -- friendly_reminder, first_notice, second_notice, final_notice, legal_warning
    template_id VARCHAR(50),
    sent_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE,
    delivery_method VARCHAR(20) NOT NULL, -- mail, email, certified_mail, both
    tracking_number VARCHAR(100),
    delivered_date DATE,
    response_received BOOLEAN DEFAULT false,
    response_date DATE,
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collection disputes
CREATE TABLE IF NOT EXISTS collection_disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES collection_cases(id) ON DELETE CASCADE,
    dispute_date DATE NOT NULL DEFAULT CURRENT_DATE,
    dispute_reason VARCHAR(50) NOT NULL, -- incorrect_amount, service_issue, never_received, already_paid, other
    disputed_amount DECIMAL(12,2) NOT NULL,
    description TEXT NOT NULL,
    supporting_documents JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20) DEFAULT 'pending', -- pending, investigating, resolved, rejected
    resolution TEXT,
    resolved_date DATE,
    resolved_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collection agency assignments
CREATE TABLE IF NOT EXISTS collection_agency_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES collection_cases(id) ON DELETE CASCADE,
    agency_id UUID,
    agency_name VARCHAR(100) NOT NULL,
    assigned_date DATE NOT NULL DEFAULT CURRENT_DATE,
    account_number VARCHAR(50),
    placed_amount DECIMAL(12,2) NOT NULL,
    commission_rate DECIMAL(5,2) NOT NULL,
    collected_amount DECIMAL(12,2) DEFAULT 0,
    commission_paid DECIMAL(12,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active', -- active, recalled, closed, settled
    recall_date DATE,
    recall_reason TEXT,
    last_update_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collection activities log
CREATE TABLE IF NOT EXISTS collection_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES collection_cases(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    performed_by VARCHAR(100),
    description TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collection templates
CREATE TABLE IF NOT EXISTS collection_templates (
    id VARCHAR(50) PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    template_type VARCHAR(30) NOT NULL, -- letter, email, sms, script
    category VARCHAR(30) NOT NULL, -- reminder, notice, warning, legal
    subject VARCHAR(200),
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collection rules
CREATE TABLE IF NOT EXISTS collection_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(30) NOT NULL, -- escalation, assignment, contact, legal
    days_overdue_min INT,
    days_overdue_max INT,
    amount_min DECIMAL(12,2),
    amount_max DECIMAL(12,2),
    action VARCHAR(50) NOT NULL,
    parameters JSONB,
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_collection_cases_customer_id ON collection_cases(customer_id);
CREATE INDEX IF NOT EXISTS idx_collection_cases_status ON collection_cases(status);
CREATE INDEX IF NOT EXISTS idx_collection_cases_stage ON collection_cases(stage);
CREATE INDEX IF NOT EXISTS idx_collection_cases_case_number ON collection_cases(case_number);
CREATE INDEX IF NOT EXISTS idx_collection_case_invoices_case_id ON collection_case_invoices(case_id);
CREATE INDEX IF NOT EXISTS idx_collection_contacts_case_id ON collection_contacts(case_id);
CREATE INDEX IF NOT EXISTS idx_collection_contacts_contact_date ON collection_contacts(contact_date);
CREATE INDEX IF NOT EXISTS idx_collection_payment_arrangements_case_id ON collection_payment_arrangements(case_id);
CREATE INDEX IF NOT EXISTS idx_collection_payment_arrangements_status ON collection_payment_arrangements(status);
CREATE INDEX IF NOT EXISTS idx_collection_arrangement_payments_arrangement_id ON collection_arrangement_payments(arrangement_id);
CREATE INDEX IF NOT EXISTS idx_collection_letters_case_id ON collection_letters(case_id);
CREATE INDEX IF NOT EXISTS idx_collection_disputes_case_id ON collection_disputes(case_id);
CREATE INDEX IF NOT EXISTS idx_collection_disputes_status ON collection_disputes(status);
CREATE INDEX IF NOT EXISTS idx_collection_agency_assignments_case_id ON collection_agency_assignments(case_id);
CREATE INDEX IF NOT EXISTS idx_collection_activities_case_id ON collection_activities(case_id);
CREATE INDEX IF NOT EXISTS idx_collection_activities_activity_date ON collection_activities(activity_date);

-- Default collection templates
INSERT INTO collection_templates (id, template_name, template_type, category, subject, content, variables)
VALUES 
    ('friendly_reminder_email', 'Friendly Payment Reminder', 'email', 'reminder', 
     'Payment Reminder - Invoice {{invoice_number}}',
     'Dear {{customer_name}},\n\nThis is a friendly reminder that invoice {{invoice_number}} for {{amount}} is now {{days_overdue}} days past due.\n\nPlease remit payment at your earliest convenience.\n\nThank you,\n{{company_name}}',
     '["customer_name", "invoice_number", "amount", "days_overdue", "company_name"]'::jsonb),
    
    ('first_notice_letter', 'First Collection Notice', 'letter', 'notice',
     'First Notice - Past Due Account',
     'Dear {{customer_name}},\n\nOur records show that your account has a past due balance of {{total_amount}}.\n\nPlease contact us immediately at {{phone}} to discuss payment arrangements.\n\nSincerely,\n{{company_name}}',
     '["customer_name", "total_amount", "phone", "company_name"]'::jsonb),
    
    ('final_notice_letter', 'Final Collection Notice', 'letter', 'warning',
     'FINAL NOTICE - Immediate Action Required',
     'Dear {{customer_name}},\n\nDespite our previous attempts to contact you, your account remains seriously past due.\n\nTotal Amount Due: {{total_amount}}\n\nThis is your FINAL NOTICE before we take further collection action.\n\nYou must contact us within 10 days to avoid additional fees and potential legal action.\n\n{{company_name}}',
     '["customer_name", "total_amount", "company_name"]'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- Function to calculate collection metrics
CREATE OR REPLACE FUNCTION calculate_collection_metrics(case_uuid UUID)
RETURNS TABLE(
    recovery_rate NUMERIC,
    days_in_collection INT,
    contact_count INT,
    last_contact_date DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN cc.total_amount > 0 THEN ROUND((cc.collected_amount / cc.total_amount) * 100, 2)
            ELSE 0
        END as recovery_rate,
        EXTRACT(DAY FROM NOW() - cc.created_at)::INT as days_in_collection,
        COUNT(DISTINCT cont.id)::INT as contact_count,
        MAX(cont.contact_date)::DATE as last_contact_date
    FROM collection_cases cc
    LEFT JOIN collection_contacts cont ON cont.case_id = cc.id
    WHERE cc.id = case_uuid
    GROUP BY cc.id, cc.total_amount, cc.collected_amount, cc.created_at;
END;
$$ LANGUAGE plpgsql;

-- Function to escalate collection cases
CREATE OR REPLACE FUNCTION escalate_collection_case(case_uuid UUID, new_stage VARCHAR)
RETURNS VOID AS $$
BEGIN
    -- Update case stage
    UPDATE collection_cases
    SET stage = new_stage,
        escalation_date = CURRENT_DATE,
        updated_at = NOW()
    WHERE id = case_uuid;
    
    -- Log activity
    INSERT INTO collection_activities (
        case_id, activity_type, description, old_value, new_value, performed_by
    )
    SELECT 
        case_uuid,
        'escalation',
        'Case escalated to ' || new_stage,
        stage,
        new_stage,
        'system'
    FROM collection_cases
    WHERE id = case_uuid;
END;
$$ LANGUAGE plpgsql;

-- Update timestamps triggers
CREATE TRIGGER set_collection_cases_updated_at
BEFORE UPDATE ON collection_cases
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_collection_payment_arrangements_updated_at
BEFORE UPDATE ON collection_payment_arrangements
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_collection_disputes_updated_at
BEFORE UPDATE ON collection_disputes
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_collection_agency_assignments_updated_at
BEFORE UPDATE ON collection_agency_assignments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_collection_templates_updated_at
BEFORE UPDATE ON collection_templates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_collection_rules_updated_at
BEFORE UPDATE ON collection_rules
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();