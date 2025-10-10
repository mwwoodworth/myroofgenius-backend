-- Sales & CRM Management Tables - Tasks 61-70
-- Complete sales and customer relationship management system

-- Task 61: Lead Management
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_number VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    mobile VARCHAR(50),
    website VARCHAR(500),
    industry VARCHAR(100),
    company_size VARCHAR(50),
    annual_revenue DECIMAL(15,2),
    lead_source VARCHAR(100) NOT NULL,
    lead_status VARCHAR(50) NOT NULL DEFAULT 'new',
    lead_score INTEGER DEFAULT 0,
    rating VARCHAR(20),
    assigned_to VARCHAR(100),
    territory_id UUID,
    address_line1 VARCHAR(500),
    address_line2 VARCHAR(500),
    city VARCHAR(200),
    state VARCHAR(100),
    postal_code VARCHAR(50),
    country VARCHAR(100),
    description TEXT,
    notes TEXT,
    tags TEXT[],
    last_contacted_at TIMESTAMP WITH TIME ZONE,
    converted_to_customer BOOLEAN DEFAULT false,
    converted_customer_id UUID,
    converted_at TIMESTAMP WITH TIME ZONE,
    converted_by VARCHAR(100),
    lost_reason VARCHAR(200),
    lost_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Lead Activities
CREATE TABLE IF NOT EXISTS lead_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    description TEXT,
    outcome VARCHAR(100),
    scheduled_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    assigned_to VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Task 62: Opportunity Tracking
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_number VARCHAR(50) UNIQUE NOT NULL,
    opportunity_name VARCHAR(200) NOT NULL,
    account_id UUID,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    customer_id UUID,
    stage VARCHAR(100) NOT NULL,
    probability INTEGER DEFAULT 0,
    amount DECIMAL(15,2) NOT NULL,
    expected_revenue DECIMAL(15,2),
    close_date DATE NOT NULL,
    opportunity_type VARCHAR(100),
    lead_source VARCHAR(100),
    next_step TEXT,
    description TEXT,
    competitor_names TEXT[],
    assigned_to VARCHAR(100) NOT NULL,
    territory_id UUID,
    campaign_id UUID,
    forecast_category VARCHAR(50),
    is_closed BOOLEAN DEFAULT false,
    is_won BOOLEAN DEFAULT false,
    closed_date DATE,
    lost_reason VARCHAR(200),
    lost_to_competitor VARCHAR(200),
    contract_id UUID,
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Opportunity Products
CREATE TABLE IF NOT EXISTS opportunity_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    product_id UUID,
    product_name VARCHAR(200) NOT NULL,
    product_code VARCHAR(100),
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    total_price DECIMAL(15,2) NOT NULL,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task 63: Sales Pipeline
CREATE TABLE IF NOT EXISTS sales_pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name VARCHAR(200) NOT NULL UNIQUE,
    pipeline_type VARCHAR(50) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT false,
    stages JSONB NOT NULL DEFAULT '[]',
    stage_probabilities JSONB DEFAULT '{}',
    stage_durations JSONB DEFAULT '{}',
    conversion_rates JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pipeline Stage History
CREATE TABLE IF NOT EXISTS pipeline_stage_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    pipeline_id UUID NOT NULL REFERENCES sales_pipelines(id) ON DELETE CASCADE,
    from_stage VARCHAR(100),
    to_stage VARCHAR(100) NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_in_stage_days INTEGER,
    notes TEXT
);

-- Task 64: Quote Management
CREATE TABLE IF NOT EXISTS quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_number VARCHAR(50) UNIQUE NOT NULL,
    quote_name VARCHAR(200) NOT NULL,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    customer_id UUID,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    valid_from DATE NOT NULL,
    valid_until DATE NOT NULL,
    subtotal DECIMAL(15,2) NOT NULL,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    shipping_amount DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    currency_code VARCHAR(3) DEFAULT 'USD',
    payment_terms VARCHAR(200),
    delivery_terms VARCHAR(200),
    notes TEXT,
    internal_notes TEXT,
    terms_and_conditions TEXT,
    prepared_by VARCHAR(100) NOT NULL,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    viewed_at TIMESTAMP WITH TIME ZONE,
    accepted_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    converted_to_order BOOLEAN DEFAULT false,
    order_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quote Line Items
