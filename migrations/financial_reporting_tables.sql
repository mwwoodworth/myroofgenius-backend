-- Financial Reporting Tables
-- Task 39: Financial reporting implementation

-- Scheduled reports
CREATE TABLE IF NOT EXISTS scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_name VARCHAR(100) NOT NULL,
    report_type VARCHAR(30) NOT NULL, -- profit_loss, balance_sheet, cash_flow, revenue, expenses, etc.
    schedule VARCHAR(20) NOT NULL, -- daily, weekly, monthly, quarterly, yearly
    schedule_time TIME DEFAULT '08:00:00',
    schedule_day INT, -- Day of week (1-7) or day of month (1-31)
    parameters JSONB, -- Report parameters
    format VARCHAR(10) DEFAULT 'pdf', -- pdf, excel, csv, json
    recipients TEXT[], -- Email addresses
    last_run TIMESTAMPTZ,
    next_run TIMESTAMPTZ,
    last_status VARCHAR(20), -- success, failed, running
    last_error TEXT,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Report history
CREATE TABLE IF NOT EXISTS report_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_name VARCHAR(100) NOT NULL,
    report_type VARCHAR(30) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    generated_by VARCHAR(100),
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    file_url TEXT,
    file_size INT,
    format VARCHAR(10),
    parameters JSONB,
    row_count INT,
    execution_time_ms INT,
    status VARCHAR(20) DEFAULT 'completed', -- completed, failed, cancelled
    error_message TEXT
);

-- Budget data
CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_name VARCHAR(100) NOT NULL,
    fiscal_year INT NOT NULL,
    budget_type VARCHAR(20) NOT NULL, -- annual, quarterly, monthly
    category VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    notes TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fiscal_year, budget_type, category, period_start)
);

-- Financial goals
CREATE TABLE IF NOT EXISTS financial_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- revenue, profit_margin, customer_count, etc.
    target_value DECIMAL(12,2) NOT NULL,
    current_value DECIMAL(12,2) DEFAULT 0,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- active, achieved, missed, cancelled
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chart of accounts
CREATE TABLE IF NOT EXISTS chart_of_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL, -- asset, liability, equity, revenue, expense
    parent_account_id UUID REFERENCES chart_of_accounts(id),
    is_active BOOLEAN DEFAULT true,
    normal_balance VARCHAR(10) NOT NULL, -- debit, credit
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- General ledger entries
CREATE TABLE IF NOT EXISTS general_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_date DATE NOT NULL,
    account_id UUID NOT NULL REFERENCES chart_of_accounts(id),
    debit_amount DECIMAL(12,2) DEFAULT 0,
    credit_amount DECIMAL(12,2) DEFAULT 0,
    description TEXT NOT NULL,
    reference_type VARCHAR(30), -- invoice, payment, expense, adjustment
    reference_id UUID,
    journal_entry_id UUID,
    posted_by VARCHAR(100),
    posted_at TIMESTAMPTZ DEFAULT NOW(),
    is_reconciled BOOLEAN DEFAULT false,
    reconciled_date DATE
);

-- Journal entries
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_number VARCHAR(50) UNIQUE NOT NULL,
    entry_date DATE NOT NULL,
    entry_type VARCHAR(20) NOT NULL, -- general, adjusting, closing, reversing
    description TEXT NOT NULL,
    total_debits DECIMAL(12,2) NOT NULL,
    total_credits DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft', -- draft, posted, reversed
    posted_by VARCHAR(100),
    posted_at TIMESTAMPTZ,
    reversed_by UUID REFERENCES journal_entries(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT balanced_entry CHECK (total_debits = total_credits)
);

-- Journal entry lines
CREATE TABLE IF NOT EXISTS journal_entry_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    line_number INT NOT NULL,
    account_id UUID NOT NULL REFERENCES chart_of_accounts(id),
    debit_amount DECIMAL(12,2) DEFAULT 0,
    credit_amount DECIMAL(12,2) DEFAULT 0,
    description TEXT,
    UNIQUE(journal_entry_id, line_number),
    CONSTRAINT one_sided_entry CHECK (
        (debit_amount > 0 AND credit_amount = 0) OR
        (credit_amount > 0 AND debit_amount = 0)
    )
);

