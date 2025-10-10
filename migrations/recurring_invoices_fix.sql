-- Fix for recurring invoices tables
-- Handle template_id foreign key issue

-- Recurring invoices main table
CREATE TABLE IF NOT EXISTS recurring_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    template_id VARCHAR(50), -- Match invoice_templates id type
    frequency VARCHAR(20) NOT NULL,
    interval_value INT NOT NULL DEFAULT 1,
    billing_day VARCHAR(20),
    specific_day INT,
    weekday INT,
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
    saved_payment_method_id UUID,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

-- Recurring invoice instances
CREATE TABLE IF NOT EXISTS recurring_invoice_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recurring_invoice_id UUID NOT NULL REFERENCES recurring_invoices(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id),
    occurrence_number INT NOT NULL,
    scheduled_date DATE NOT NULL,
    generated_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'scheduled',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recurring invoice modifications
CREATE TABLE IF NOT EXISTS recurring_invoice_modifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recurring_invoice_id UUID NOT NULL REFERENCES recurring_invoices(id) ON DELETE CASCADE,
    modification_type VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    effective_date DATE,
    reason TEXT,
    modified_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_recurring_invoices_customer_id ON recurring_invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_recurring_invoices_status ON recurring_invoices(status);
CREATE INDEX IF NOT EXISTS idx_recurring_invoices_next_occurrence ON recurring_invoices(next_occurrence_date);
CREATE INDEX IF NOT EXISTS idx_recurring_invoice_instances_recurring_id ON recurring_invoice_instances(recurring_invoice_id);
CREATE INDEX IF NOT EXISTS idx_recurring_invoice_instances_scheduled_date ON recurring_invoice_instances(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_recurring_invoice_instances_status ON recurring_invoice_instances(status);
CREATE INDEX IF NOT EXISTS idx_recurring_invoice_modifications_recurring_id ON recurring_invoice_modifications(recurring_invoice_id);

-- Add trigger for updated_at
CREATE TRIGGER set_recurring_invoices_updated_at
BEFORE UPDATE ON recurring_invoices
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();