-- Create missing invoice tables with proper UUID columns
-- Task 31: Invoice management implementation

-- Payment records
CREATE TABLE IF NOT EXISTS invoice_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    payment_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL, -- cash, check, credit_card, ach, other
    reference_number VARCHAR(100),
    notes TEXT,
    transaction_id VARCHAR(100),
    gateway_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

-- Invoice activity log
CREATE TABLE IF NOT EXISTS invoice_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- created, sent, viewed, payment_received, reminder_sent, etc
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

-- Add missing columns to invoices table if they don't exist
DO $$
BEGIN
    -- Add issue_date column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'invoices' AND column_name = 'issue_date') THEN
        ALTER TABLE invoices ADD COLUMN issue_date DATE DEFAULT CURRENT_DATE;
    END IF;
    
    -- Add internal_notes column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'invoices' AND column_name = 'internal_notes') THEN
        ALTER TABLE invoices ADD COLUMN internal_notes TEXT;
    END IF;
    
    -- Add reminder_sent_count column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'invoices' AND column_name = 'reminder_sent_count') THEN
        ALTER TABLE invoices ADD COLUMN reminder_sent_count INT DEFAULT 0;
    END IF;
    
    -- Add last_reminder_date column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'invoices' AND column_name = 'last_reminder_date') THEN
        ALTER TABLE invoices ADD COLUMN last_reminder_date TIMESTAMPTZ;
    END IF;
    
    -- Add overdue_date column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'invoices' AND column_name = 'overdue_date') THEN
        ALTER TABLE invoices ADD COLUMN overdue_date DATE;
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_invoice_payments_invoice_id ON invoice_payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_payments_payment_date ON invoice_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_invoice_activities_invoice_id ON invoice_activities(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoices_issue_date ON invoices(issue_date);

-- Trigger for updating balance_due
CREATE OR REPLACE FUNCTION update_invoice_balance()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE invoices
    SET amount_paid_cents = (
            SELECT COALESCE(SUM(amount * 100), 0)::integer
            FROM invoice_payments
            WHERE invoice_id = COALESCE(NEW.invoice_id, OLD.invoice_id)
        ),
        balance_cents = total_cents - (
            SELECT COALESCE(SUM(amount * 100), 0)::integer
            FROM invoice_payments
            WHERE invoice_id = COALESCE(NEW.invoice_id, OLD.invoice_id)
        ),
        status = CASE
            WHEN total_cents <= (
                SELECT COALESCE(SUM(amount * 100), 0)::integer
                FROM invoice_payments
                WHERE invoice_id = COALESCE(NEW.invoice_id, OLD.invoice_id)
            ) THEN 'paid'
            WHEN (
                SELECT COALESCE(SUM(amount * 100), 0)::integer
                FROM invoice_payments
                WHERE invoice_id = COALESCE(NEW.invoice_id, OLD.invoice_id)
            ) > 0 THEN 'partial'
            ELSE status
        END,
        updated_at = NOW()
    WHERE id = COALESCE(NEW.invoice_id, OLD.invoice_id);
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_invoice_balance ON invoice_payments;
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
        AND balance_cents > 0;
END;
$$ LANGUAGE plpgsql;