-- Advanced Operations Database Schema
-- Tasks 101-110: Enterprise Operations Systems

-- Task 101: Vendor Management
CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_name VARCHAR(255) NOT NULL,
    vendor_type VARCHAR(100) DEFAULT 'supplier',
    tax_id VARCHAR(50),
    contact_info JSONB DEFAULT '{}'::jsonb,
    payment_terms VARCHAR(50) DEFAULT 'net30',
    rating DECIMAL(3,2),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendor_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID REFERENCES vendors(id),
    quality_score DECIMAL(5,2),
    delivery_score DECIMAL(5,2),
    price_score DECIMAL(5,2),
    service_score DECIMAL(5,2),
    overall_score DECIMAL(5,2),
    evaluation_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 102: Procurement System
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number VARCHAR(50) UNIQUE NOT NULL,
    vendor_id UUID REFERENCES vendors(id),
    items JSONB DEFAULT '[]'::jsonb,
    total_amount DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'draft',
    order_date DATE DEFAULT CURRENT_DATE,
    delivery_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS requisitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    req_number VARCHAR(50) UNIQUE NOT NULL,
    department VARCHAR(100),
    requested_by VARCHAR(255),
    items JSONB DEFAULT '[]'::jsonb,
    total_amount DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rfqs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    items JSONB DEFAULT '[]'::jsonb,
    deadline TIMESTAMP,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 103: Contract Lifecycle
CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    contract_type VARCHAR(100) DEFAULT 'service',
    vendor_id UUID REFERENCES vendors(id),
    parties JSONB DEFAULT '[]'::jsonb,
    terms JSONB DEFAULT '{}'::jsonb,
    start_date DATE,
    end_date DATE,
    total_value DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS contract_renewals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_contract_id UUID REFERENCES contracts(id),
    new_start_date DATE,
    new_end_date DATE,
    renewal_terms JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 104: Risk Management
CREATE TABLE IF NOT EXISTS risks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'operational',
    likelihood INTEGER CHECK (likelihood BETWEEN 1 AND 5),
    impact_score INTEGER CHECK (impact_score BETWEEN 1 AND 5),
    risk_score INTEGER,
    severity VARCHAR(20),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_mitigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id UUID REFERENCES risks(id),
    strategy VARCHAR(100),
    actions JSONB DEFAULT '[]'::jsonb,
    responsible_party VARCHAR(255),
    timeline VARCHAR(100),
    cost_estimate DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 105: Compliance Tracking
CREATE TABLE IF NOT EXISTS compliance_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    regulation VARCHAR(100) NOT NULL,
    requirement_name VARCHAR(500) NOT NULL,
    description TEXT,
    compliance_status VARCHAR(50) DEFAULT 'pending',
    due_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compliance_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_type VARCHAR(100),
    scope JSONB DEFAULT '[]'::jsonb,
    scheduled_date DATE,
    auditor VARCHAR(255),
    status VARCHAR(50) DEFAULT 'scheduled',
    findings JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID REFERENCES compliance_audits(id),
    finding_type VARCHAR(100),
    severity VARCHAR(20) DEFAULT 'medium',
    description TEXT,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compliance_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    violation_type VARCHAR(100),
    severity VARCHAR(20),
    description TEXT,
    reported_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 106: Legal Management