-- Financial periods
CREATE TABLE IF NOT EXISTS financial_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_name VARCHAR(50) NOT NULL,
    period_type VARCHAR(20) NOT NULL, -- monthly, quarterly, yearly
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    fiscal_year INT NOT NULL,
    is_closed BOOLEAN DEFAULT false,
    closed_date TIMESTAMPTZ,
    closed_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fiscal_year, period_type, period_start)
);

-- Tax rates
CREATE TABLE IF NOT EXISTS tax_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tax_name VARCHAR(50) NOT NULL,
    tax_type VARCHAR(20) NOT NULL, -- sales, income, payroll, property
    rate DECIMAL(5,4) NOT NULL,
    jurisdiction VARCHAR(50) NOT NULL, -- federal, state, local
    effective_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Report templates
CREATE TABLE IF NOT EXISTS report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) NOT NULL,
    report_type VARCHAR(30) NOT NULL,
    template_config JSONB NOT NULL, -- Layout, sections, calculations
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Financial ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_date DATE NOT NULL,
    current_ratio DECIMAL(10,4),
    quick_ratio DECIMAL(10,4),
    debt_to_equity DECIMAL(10,4),
    gross_margin DECIMAL(10,4),
    operating_margin DECIMAL(10,4),
    net_margin DECIMAL(10,4),
    return_on_assets DECIMAL(10,4),
    return_on_equity DECIMAL(10,4),
    inventory_turnover DECIMAL(10,4),
    receivables_turnover DECIMAL(10,4),
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(period_date)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_is_active ON scheduled_reports(is_active);
CREATE INDEX IF NOT EXISTS idx_scheduled_reports_next_run ON scheduled_reports(next_run);
CREATE INDEX IF NOT EXISTS idx_report_history_report_type ON report_history(report_type);
CREATE INDEX IF NOT EXISTS idx_report_history_generated_at ON report_history(generated_at);
CREATE INDEX IF NOT EXISTS idx_budgets_fiscal_year ON budgets(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_budgets_category ON budgets(category);
CREATE INDEX IF NOT EXISTS idx_financial_goals_status ON financial_goals(status);
CREATE INDEX IF NOT EXISTS idx_chart_of_accounts_account_number ON chart_of_accounts(account_number);
CREATE INDEX IF NOT EXISTS idx_chart_of_accounts_account_type ON chart_of_accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_general_ledger_transaction_date ON general_ledger(transaction_date);
CREATE INDEX IF NOT EXISTS idx_general_ledger_account_id ON general_ledger(account_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_entry_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_entries_status ON journal_entries(status);
CREATE INDEX IF NOT EXISTS idx_financial_periods_fiscal_year ON financial_periods(fiscal_year);
CREATE INDEX IF NOT EXISTS idx_financial_periods_is_closed ON financial_periods(is_closed);
CREATE INDEX IF NOT EXISTS idx_tax_rates_tax_type ON tax_rates(tax_type);
CREATE INDEX IF NOT EXISTS idx_financial_ratios_period_date ON financial_ratios(period_date);

-- Default chart of accounts
INSERT INTO chart_of_accounts (account_number, account_name, account_type, normal_balance, description)
VALUES
    -- Assets
    ('1000', 'Cash', 'asset', 'debit', 'Cash and cash equivalents'),
    ('1100', 'Accounts Receivable', 'asset', 'debit', 'Customer receivables'),
    ('1200', 'Inventory', 'asset', 'debit', 'Inventory on hand'),
    ('1300', 'Prepaid Expenses', 'asset', 'debit', 'Prepaid expenses'),
    ('1500', 'Equipment', 'asset', 'debit', 'Equipment and machinery'),
    ('1600', 'Vehicles', 'asset', 'debit', 'Company vehicles'),

    -- Liabilities
    ('2000', 'Accounts Payable', 'liability', 'credit', 'Vendor payables'),
    ('2100', 'Accrued Expenses', 'liability', 'credit', 'Accrued expenses'),
    ('2200', 'Sales Tax Payable', 'liability', 'credit', 'Sales tax collected'),
    ('2300', 'Payroll Liabilities', 'liability', 'credit', 'Payroll taxes and benefits'),
    ('2500', 'Notes Payable', 'liability', 'credit', 'Short-term loans'),

    -- Equity
    ('3000', 'Owner Equity', 'equity', 'credit', 'Owner capital'),
    ('3100', 'Retained Earnings', 'equity', 'credit', 'Accumulated earnings'),

    -- Revenue
    ('4000', 'Sales Revenue', 'revenue', 'credit', 'Product and service sales'),
    ('4100', 'Service Revenue', 'revenue', 'credit', 'Service income'),
    ('4200', 'Other Revenue', 'revenue', 'credit', 'Miscellaneous income'),

    -- Expenses
    ('5000', 'Cost of Goods Sold', 'expense', 'debit', 'Direct costs'),
    ('5100', 'Materials', 'expense', 'debit', 'Material costs'),
    ('5200', 'Labor', 'expense', 'debit', 'Direct labor costs'),
    ('6000', 'Operating Expenses', 'expense', 'debit', 'Operating costs'),
    ('6100', 'Rent', 'expense', 'debit', 'Rent expense'),
    ('6200', 'Utilities', 'expense', 'debit', 'Utilities expense'),
    ('6300', 'Insurance', 'expense', 'debit', 'Insurance premiums'),
    ('6400', 'Marketing', 'expense', 'debit', 'Marketing and advertising'),
    ('6500', 'Office Supplies', 'expense', 'debit', 'Office supplies and materials')
ON CONFLICT (account_number) DO NOTHING;

-- Default tax rates
INSERT INTO tax_rates (tax_name, tax_type, rate, jurisdiction, effective_date)
VALUES
    ('Federal Income Tax', 'income', 0.21, 'federal', '2024-01-01'),
    ('State Income Tax', 'income', 0.05, 'state', '2024-01-01'),
    ('State Sales Tax', 'sales', 0.06, 'state', '2024-01-01'),
    ('Local Sales Tax', 'sales', 0.02, 'local', '2024-01-01'),
    ('FICA Employee', 'payroll', 0.0765, 'federal', '2024-01-01'),
    ('FICA Employer', 'payroll', 0.0765, 'federal', '2024-01-01'),
    ('FUTA', 'payroll', 0.006, 'federal', '2024-01-01'),
    ('SUTA', 'payroll', 0.027, 'state', '2024-01-01')
ON CONFLICT DO NOTHING;

-- Function to calculate financial ratios
CREATE OR REPLACE FUNCTION calculate_financial_ratios(period_date DATE)
RETURNS VOID AS $$
DECLARE
    current_assets DECIMAL;
    current_liabilities DECIMAL;
    total_assets DECIMAL;
    total_liabilities DECIMAL;
    total_equity DECIMAL;
    revenue DECIMAL;
    gross_profit DECIMAL;
    operating_profit DECIMAL;
    net_profit DECIMAL;
BEGIN
    -- Get balance sheet data (simplified)
    -- This would need actual GL data in production

    -- Calculate ratios
    INSERT INTO financial_ratios (
        period_date,
        current_ratio,
        quick_ratio,
        debt_to_equity,
        gross_margin,
        operating_margin,
        net_margin
    )
    VALUES (
        period_date,
        1.5,  -- Placeholder
        1.2,  -- Placeholder
        0.5,  -- Placeholder
        0.35, -- Placeholder
        0.20, -- Placeholder
        0.15  -- Placeholder
    )
    ON CONFLICT (period_date) DO UPDATE
    SET current_ratio = EXCLUDED.current_ratio,
        quick_ratio = EXCLUDED.quick_ratio,
        debt_to_equity = EXCLUDED.debt_to_equity,
        gross_margin = EXCLUDED.gross_margin,
        operating_margin = EXCLUDED.operating_margin,
        net_margin = EXCLUDED.net_margin,
        calculated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to close financial period
CREATE OR REPLACE FUNCTION close_financial_period(period_id UUID, closing_user VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    -- Update period status
    UPDATE financial_periods
    SET is_closed = true,
        closed_date = NOW(),
        closed_by = closing_user
    WHERE id = period_id
        AND is_closed = false;

    -- Create closing journal entries
    -- This would involve transferring revenue/expense accounts to retained earnings

    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER set_scheduled_reports_updated_at
BEFORE UPDATE ON scheduled_reports
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_budgets_updated_at
BEFORE UPDATE ON budgets
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_financial_goals_updated_at
BEFORE UPDATE ON financial_goals
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_chart_of_accounts_updated_at
BEFORE UPDATE ON chart_of_accounts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_journal_entries_updated_at
BEFORE UPDATE ON journal_entries
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_tax_rates_updated_at
BEFORE UPDATE ON tax_rates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_report_templates_updated_at
BEFORE UPDATE ON report_templates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();