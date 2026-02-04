-- Payment Processing Tables
-- Task 33: Payment processing implementation

-- Payment refunds table
CREATE TABLE IF NOT EXISTS payment_refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES invoice_payments(id) ON DELETE CASCADE,
    refund_date DATE NOT NULL DEFAULT CURRENT_DATE,
    amount DECIMAL(12,2) NOT NULL,
    reason VARCHAR(50) NOT NULL,
    notes TEXT,
    transaction_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed',
    gateway_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    tenant_id UUID NOT NULL
);

-- Payment plans table
CREATE TABLE IF NOT EXISTS payment_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    total_amount DECIMAL(12,2) NOT NULL,
    down_payment DECIMAL(12,2) DEFAULT 0,
    installments INT NOT NULL,
    installment_amount DECIMAL(12,2) NOT NULL,
    frequency VARCHAR(20) NOT NULL, -- weekly, biweekly, monthly
    start_date DATE NOT NULL,
    end_date DATE,
    auto_charge BOOLEAN DEFAULT false,
    payment_method VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active', -- active, completed, cancelled, defaulted
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payment plan installments
CREATE TABLE IF NOT EXISTS payment_plan_installments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES payment_plans(id) ON DELETE CASCADE,
    installment_number INT NOT NULL,
    due_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    paid_amount DECIMAL(12,2) DEFAULT 0,
    payment_id UUID REFERENCES invoice_payments(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, paid, overdue, cancelled
    paid_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Saved payment methods
CREATE TABLE IF NOT EXISTS saved_payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    payment_method VARCHAR(50) NOT NULL,
    last_four VARCHAR(4),
    brand VARCHAR(50),
    bank_name VARCHAR(100),
    account_type VARCHAR(20),
    expiry_month INT,
    expiry_year INT,
    is_default BOOLEAN DEFAULT false,
    stripe_payment_method_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payment gateway logs
CREATE TABLE IF NOT EXISTS payment_gateway_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID REFERENCES invoice_payments(id),
    gateway VARCHAR(50) NOT NULL, -- stripe, square, paypal, etc
    event_type VARCHAR(100),
    request_data JSONB,
    response_data JSONB,
    status_code INT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_payment_refunds_payment_id ON payment_refunds(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_refunds_refund_date ON payment_refunds(refund_date);
CREATE INDEX IF NOT EXISTS idx_payment_plans_invoice_id ON payment_plans(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payment_plans_status ON payment_plans(status);
CREATE INDEX IF NOT EXISTS idx_payment_plan_installments_plan_id ON payment_plan_installments(plan_id);
CREATE INDEX IF NOT EXISTS idx_payment_plan_installments_due_date ON payment_plan_installments(due_date);
CREATE INDEX IF NOT EXISTS idx_saved_payment_methods_customer_id ON saved_payment_methods(customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_gateway_logs_payment_id ON payment_gateway_logs(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_gateway_logs_created_at ON payment_gateway_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_payment_refunds_tenant_id ON payment_refunds(tenant_id);
CREATE INDEX IF NOT EXISTS idx_payment_gateway_logs_tenant_id ON payment_gateway_logs(tenant_id);

-- Function to update payment plan status
CREATE OR REPLACE FUNCTION update_payment_plan_status()
RETURNS TRIGGER AS $$
DECLARE
    total_paid DECIMAL;
    total_due DECIMAL;
BEGIN
    -- Calculate total paid and due
    SELECT 
        COALESCE(SUM(paid_amount), 0),
        COALESCE(SUM(amount), 0)
    INTO total_paid, total_due
    FROM payment_plan_installments
    WHERE plan_id = NEW.plan_id;
    
    -- Update plan status
    UPDATE payment_plans
    SET status = CASE
        WHEN total_paid >= total_due THEN 'completed'
        WHEN EXISTS (
            SELECT 1 FROM payment_plan_installments
            WHERE plan_id = NEW.plan_id
            AND due_date < CURRENT_DATE
            AND status = 'overdue'
        ) THEN 'defaulted'
        ELSE 'active'
    END,
    updated_at = NOW()
    WHERE id = NEW.plan_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_payment_plan_status
AFTER UPDATE ON payment_plan_installments
FOR EACH ROW
WHEN (OLD.status IS DISTINCT FROM NEW.status)
EXECUTE FUNCTION update_payment_plan_status();

-- Function to check for overdue installments
CREATE OR REPLACE FUNCTION check_overdue_installments()
RETURNS void AS $$
BEGIN
    UPDATE payment_plan_installments
    SET status = 'overdue'
    WHERE status = 'pending'
        AND due_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;
