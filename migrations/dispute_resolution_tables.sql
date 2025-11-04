-- Dispute Resolution Tables
-- Task 38: Dispute resolution implementation

-- Main disputes table
CREATE TABLE IF NOT EXISTS disputes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id),
    job_id UUID REFERENCES jobs(id),
    dispute_type VARCHAR(20) NOT NULL, -- billing, service, quality, warranty, contract, payment, pricing, other
    status VARCHAR(20) DEFAULT 'submitted', -- submitted, acknowledged, investigating, pending_info, under_review, escalated, resolved, rejected, withdrawn, legal
    priority VARCHAR(10) DEFAULT 'medium', -- low, medium, high, critical
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    disputed_amount DECIMAL(12,2) NOT NULL,
    requested_resolution TEXT,
    assigned_to VARCHAR(100),
    resolution_type VARCHAR(30), -- full_refund, partial_refund, service_credit, replacement, repair, compensation, apology, no_action, legal_settlement
    resolution_amount DECIMAL(12,2),
    resolution_notes TEXT,
    resolution_approved_by VARCHAR(100),
    customer_accepted BOOLEAN DEFAULT false,
    contact_preference VARCHAR(20) DEFAULT 'email', -- email, phone, in_person, portal, letter, video_call
    submitted_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_date TIMESTAMPTZ,
    resolved_date TIMESTAMPTZ,
    internal_notes TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dispute communications
CREATE TABLE IF NOT EXISTS dispute_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    direction VARCHAR(10) NOT NULL, -- inbound, outbound
    method VARCHAR(20) NOT NULL, -- email, phone, in_person, portal, letter, video_call
    subject VARCHAR(200),
    message TEXT NOT NULL,
    sender VARCHAR(100) NOT NULL,
    recipient VARCHAR(100) NOT NULL,
    attachments JSONB,
    read_status BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dispute evidence
CREATE TABLE IF NOT EXISTS dispute_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    evidence_type VARCHAR(30) NOT NULL, -- photo, video, document, email, invoice, contract, receipt, testimony, expert_report, other
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_url TEXT,
    file_size INT,
    mime_type VARCHAR(100),
    submitted_by VARCHAR(100) NOT NULL,
    submitted_date TIMESTAMPTZ DEFAULT NOW(),
    verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(100),
    verified_date TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dispute resolutions
CREATE TABLE IF NOT EXISTS dispute_resolutions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    resolution_type VARCHAR(30) NOT NULL,
    resolution_amount DECIMAL(12,2),
    resolution_notes TEXT NOT NULL,
    implementation_date DATE,
    approved_by VARCHAR(100) NOT NULL,
    customer_accepted BOOLEAN DEFAULT false,
    customer_response TEXT,
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dispute escalations
CREATE TABLE IF NOT EXISTS dispute_escalations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    escalation_level INT DEFAULT 1, -- 1, 2, 3
    escalation_reason TEXT NOT NULL,
    escalated_from VARCHAR(100),
    escalated_to VARCHAR(100) NOT NULL,
    urgency VARCHAR(10) NOT NULL, -- low, medium, high, critical
    expected_resolution_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dispute activities log
CREATE TABLE IF NOT EXISTS dispute_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- created, updated, communication, evidence_added, escalated, resolved, etc.
    description TEXT NOT NULL,
    performed_by VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dispute templates
CREATE TABLE IF NOT EXISTS dispute_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) NOT NULL,
    template_type VARCHAR(30) NOT NULL, -- acknowledgment, investigation, resolution, rejection, escalation
    subject VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dispute categories
CREATE TABLE IF NOT EXISTS dispute_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES dispute_categories(id),
    typical_resolution VARCHAR(30),
    avg_resolution_days INT,
    escalation_threshold_days INT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dispute SLA rules
CREATE TABLE IF NOT EXISTS dispute_sla_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    priority VARCHAR(10) NOT NULL, -- low, medium, high, critical
    acknowledgment_hours INT NOT NULL, -- Hours to acknowledge
    resolution_hours INT NOT NULL, -- Hours to resolve
    escalation_hours INT, -- Hours before auto-escalation
    notification_intervals INT[], -- Hours for reminder notifications
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(priority)
);