CREATE TABLE IF NOT EXISTS legal_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    case_type VARCHAR(100) DEFAULT 'general',
    description TEXT,
    parties JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(50) DEFAULT 'open',
    filing_date DATE,
    next_hearing_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS legal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES legal_cases(id),
    document_type VARCHAR(100),
    title VARCHAR(500),
    file_path VARCHAR(1000),
    confidentiality VARCHAR(50) DEFAULT 'internal',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS intellectual_property (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    registration_number VARCHAR(100),
    filing_date DATE,
    expiry_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 107: Insurance Management
CREATE TABLE IF NOT EXISTS insurance_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_number VARCHAR(50) UNIQUE NOT NULL,
    policy_type VARCHAR(100),
    insurer VARCHAR(255),
    coverage_amount DECIMAL(15,2),
    premium DECIMAL(15,2),
    deductible DECIMAL(15,2),
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS insurance_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_number VARCHAR(50) UNIQUE NOT NULL,
    policy_id UUID REFERENCES insurance_policies(id),
    claim_type VARCHAR(100),
    incident_date DATE,
    claim_amount DECIMAL(15,2),
    approved_amount DECIMAL(15,2),
    description TEXT,
    status VARCHAR(50) DEFAULT 'submitted',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 108: Sustainability Tracking
CREATE TABLE IF NOT EXISTS sustainability_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_category VARCHAR(100) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    value DECIMAL(15,2),
    unit VARCHAR(50),
    measurement_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS carbon_emissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    emission_source VARCHAR(100) NOT NULL,
    co2_equivalent DECIMAL(15,2),
    emission_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sustainability_initiatives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    category VARCHAR(100) DEFAULT 'environmental',
    description TEXT,
    goals JSONB DEFAULT '[]'::jsonb,
    start_date DATE,
    target_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 109: R&D Management
CREATE TABLE IF NOT EXISTS rd_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(500) NOT NULL,
    research_area VARCHAR(100),
    objectives JSONB DEFAULT '[]'::jsonb,
    budget DECIMAL(15,2),
    team_members JSONB DEFAULT '[]'::jsonb,
    stage VARCHAR(50) DEFAULT 'research',
    status VARCHAR(50) DEFAULT 'active',
    start_date DATE DEFAULT CURRENT_DATE,
    estimated_completion DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rd_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES rd_projects(id),
    experiment_name VARCHAR(500) NOT NULL,
    hypothesis TEXT,
    methodology JSONB DEFAULT '{}'::jsonb,
    results JSONB DEFAULT '{}'::jsonb,
    conclusion TEXT,
    date_conducted DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 110: Strategic Planning
CREATE TABLE IF NOT EXISTS strategic_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_name VARCHAR(500) NOT NULL,
    vision TEXT,
    mission TEXT,
    timeframe VARCHAR(50) DEFAULT 'annual',
    objectives JSONB DEFAULT '[]'::jsonb,
    strategies JSONB DEFAULT '[]'::jsonb,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS okrs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objective TEXT NOT NULL,
    key_results JSONB DEFAULT '[]'::jsonb,
    owner VARCHAR(255),
    department VARCHAR(100),
    quarter VARCHAR(10),
    progress DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS swot_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_name VARCHAR(500),
    strengths JSONB DEFAULT '[]'::jsonb,
    weaknesses JSONB DEFAULT '[]'::jsonb,
    opportunities JSONB DEFAULT '[]'::jsonb,
    threats JSONB DEFAULT '[]'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scorecard_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    perspective VARCHAR(50) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    current_value DECIMAL(15,2),
    target_value DECIMAL(15,2),
    unit VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_vendors_status ON vendors(status);
CREATE INDEX IF NOT EXISTS idx_po_vendor ON purchase_orders(vendor_id);
CREATE INDEX IF NOT EXISTS idx_contracts_vendor ON contracts(vendor_id);
CREATE INDEX IF NOT EXISTS idx_risks_severity ON risks(severity);
CREATE INDEX IF NOT EXISTS idx_compliance_status ON compliance_requirements(compliance_status);
CREATE INDEX IF NOT EXISTS idx_legal_cases_status ON legal_cases(status);
CREATE INDEX IF NOT EXISTS idx_insurance_policies_type ON insurance_policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_sustainability_category ON sustainability_metrics(metric_category);
CREATE INDEX IF NOT EXISTS idx_rd_projects_stage ON rd_projects(stage);
CREATE INDEX IF NOT EXISTS idx_okrs_quarter ON okrs(quarter);

-- Comments for documentation
COMMENT ON TABLE vendors IS 'Task 101: Vendor Management System';
COMMENT ON TABLE purchase_orders IS 'Task 102: Procurement System';
COMMENT ON TABLE contracts IS 'Task 103: Contract Lifecycle Management';
COMMENT ON TABLE risks IS 'Task 104: Risk Management';
COMMENT ON TABLE compliance_requirements IS 'Task 105: Compliance Tracking';
COMMENT ON TABLE legal_cases IS 'Task 106: Legal Management';
COMMENT ON TABLE insurance_policies IS 'Task 107: Insurance Management';
COMMENT ON TABLE sustainability_metrics IS 'Task 108: Sustainability Tracking';
COMMENT ON TABLE rd_projects IS 'Task 109: R&D Management';
COMMENT ON TABLE strategic_plans IS 'Task 110: Strategic Planning';