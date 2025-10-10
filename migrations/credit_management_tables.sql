-- Credit Management Tables
-- Task 36: Credit management implementation

-- Customer credit profiles
CREATE TABLE IF NOT EXISTS customer_credit_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    credit_limit DECIMAL(12,2) DEFAULT 0,
    current_balance DECIMAL(12,2) DEFAULT 0,
    available_credit DECIMAL(12,2) DEFAULT 0,
    credit_status VARCHAR(20) DEFAULT 'no_credit', -- excellent, good, fair, poor, very_poor, no_credit, suspended
    payment_behavior VARCHAR(30) DEFAULT 'no_history', -- on_time, occasionally_late, frequently_late, delinquent, default
    risk_level VARCHAR(20) DEFAULT 'unknown', -- low, medium, high, very_high, unacceptable
    days_sales_outstanding INT DEFAULT 0,
    last_payment_date DATE,
    last_review_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(customer_id)
);

-- Credit limit history
CREATE TABLE IF NOT EXISTS credit_limit_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    old_limit DECIMAL(12,2),
    new_limit DECIMAL(12,2) NOT NULL,
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    reason TEXT NOT NULL,
    approved_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Credit applications
CREATE TABLE IF NOT EXISTS credit_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    company_name VARCHAR(200) NOT NULL,
    tax_id VARCHAR(50),
    annual_revenue DECIMAL(15,2),
    years_in_business INT,
    requested_credit_limit DECIMAL(12,2) NOT NULL,
    trade_references JSONB DEFAULT '[]'::jsonb,
    bank_references JSONB DEFAULT '[]'::jsonb,
    financial_statements JSONB,
    application_status VARCHAR(20) DEFAULT 'pending', -- pending, approved, declined, withdrawn
    decision_date DATE,
    approved_limit DECIMAL(12,2),
    decline_reason TEXT,
    authorized_signature BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Credit checks
CREATE TABLE IF NOT EXISTS credit_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    check_type VARCHAR(20) NOT NULL, -- internal, bureau, comprehensive
    check_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    internal_score INT,
    bureau_score INT,
    bureau_provider VARCHAR(50), -- Equifax, Experian, D&B
    risk_level VARCHAR(20),
    recommended_limit DECIMAL(12,2),
    decision VARCHAR(20), -- approve, review, decline
    report_data JSONB,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trade references
CREATE TABLE IF NOT EXISTS customer_trade_references (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    company_name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    account_number VARCHAR(50),
    credit_limit DECIMAL(12,2),
    payment_history VARCHAR(50), -- excellent, good, fair, poor
    years_relationship INT,
    verified BOOLEAN DEFAULT false,
    verified_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Credit write-offs
CREATE TABLE IF NOT EXISTS credit_write_offs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id),
    amount DECIMAL(12,2) NOT NULL,
    reason TEXT NOT NULL,
    write_off_date DATE NOT NULL DEFAULT CURRENT_DATE,
    recovery_attempts INT DEFAULT 0,
    amount_recovered DECIMAL(12,2) DEFAULT 0,
    approved_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Collections accounts
CREATE TABLE IF NOT EXISTS collections_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    agency_name VARCHAR(100),
    sent_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_amount DECIMAL(12,2) NOT NULL,
    amount_recovered DECIMAL(12,2) DEFAULT 0,
    commission_rate DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'active', -- active, settled, returned, closed
    reason TEXT,
    return_date DATE,
    settlement_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Credit actions log
CREATE TABLE IF NOT EXISTS credit_actions_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL, -- increase_limit, decrease_limit, suspend, reinstate, write_off, send_to_collections
    amount DECIMAL(12,2),
    reason TEXT,
    approved_by VARCHAR(100),
    action_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Credit terms