-- Dispute refunds
CREATE TABLE IF NOT EXISTS dispute_refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id),
    refund_amount DECIMAL(12,2) NOT NULL,
    refund_method VARCHAR(20) NOT NULL, -- credit_card, ach, check, credit_memo, cash
    refund_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed, cancelled
    refund_date DATE,
    transaction_id VARCHAR(100),
    processed_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dispute ratings
CREATE TABLE IF NOT EXISTS dispute_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dispute_id UUID NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id),
    resolution_satisfaction INT CHECK (resolution_satisfaction >= 1 AND resolution_satisfaction <= 5),
    process_satisfaction INT CHECK (process_satisfaction >= 1 AND process_satisfaction <= 5),
    communication_satisfaction INT CHECK (communication_satisfaction >= 1 AND communication_satisfaction <= 5),
    overall_satisfaction INT CHECK (overall_satisfaction >= 1 AND overall_satisfaction <= 5),
    would_recommend BOOLEAN,
    feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_disputes_customer_id ON disputes(customer_id);
CREATE INDEX IF NOT EXISTS idx_disputes_status ON disputes(status);
CREATE INDEX IF NOT EXISTS idx_disputes_priority ON disputes(priority);
CREATE INDEX IF NOT EXISTS idx_disputes_dispute_type ON disputes(dispute_type);
CREATE INDEX IF NOT EXISTS idx_disputes_submitted_date ON disputes(submitted_date);
CREATE INDEX IF NOT EXISTS idx_disputes_dispute_number ON disputes(dispute_number);
CREATE INDEX IF NOT EXISTS idx_dispute_communications_dispute_id ON dispute_communications(dispute_id);
CREATE INDEX IF NOT EXISTS idx_dispute_evidence_dispute_id ON dispute_evidence(dispute_id);
CREATE INDEX IF NOT EXISTS idx_dispute_resolutions_dispute_id ON dispute_resolutions(dispute_id);
CREATE INDEX IF NOT EXISTS idx_dispute_escalations_dispute_id ON dispute_escalations(dispute_id);
CREATE INDEX IF NOT EXISTS idx_dispute_activities_dispute_id ON dispute_activities(dispute_id);
CREATE INDEX IF NOT EXISTS idx_dispute_activities_created_at ON dispute_activities(created_at);
CREATE INDEX IF NOT EXISTS idx_dispute_refunds_dispute_id ON dispute_refunds(dispute_id);
CREATE INDEX IF NOT EXISTS idx_dispute_ratings_dispute_id ON dispute_ratings(dispute_id);

-- Default SLA rules
INSERT INTO dispute_sla_rules (priority, acknowledgment_hours, resolution_hours, escalation_hours, notification_intervals)
VALUES
    ('critical', 2, 24, 12, ARRAY[4, 8, 12]),
    ('high', 4, 72, 48, ARRAY[12, 24, 48]),
    ('medium', 12, 120, 96, ARRAY[24, 48, 72]),
    ('low', 24, 240, 192, ARRAY[48, 96, 144])
ON CONFLICT (priority) DO NOTHING;

-- Default dispute categories
INSERT INTO dispute_categories (category_name, description, typical_resolution, avg_resolution_days, escalation_threshold_days)
VALUES
    ('Billing Error', 'Incorrect charges or billing mistakes', 'full_refund', 3, 5),
    ('Service Quality', 'Service did not meet expectations', 'partial_refund', 7, 10),
    ('Product Defect', 'Product damaged or defective', 'replacement', 5, 7),
    ('Contract Dispute', 'Disagreement over contract terms', 'compensation', 14, 21),
    ('Payment Issue', 'Problems with payment processing', 'full_refund', 2, 3),
    ('Warranty Claim', 'Product warranty issues', 'repair', 10, 14),
    ('Delivery Problem', 'Late or missing delivery', 'service_credit', 3, 5)
ON CONFLICT (category_name) DO NOTHING;

