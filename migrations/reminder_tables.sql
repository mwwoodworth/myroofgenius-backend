-- Payment Reminder Tables
-- Task 34: Payment reminders implementation

-- Reminder templates
CREATE TABLE IF NOT EXISTS reminder_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- payment_due, overdue, final_notice, etc
    subject VARCHAR(200),
    body TEXT NOT NULL,
    sms_message TEXT,
    days_before_due INT DEFAULT 3,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID NOT NULL
);

-- Payment reminders
CREATE TABLE IF NOT EXISTS payment_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,
    scheduled_time TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    channels JSONB, -- ['email', 'sms', 'in_app']
    template_id UUID REFERENCES reminder_templates(id),
    custom_message TEXT,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, sent, delivered, failed, cancelled
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID NOT NULL
);

-- Customer reminder settings
CREATE TABLE IF NOT EXISTS customer_reminder_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    enable_reminders BOOLEAN DEFAULT true,
    preferred_channel VARCHAR(20) DEFAULT 'email',
    email_address VARCHAR(255),
    phone_number VARCHAR(20),
    reminder_frequency VARCHAR(20) DEFAULT 'weekly', -- daily, weekly, biweekly, monthly
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID NOT NULL,
    UNIQUE(customer_id, tenant_id)
);

-- Reminder campaigns
CREATE TABLE IF NOT EXISTS reminder_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    trigger_conditions JSONB NOT NULL, -- Conditions to trigger campaign
    reminder_sequence JSONB NOT NULL, -- Sequence of reminders to send
    is_active BOOLEAN DEFAULT true,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID NOT NULL
);

-- Campaign enrollments
CREATE TABLE IF NOT EXISTS campaign_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES reminder_campaigns(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),
    current_step INT DEFAULT 0,
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active', -- active, completed, cancelled
    tenant_id UUID NOT NULL,
    UNIQUE(campaign_id, invoice_id, tenant_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_reminder_templates_type ON reminder_templates(type);
CREATE INDEX IF NOT EXISTS idx_reminder_templates_tenant_id ON reminder_templates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_payment_reminders_invoice_id ON payment_reminders(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payment_reminders_scheduled_time ON payment_reminders(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_payment_reminders_status ON payment_reminders(status);
CREATE INDEX IF NOT EXISTS idx_payment_reminders_sent_at ON payment_reminders(sent_at);
CREATE INDEX IF NOT EXISTS idx_payment_reminders_tenant_id ON payment_reminders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_customer_reminder_settings_customer_id ON customer_reminder_settings(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_reminder_settings_tenant_id ON customer_reminder_settings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reminder_campaigns_is_active ON reminder_campaigns(is_active);
CREATE INDEX IF NOT EXISTS idx_reminder_campaigns_tenant_id ON reminder_campaigns(tenant_id);
CREATE INDEX IF NOT EXISTS idx_campaign_enrollments_campaign_id ON campaign_enrollments(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_enrollments_status ON campaign_enrollments(status);
CREATE INDEX IF NOT EXISTS idx_campaign_enrollments_tenant_id ON campaign_enrollments(tenant_id);

-- Default reminder templates
INSERT INTO reminder_templates (name, type, subject, body, days_before_due, tenant_id) VALUES
('Payment Due Soon', 'payment_due', 'Payment Due: Invoice {invoice_number}',
 'Dear {customer_name},\n\nThis is a friendly reminder that your invoice {invoice_number} for {amount_due} is due on {due_date}.\n\nYou can pay online at: {payment_link}\n\nThank you for your business!',
 3, COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '00000000-0000-0000-0000-000000000001')::uuid),
('Overdue Notice', 'overdue', 'Overdue: Invoice {invoice_number}',
 'Dear {customer_name},\n\nYour invoice {invoice_number} for {amount_due} was due on {due_date} and is now {days_overdue} days overdue.\n\nPlease make payment as soon as possible at: {payment_link}\n\nIf you have already paid, please disregard this notice.',
 0, COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '00000000-0000-0000-0000-000000000001')::uuid),
('Final Notice', 'final_notice', 'Final Notice: Invoice {invoice_number}',
 'Dear {customer_name},\n\nThis is a final notice regarding your overdue invoice {invoice_number} for {amount_due}.\n\nImmediate payment is required to avoid further collection actions.\n\nPay now: {payment_link}',
 0, COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '00000000-0000-0000-0000-000000000001')::uuid)
ON CONFLICT DO NOTHING;

-- Function to auto-schedule reminders
CREATE OR REPLACE FUNCTION auto_schedule_reminders()
RETURNS void AS $$
DECLARE
    inv RECORD;
    template RECORD;
BEGIN
    -- For each unpaid invoice
    FOR inv IN 
        SELECT i.*, c.email
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        LEFT JOIN customer_reminder_settings crs ON c.id = crs.customer_id
        WHERE i.status IN ('sent', 'viewed', 'partial')
            AND i.balance_cents > 0
            AND (crs.enable_reminders IS NULL OR crs.enable_reminders = true)
    LOOP
        -- Check if reminder already scheduled
        IF NOT EXISTS (
            SELECT 1 FROM payment_reminders
            WHERE invoice_id = inv.id
                AND status = 'scheduled'
                AND scheduled_time > NOW()
        ) THEN
            -- Determine reminder type
            IF inv.due_date > CURRENT_DATE THEN
                -- Payment due soon
                SELECT * INTO template FROM reminder_templates
                WHERE type = 'payment_due' AND is_active = true
                LIMIT 1;
                
                IF FOUND THEN
                    INSERT INTO payment_reminders (
                        invoice_id, reminder_type, scheduled_time,
                        channels, template_id, status, tenant_id
                    ) VALUES (
                        inv.id, 'payment_due',
                        inv.due_date - INTERVAL '3 days',
                        '["email"]'::jsonb, template.id, 'scheduled', inv.tenant_id
                    );
                END IF;
            ELSIF inv.due_date <= CURRENT_DATE - 7 THEN
                -- Overdue
                SELECT * INTO template FROM reminder_templates
                WHERE type = 'overdue' AND is_active = true
                LIMIT 1;
                
                IF FOUND THEN
                    INSERT INTO payment_reminders (
                        invoice_id, reminder_type, scheduled_time,
                        channels, template_id, status, tenant_id
                    ) VALUES (
                        inv.id, 'overdue',
                        NOW() + INTERVAL '1 hour',
                        '["email"]'::jsonb, template.id, 'scheduled', inv.tenant_id
                    );
                END IF;
            END IF;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updating timestamps
CREATE TRIGGER set_reminder_templates_updated_at
BEFORE UPDATE ON reminder_templates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_customer_reminder_settings_updated_at
BEFORE UPDATE ON customer_reminder_settings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_reminder_campaigns_updated_at
BEFORE UPDATE ON reminder_campaigns
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