CREATE TABLE IF NOT EXISTS quote_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quote_id UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
    product_id UUID,
    product_name VARCHAR(200) NOT NULL,
    product_code VARCHAR(100),
    description TEXT,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(12,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task 65: Proposal Generation
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_number VARCHAR(50) UNIQUE NOT NULL,
    proposal_title VARCHAR(500) NOT NULL,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    quote_id UUID REFERENCES quotes(id) ON DELETE SET NULL,
    customer_id UUID,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    template_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    executive_summary TEXT,
    problem_statement TEXT,
    proposed_solution TEXT,
    scope_of_work TEXT,
    deliverables TEXT[],
    timeline TEXT,
    investment_summary TEXT,
    terms_and_conditions TEXT,
    appendices JSONB DEFAULT '[]',
    valid_until DATE,
    prepared_by VARCHAR(100) NOT NULL,
    reviewed_by VARCHAR(100),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    viewed_at TIMESTAMP WITH TIME ZONE,
    accepted_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    version INTEGER DEFAULT 1,
    parent_proposal_id UUID,
    attachments TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Proposal Templates
CREATE TABLE IF NOT EXISTS proposal_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(200) NOT NULL UNIQUE,
    template_type VARCHAR(100),
    description TEXT,
    sections JSONB NOT NULL DEFAULT '[]',
    default_terms TEXT,
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task 66: Contract Management
CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    contract_name VARCHAR(200) NOT NULL,
    contract_type VARCHAR(100) NOT NULL,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    quote_id UUID REFERENCES quotes(id) ON DELETE SET NULL,
    proposal_id UUID REFERENCES proposals(id) ON DELETE SET NULL,
    customer_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    renewal_date DATE,
    contract_value DECIMAL(15,2) NOT NULL,
    payment_terms VARCHAR(500),
    billing_frequency VARCHAR(50),
    auto_renewal BOOLEAN DEFAULT false,
    renewal_terms TEXT,
    termination_clause TEXT,
    sla_terms TEXT,
    special_terms TEXT,
    signed_date DATE,
    signed_by_customer VARCHAR(200),
    signed_by_company VARCHAR(200),
    contract_owner VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    attachments TEXT[],
    parent_contract_id UUID,
    amendment_number INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Contract Milestones
CREATE TABLE IF NOT EXISTS contract_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    milestone_name VARCHAR(200) NOT NULL,
    milestone_date DATE NOT NULL,
    milestone_value DECIMAL(12,2),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    completed_date DATE,
    invoice_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task 67: Commission Tracking
CREATE TABLE IF NOT EXISTS commission_structures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    structure_name VARCHAR(200) NOT NULL UNIQUE,
    structure_type VARCHAR(50) NOT NULL,
    description TEXT,
    base_rate DECIMAL(5,2),
    tier_rates JSONB DEFAULT '[]',
    product_rates JSONB DEFAULT '{}',
    territory_rates JSONB DEFAULT '{}',
    bonus_conditions JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    effective_date DATE NOT NULL,
    expiry_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Commission Calculations
CREATE TABLE IF NOT EXISTS commissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sales_rep VARCHAR(100) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    contract_id UUID REFERENCES contracts(id) ON DELETE SET NULL,
    invoice_id UUID,
    sale_amount DECIMAL(15,2) NOT NULL,
    commission_rate DECIMAL(5,2) NOT NULL,
    commission_amount DECIMAL(12,2) NOT NULL,
    bonus_amount DECIMAL(12,2) DEFAULT 0,
    total_commission DECIMAL(12,2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,
    paid_date DATE,
    payment_reference VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task 68: Sales Forecasting
CREATE TABLE IF NOT EXISTS sales_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_name VARCHAR(200) NOT NULL,
    forecast_period VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    forecast_type VARCHAR(50) NOT NULL,
    sales_rep VARCHAR(100),
    territory_id UUID,
    team_id UUID,
    pipeline_coverage DECIMAL(15,2),
    committed_amount DECIMAL(15,2),
    best_case_amount DECIMAL(15,2),
    most_likely_amount DECIMAL(15,2),
    worst_case_amount DECIMAL(15,2),
    closed_amount DECIMAL(15,2),
    quota_amount DECIMAL(15,2),
    attainment_percentage DECIMAL(5,2),
    opportunities_count INTEGER,
    weighted_pipeline DECIMAL(15,2),
    forecast_category_breakdown JSONB DEFAULT '{}',
    stage_breakdown JSONB DEFAULT '{}',
    assumptions TEXT,
    risks TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Forecast Adjustments
CREATE TABLE IF NOT EXISTS forecast_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_id UUID NOT NULL REFERENCES sales_forecasts(id) ON DELETE CASCADE,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    adjustment_type VARCHAR(50) NOT NULL,
    original_amount DECIMAL(15,2),
    adjusted_amount DECIMAL(15,2),
    adjustment_reason TEXT NOT NULL,
    adjusted_by VARCHAR(100) NOT NULL,
    adjusted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task 69: Territory Management
CREATE TABLE IF NOT EXISTS territories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    territory_code VARCHAR(50) UNIQUE NOT NULL,
    territory_name VARCHAR(200) NOT NULL,
    territory_type VARCHAR(50) NOT NULL,
    parent_territory_id UUID,
    description TEXT,
    geographic_area TEXT,
    countries TEXT[],
    states TEXT[],
    cities TEXT[],
    postal_codes TEXT[],
    industry_segments TEXT[],
    customer_segments TEXT[],
    account_size_range JSONB DEFAULT '{}',
    annual_quota DECIMAL(15,2),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Territory Assignments
CREATE TABLE IF NOT EXISTS territory_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    territory_id UUID NOT NULL REFERENCES territories(id) ON DELETE CASCADE,
    sales_rep VARCHAR(100) NOT NULL,
    role VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    quota_amount DECIMAL(15,2),
    commission_structure_id UUID REFERENCES commission_structures(id) ON DELETE SET NULL,
    is_primary BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_territory_assignment UNIQUE(territory_id, sales_rep, role)
);

-- Territory Rules
CREATE TABLE IF NOT EXISTS territory_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    territory_id UUID NOT NULL REFERENCES territories(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL,
    rule_name VARCHAR(200) NOT NULL,
    conditions JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task 70: Sales Analytics
CREATE TABLE IF NOT EXISTS sales_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    sales_rep VARCHAR(100),
    territory_id UUID,
    team_id UUID,
    new_leads_count INTEGER DEFAULT 0,
    qualified_leads_count INTEGER DEFAULT 0,
    opportunities_created INTEGER DEFAULT 0,
    opportunities_won INTEGER DEFAULT 0,
    opportunities_lost INTEGER DEFAULT 0,
    quotes_sent INTEGER DEFAULT 0,
    proposals_sent INTEGER DEFAULT 0,
    contracts_signed INTEGER DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    average_deal_size DECIMAL(15,2),
    win_rate DECIMAL(5,2),
    average_sales_cycle_days INTEGER,
    pipeline_value DECIMAL(15,2),
    quota_attainment DECIMAL(5,2),
    activity_metrics JSONB DEFAULT '{}',
    conversion_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales Activities
CREATE TABLE IF NOT EXISTS sales_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_type VARCHAR(50) NOT NULL,
    activity_date TIMESTAMP WITH TIME ZONE NOT NULL,
    sales_rep VARCHAR(100) NOT NULL,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    customer_id UUID,
    subject VARCHAR(500) NOT NULL,
    description TEXT,
    outcome VARCHAR(100),
    duration_minutes INTEGER,
    next_action TEXT,
    next_action_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales Goals
CREATE TABLE IF NOT EXISTS sales_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_name VARCHAR(200) NOT NULL,
    goal_type VARCHAR(50) NOT NULL,
    sales_rep VARCHAR(100),
    territory_id UUID,
    team_id UUID,
    period_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    target_value DECIMAL(15,2) NOT NULL,
    actual_value DECIMAL(15,2) DEFAULT 0,
    attainment_percentage DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_leads_status ON leads(lead_status);
CREATE INDEX idx_leads_assigned ON leads(assigned_to);
CREATE INDEX idx_leads_source ON leads(lead_source);
CREATE INDEX idx_leads_score ON leads(lead_score);
CREATE INDEX idx_lead_activities_lead ON lead_activities(lead_id);
CREATE INDEX idx_opportunities_stage ON opportunities(stage);
CREATE INDEX idx_opportunities_assigned ON opportunities(assigned_to);
CREATE INDEX idx_opportunities_close_date ON opportunities(close_date);
CREATE INDEX idx_opportunity_products_opportunity ON opportunity_products(opportunity_id);
CREATE INDEX idx_pipeline_history_opportunity ON pipeline_stage_history(opportunity_id);
CREATE INDEX idx_quotes_status ON quotes(status);
CREATE INDEX idx_quotes_opportunity ON quotes(opportunity_id);
CREATE INDEX idx_quote_items_quote ON quote_line_items(quote_id);
CREATE INDEX idx_proposals_status ON proposals(status);
CREATE INDEX idx_proposals_opportunity ON proposals(opportunity_id);
CREATE INDEX idx_contracts_status ON contracts(status);
CREATE INDEX idx_contracts_customer ON contracts(customer_id);
CREATE INDEX idx_contract_milestones_contract ON contract_milestones(contract_id);
CREATE INDEX idx_commissions_sales_rep ON commissions(sales_rep);
CREATE INDEX idx_commissions_period ON commissions(period_start, period_end);
CREATE INDEX idx_sales_forecasts_period ON sales_forecasts(start_date, end_date);
CREATE INDEX idx_territories_active ON territories(is_active);
CREATE INDEX idx_territory_assignments_sales_rep ON territory_assignments(sales_rep);
CREATE INDEX idx_sales_metrics_date ON sales_metrics(metric_date);
CREATE INDEX idx_sales_metrics_rep ON sales_metrics(sales_rep);
CREATE INDEX idx_sales_activities_date ON sales_activities(activity_date);
CREATE INDEX idx_sales_activities_rep ON sales_activities(sales_rep);
CREATE INDEX idx_sales_goals_period ON sales_goals(start_date, end_date);

-- Add comments
COMMENT ON TABLE leads IS 'Lead management and tracking';
COMMENT ON TABLE opportunities IS 'Sales opportunity tracking';
COMMENT ON TABLE sales_pipelines IS 'Configurable sales pipelines';
COMMENT ON TABLE quotes IS 'Quote management system';
COMMENT ON TABLE proposals IS 'Proposal generation and tracking';
COMMENT ON TABLE contracts IS 'Contract lifecycle management';
COMMENT ON TABLE commissions IS 'Sales commission tracking';
COMMENT ON TABLE sales_forecasts IS 'Sales forecasting and planning';
COMMENT ON TABLE territories IS 'Territory definition and management';
COMMENT ON TABLE sales_metrics IS 'Sales performance analytics';