-- Default dispute templates
INSERT INTO dispute_templates (template_name, template_type, subject, content, variables)
VALUES
    ('Dispute Acknowledgment', 'acknowledgment',
     'We''ve Received Your Dispute - {{dispute_number}}',
     'Dear {{customer_name}},\n\nThank you for bringing this matter to our attention. We have received your dispute regarding {{subject}} and assigned it case number {{dispute_number}}.\n\nWhat happens next:\n- Our team will review your dispute within {{sla_hours}} hours\n- We may contact you for additional information\n- You will receive updates via {{contact_preference}}\n\nWe appreciate your patience as we investigate this matter.\n\nSincerely,\n{{company_name}}',
     '["customer_name", "dispute_number", "subject", "sla_hours", "contact_preference", "company_name"]'::jsonb),

    ('Resolution Notification', 'resolution',
     'Your Dispute Has Been Resolved - {{dispute_number}}',
     'Dear {{customer_name}},\n\nWe have completed our investigation of your dispute ({{dispute_number}}) and reached a resolution.\n\nResolution Details:\n{{resolution_details}}\n\nNext Steps:\n{{next_steps}}\n\nIf you have any questions about this resolution, please contact us.\n\nThank you for your patience.\n\nSincerely,\n{{company_name}}',
     '["customer_name", "dispute_number", "resolution_details", "next_steps", "company_name"]'::jsonb),

    ('Escalation Notice', 'escalation',
     'Your Dispute Has Been Escalated - {{dispute_number}}',
     'Dear {{customer_name}},\n\nYour dispute ({{dispute_number}}) has been escalated to {{escalation_level}} for expedited resolution.\n\nReason for escalation: {{escalation_reason}}\n\nYour new contact: {{escalated_to}}\nExpected resolution: {{expected_date}}\n\nWe apologize for any inconvenience and are working to resolve this matter quickly.\n\nSincerely,\n{{company_name}}',
     '["customer_name", "dispute_number", "escalation_level", "escalation_reason", "escalated_to", "expected_date", "company_name"]'::jsonb)
ON CONFLICT DO NOTHING;

-- Function to calculate dispute metrics
CREATE OR REPLACE FUNCTION calculate_dispute_age(dispute_uuid UUID)
RETURNS INT AS $$
DECLARE
    age_days INT;
BEGIN
    SELECT EXTRACT(DAY FROM NOW() - submitted_date)::INT
    INTO age_days
    FROM disputes
    WHERE id = dispute_uuid;

    RETURN COALESCE(age_days, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to check SLA breach
CREATE OR REPLACE FUNCTION check_sla_breach(dispute_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    is_breached BOOLEAN := false;
    dispute_record RECORD;
    sla_record RECORD;
    hours_elapsed NUMERIC;
BEGIN
    -- Get dispute details
    SELECT * INTO dispute_record
    FROM disputes
    WHERE id = dispute_uuid;

    -- Get SLA rules for priority
    SELECT * INTO sla_record
    FROM dispute_sla_rules
    WHERE priority = dispute_record.priority;

    -- Check acknowledgment SLA
    IF dispute_record.acknowledged_date IS NULL THEN
        hours_elapsed := EXTRACT(EPOCH FROM NOW() - dispute_record.submitted_date) / 3600;
        IF hours_elapsed > sla_record.acknowledgment_hours THEN
            is_breached := true;
        END IF;
    END IF;

    -- Check resolution SLA if not resolved
    IF dispute_record.resolved_date IS NULL THEN
        hours_elapsed := EXTRACT(EPOCH FROM NOW() - dispute_record.submitted_date) / 3600;
        IF hours_elapsed > sla_record.resolution_hours THEN
            is_breached := true;
        END IF;
    END IF;

    RETURN is_breached;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update dispute timestamps
CREATE TRIGGER set_disputes_updated_at
BEFORE UPDATE ON disputes
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_dispute_templates_updated_at
BEFORE UPDATE ON dispute_templates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_dispute_refunds_updated_at
BEFORE UPDATE ON dispute_refunds
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();