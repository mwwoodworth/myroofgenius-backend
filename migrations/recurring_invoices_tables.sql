-- Recurring Invoices Tables
-- Task 35: Recurring invoices implementation

-- Recurring invoices main table
CREATE TABLE IF NOT EXISTS recurring_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    template_id UUID REFERENCES invoice_templates(id),
    frequency VARCHAR(20) NOT NULL, -- daily, weekly, monthly, quarterly, etc
    interval_value INT NOT NULL DEFAULT 1, -- Interval between occurrences
    billing_day VARCHAR(20), -- first, last, specific, weekday
    specific_day INT, -- Day of month (1-31)
    weekday INT, -- Day of week (0-6, 0=Monday)
    start_date DATE NOT NULL,
    end_date DATE,
    max_occurrences INT,
    occurrences_generated INT DEFAULT 0,
    next_occurrence_date DATE,
    line_items JSONB NOT NULL DEFAULT '[]'::jsonb,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    payment_terms VARCHAR(100) DEFAULT 'Net 30',
    notes TEXT,
    auto_send BOOLEAN DEFAULT false,
    auto_charge BOOLEAN DEFAULT false,
    saved_payment_method_id UUID REFERENCES saved_payment_methods(id),
    status VARCHAR(20) DEFAULT 'active', -- active, paused, cancelled, completed, expired
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

-- Recurring invoice instances (each generated invoice)
CREATE TABLE IF NOT EXISTS recurring_invoice_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recurring_invoice_id UUID NOT NULL REFERENCES recurring_invoices(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id),
    occurrence_number INT NOT NULL,
    scheduled_date DATE NOT NULL,
    generated_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, generated, sent, paid, failed, cancelled
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recurring invoice modifications (track changes)
CREATE TABLE IF NOT EXISTS recurring_invoice_modifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recurring_invoice_id UUID NOT NULL REFERENCES recurring_invoices(id) ON DELETE CASCADE,
    modification_type VARCHAR(50) NOT NULL, -- line_item_change, frequency_change, amount_change, etc
    old_value JSONB,
    new_value JSONB,
    effective_date DATE,
    reason TEXT,
    modified_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscription plans (predefined recurring templates)
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_name VARCHAR(100) NOT NULL,
    description TEXT,
    frequency VARCHAR(20) NOT NULL,
    interval_value INT DEFAULT 1,
    base_price DECIMAL(12,2) NOT NULL,
    setup_fee DECIMAL(12,2) DEFAULT 0,
    trial_days INT DEFAULT 0,
    features JSONB,
    line_items JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Customer subscriptions
CREATE TABLE IF NOT EXISTS customer_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    subscription_plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    recurring_invoice_id UUID REFERENCES recurring_invoices(id),
    start_date DATE NOT NULL,
    trial_end_date DATE,
    current_period_start DATE,
    current_period_end DATE,
    status VARCHAR(20) DEFAULT 'active', -- trialing, active, past_due, cancelled, expired
    cancel_at_period_end BOOLEAN DEFAULT false,
    cancelled_at TIMESTAMPTZ,
    cancel_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(customer_id, subscription_plan_id, status)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_recurring_invoices_customer_id ON recurring_invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_recurring_invoices_status ON recurring_invoices(status);
CREATE INDEX IF NOT EXISTS idx_recurring_invoices_next_occurrence ON recurring_invoices(next_occurrence_date);
CREATE INDEX IF NOT EXISTS idx_recurring_invoice_instances_recurring_id ON recurring_invoice_instances(recurring_invoice_id);
CREATE INDEX IF NOT EXISTS idx_recurring_invoice_instances_scheduled_date ON recurring_invoice_instances(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_recurring_invoice_instances_status ON recurring_invoice_instances(status);
CREATE INDEX IF NOT EXISTS idx_subscription_plans_is_active ON subscription_plans(is_active);
CREATE INDEX IF NOT EXISTS idx_customer_subscriptions_customer_id ON customer_subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_subscriptions_status ON customer_subscriptions(status);

-- Function to process scheduled recurring invoices
CREATE OR REPLACE FUNCTION process_scheduled_recurring_invoices()
RETURNS void AS $$
DECLARE
    rec RECORD;
BEGIN
    -- Find all active recurring invoices due today
    FOR rec IN
        SELECT * FROM recurring_invoices
        WHERE status = 'active'
            AND next_occurrence_date <= CURRENT_DATE
            AND (end_date IS NULL OR next_occurrence_date <= end_date)
            AND (max_occurrences IS NULL OR occurrences_generated < max_occurrences)
    LOOP
        -- Create scheduled instance
        INSERT INTO recurring_invoice_instances (
            recurring_invoice_id,
            occurrence_number,
            scheduled_date,
            status
        ) VALUES (
            rec.id,
            rec.occurrences_generated + 1,
            rec.next_occurrence_date,
            'scheduled'
        );
        
        -- Update recurring invoice
        UPDATE recurring_invoices
        SET occurrences_generated = occurrences_generated + 1,
            next_occurrence_date = CASE rec.frequency
                WHEN 'daily' THEN rec.next_occurrence_date + INTERVAL '1 day' * rec.interval_value
                WHEN 'weekly' THEN rec.next_occurrence_date + INTERVAL '1 week' * rec.interval_value
                WHEN 'biweekly' THEN rec.next_occurrence_date + INTERVAL '2 weeks' * rec.interval_value
                WHEN 'monthly' THEN rec.next_occurrence_date + INTERVAL '1 month' * rec.interval_value
                WHEN 'quarterly' THEN rec.next_occurrence_date + INTERVAL '3 months' * rec.interval_value
                WHEN 'semi_annually' THEN rec.next_occurrence_date + INTERVAL '6 months' * rec.interval_value
                WHEN 'annually' THEN rec.next_occurrence_date + INTERVAL '1 year' * rec.interval_value
                ELSE rec.next_occurrence_date + INTERVAL '1 month'
            END,
            status = CASE
                WHEN rec.max_occurrences IS NOT NULL AND rec.occurrences_generated + 1 >= rec.max_occurrences THEN 'completed'
                WHEN rec.end_date IS NOT NULL AND rec.next_occurrence_date >= rec.end_date THEN 'completed'
                ELSE rec.status
            END
        WHERE id = rec.id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updating timestamps
CREATE TRIGGER set_recurring_invoices_updated_at
BEFORE UPDATE ON recurring_invoices
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_subscription_plans_updated_at
BEFORE UPDATE ON subscription_plans
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_customer_subscriptions_updated_at
BEFORE UPDATE ON customer_subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();