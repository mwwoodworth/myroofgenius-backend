-- Invoice Management Tables
-- Task 31: Invoice management implementation

-- Invoice table
CREATE TABLE IF NOT EXISTS invoices (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(id),
    job_id VARCHAR(50) REFERENCES jobs(id),
    estimate_id VARCHAR(50) REFERENCES estimates(id),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    amount_paid DECIMAL(12,2) DEFAULT 0,
    balance_due DECIMAL(12,2) NOT NULL DEFAULT 0,
    payment_terms VARCHAR(100),
    notes TEXT,
    internal_notes TEXT,
    sent_date TIMESTAMPTZ,
    viewed_date TIMESTAMPTZ,
    paid_date TIMESTAMPTZ,
    overdue_date DATE,
    reminder_sent_count INT DEFAULT 0,
    last_reminder_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(50),
    updated_by VARCHAR(50)
);

-- Invoice line items
CREATE TABLE IF NOT EXISTS invoice_items (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    invoice_id VARCHAR(50) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    item_type VARCHAR(20) NOT NULL, -- service, material, expense, other
    description TEXT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL DEFAULT 1,
    unit_price DECIMAL(12,2) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    total DECIMAL(12,2) NOT NULL,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payment records
CREATE TABLE IF NOT EXISTS invoice_payments (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    invoice_id VARCHAR(50) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL, -- cash, check, credit_card, ach, other
    reference_number VARCHAR(100),
    notes TEXT,
    transaction_id VARCHAR(100),
    gateway_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(50)
);

-- Invoice activity log
CREATE TABLE IF NOT EXISTS invoice_activities (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    invoice_id VARCHAR(50) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- created, sent, viewed, payment_received, reminder_sent, etc
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(50)
);

-- Invoice templates (for Task 32)
CREATE TABLE IF NOT EXISTS invoice_templates (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    template_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    payment_terms VARCHAR(100),
    default_notes TEXT,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoice template items
CREATE TABLE IF NOT EXISTS invoice_template_items (
    id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    template_id VARCHAR(50) NOT NULL REFERENCES invoice_templates(id) ON DELETE CASCADE,
    item_type VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    default_quantity DECIMAL(10,2) DEFAULT 1,
    default_price DECIMAL(12,2),
    tax_rate DECIMAL(5,2) DEFAULT 0,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_job_id ON invoices(job_id);
CREATE INDEX IF NOT EXISTS idx_invoices_estimate_id ON invoices(estimate_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_invoices_issue_date ON invoices(issue_date);
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id ON invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_invoice_id ON invoice_payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_payment_date ON invoice_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_invoice_activities_invoice_id ON invoice_activities(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_templates_category ON invoice_templates(category);

-- Trigger for updating balance_due
CREATE OR REPLACE FUNCTION update_invoice_balance()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE invoices
    SET amount_paid = (
            SELECT COALESCE(SUM(amount), 0)
            FROM invoice_payments
            WHERE invoice_id = NEW.invoice_id
        ),
        balance_due = total_amount - (
            SELECT COALESCE(SUM(amount), 0)
            FROM invoice_payments
            WHERE invoice_id = NEW.invoice_id
        ),
        status = CASE
            WHEN total_amount <= (
                SELECT COALESCE(SUM(amount), 0)
                FROM invoice_payments
                WHERE invoice_id = NEW.invoice_id
            ) THEN 'paid'
            WHEN (
                SELECT COALESCE(SUM(amount), 0)
                FROM invoice_payments
                WHERE invoice_id = NEW.invoice_id
            ) > 0 THEN 'partial'
            ELSE status
        END,
        updated_at = NOW()
    WHERE id = NEW.invoice_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_invoice_balance
AFTER INSERT OR UPDATE OR DELETE ON invoice_payments
FOR EACH ROW
EXECUTE FUNCTION update_invoice_balance();

-- Function to check for overdue invoices
CREATE OR REPLACE FUNCTION check_overdue_invoices()
RETURNS void AS $$
BEGIN
    UPDATE invoices
    SET status = 'overdue',
        overdue_date = CURRENT_DATE
    WHERE status IN ('sent', 'viewed', 'partial')
        AND due_date < CURRENT_DATE
        AND balance_due > 0;
END;
$$ LANGUAGE plpgsql;

-- Create updated_at trigger
CREATE TRIGGER set_invoices_updated_at
BEFORE UPDATE ON invoices
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_invoice_items_updated_at
BEFORE UPDATE ON invoice_items
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_invoice_templates_updated_at
BEFORE UPDATE ON invoice_templates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();