CREATE TABLE IF NOT EXISTS credit_terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_name VARCHAR(50) NOT NULL UNIQUE,
    net_days INT NOT NULL, -- Net 30, Net 60, etc
    discount_percentage DECIMAL(5,2), -- Early payment discount
    discount_days INT, -- Days to qualify for discount
    late_fee_percentage DECIMAL(5,2),
    grace_period_days INT DEFAULT 0,
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_customer_credit_profiles_customer_id ON customer_credit_profiles(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_credit_profiles_credit_status ON customer_credit_profiles(credit_status);
CREATE INDEX IF NOT EXISTS idx_customer_credit_profiles_risk_level ON customer_credit_profiles(risk_level);
CREATE INDEX IF NOT EXISTS idx_credit_limit_history_customer_id ON credit_limit_history(customer_id);
CREATE INDEX IF NOT EXISTS idx_credit_limit_history_effective_date ON credit_limit_history(effective_date);
CREATE INDEX IF NOT EXISTS idx_credit_applications_customer_id ON credit_applications(customer_id);
CREATE INDEX IF NOT EXISTS idx_credit_applications_status ON credit_applications(application_status);
CREATE INDEX IF NOT EXISTS idx_credit_checks_customer_id ON credit_checks(customer_id);
CREATE INDEX IF NOT EXISTS idx_credit_checks_check_date ON credit_checks(check_date);
CREATE INDEX IF NOT EXISTS idx_credit_write_offs_customer_id ON credit_write_offs(customer_id);
CREATE INDEX IF NOT EXISTS idx_collections_accounts_customer_id ON collections_accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_collections_accounts_status ON collections_accounts(status);
CREATE INDEX IF NOT EXISTS idx_credit_actions_log_customer_id ON credit_actions_log(customer_id);
CREATE INDEX IF NOT EXISTS idx_credit_actions_log_action_date ON credit_actions_log(action_date);

-- Default credit terms
INSERT INTO credit_terms (term_name, net_days, discount_percentage, discount_days, late_fee_percentage, is_default)
VALUES 
    ('Net 30', 30, 2.0, 10, 1.5, true),
    ('Net 15', 15, 1.0, 5, 2.0, false),
    ('Net 60', 60, 0, 0, 1.0, false),
    ('Due on Receipt', 0, 0, 0, 2.5, false),
    ('2/10 Net 30', 30, 2.0, 10, 1.5, false)
ON CONFLICT (term_name) DO NOTHING;

-- Function to update credit profile balances
CREATE OR REPLACE FUNCTION update_credit_profile_balance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update current balance based on outstanding invoices
    UPDATE customer_credit_profiles
    SET current_balance = (
            SELECT COALESCE(SUM(balance_cents), 0) / 100.0
            FROM invoices
            WHERE customer_id = NEW.customer_id
                AND status NOT IN ('paid', 'cancelled')
        ),
        available_credit = credit_limit - (
            SELECT COALESCE(SUM(balance_cents), 0) / 100.0
            FROM invoices
            WHERE customer_id = NEW.customer_id
                AND status NOT IN ('paid', 'cancelled')
        ),
        updated_at = NOW()
    WHERE customer_id = NEW.customer_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for invoice changes
CREATE TRIGGER trigger_update_credit_balance
AFTER INSERT OR UPDATE OR DELETE ON invoices
FOR EACH ROW
EXECUTE FUNCTION update_credit_profile_balance();

-- Function to calculate credit risk
CREATE OR REPLACE FUNCTION calculate_credit_risk(customer_uuid UUID)
RETURNS VARCHAR AS $$
DECLARE
    overdue_count INT;
    avg_days_late NUMERIC;
    utilization_rate NUMERIC;
    risk VARCHAR;
BEGIN
    -- Get overdue invoice count
    SELECT COUNT(*), AVG(CURRENT_DATE - due_date)
    INTO overdue_count, avg_days_late
    FROM invoices
    WHERE customer_id = customer_uuid
        AND status = 'overdue';
    
    -- Get credit utilization
    SELECT CASE 
        WHEN cp.credit_limit > 0 THEN cp.current_balance / cp.credit_limit
        ELSE 1.0
    END INTO utilization_rate
    FROM customer_credit_profiles cp
    WHERE cp.customer_id = customer_uuid;
    
    -- Calculate risk level
    IF overdue_count > 5 OR avg_days_late > 60 OR utilization_rate > 0.9 THEN
        risk := 'very_high';
    ELSIF overdue_count > 2 OR avg_days_late > 30 OR utilization_rate > 0.75 THEN
        risk := 'high';
    ELSIF overdue_count > 0 OR avg_days_late > 15 OR utilization_rate > 0.5 THEN
        risk := 'medium';
    ELSE
        risk := 'low';
    END IF;
    
    RETURN risk;
END;
$$ LANGUAGE plpgsql;

-- Update timestamps trigger
CREATE TRIGGER set_customer_credit_profiles_updated_at
BEFORE UPDATE ON customer_credit_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_credit_applications_updated_at
BEFORE UPDATE ON credit_applications
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_collections_accounts_updated_at
BEFORE UPDATE ON collections_accounts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_credit_terms_updated_at
BEFORE UPDATE ON credit_terms
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();