-- Analytics & Business Intelligence Database Schema
-- Tasks 91-100: Complete Analytics System

-- Task 91: Business Intelligence
CREATE TABLE IF NOT EXISTS bi_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dashboard_type VARCHAR(100) DEFAULT 'standard',
    layout JSONB DEFAULT '{}'::jsonb,
    widgets JSONB DEFAULT '[]'::jsonb,
    filters JSONB DEFAULT '[]'::jsonb,
    refresh_interval INTEGER DEFAULT 300,
    is_public BOOLEAN DEFAULT false,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bi_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(100),
    query TEXT,
    parameters JSONB DEFAULT '{}'::jsonb,
    schedule VARCHAR(100),
    recipients JSONB DEFAULT '[]'::jsonb,
    format VARCHAR(20) DEFAULT 'pdf',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 92: Data Warehouse
CREATE TABLE IF NOT EXISTS data_warehouse_etl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    target_table VARCHAR(255) NOT NULL,
    transformation_rules JSONB DEFAULT '[]'::jsonb,
    schedule VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_warehouse_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fact_date DATE NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    value DECIMAL(15,2),
    dimensions JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_warehouse_dimensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension_type VARCHAR(100) NOT NULL,
    dimension_value VARCHAR(500) NOT NULL,
    attributes JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 93: Reporting Engine
CREATE TABLE IF NOT EXISTS report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    template_type VARCHAR(50) DEFAULT 'standard',
    content_template TEXT,
    data_queries JSONB DEFAULT '[]'::jsonb,
    parameters JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generated_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES report_templates(id),
    name VARCHAR(500) NOT NULL,
    parameters JSONB DEFAULT '{}'::jsonb,
    data JSONB,
    file_path VARCHAR(1000),
    status VARCHAR(50) DEFAULT 'pending',
    generated_at TIMESTAMP DEFAULT NOW()
);

-- Task 94: Predictive Analytics
CREATE TABLE IF NOT EXISTS ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    algorithm VARCHAR(100),
    features JSONB DEFAULT '[]'::jsonb,
    hyperparameters JSONB DEFAULT '{}'::jsonb,
    accuracy DECIMAL(5,4),
    version VARCHAR(20),
    file_path VARCHAR(1000),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id),
    entity_type VARCHAR(100),
    entity_id UUID,
    prediction_type VARCHAR(100),
    predicted_value JSONB,
    confidence DECIMAL(5,4),
    features_used JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 95: Real-time Analytics
CREATE TABLE IF NOT EXISTS real_time_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,2),
    metric_type VARCHAR(100),
    dimensions JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS streaming_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100),
    connection_string TEXT,
    is_active BOOLEAN DEFAULT true,
    processing_rules JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 96: Data Visualization
CREATE TABLE IF NOT EXISTS visualizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    chart_type VARCHAR(50) NOT NULL,
    data_source VARCHAR(500),
    config JSONB DEFAULT '{}'::jsonb,
    style JSONB DEFAULT '{}'::jsonb,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS visualization_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visualization_id UUID REFERENCES visualizations(id),
    snapshot_data JSONB,
    image_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 97: Performance Metrics
CREATE TABLE IF NOT EXISTS kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kpi_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100),
    calculation_formula TEXT,
    target_value DECIMAL(15,2),
    unit VARCHAR(50),
    frequency VARCHAR(50) DEFAULT 'daily',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS kpi_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kpi_id UUID REFERENCES kpis(id),
    value DECIMAL(15,2),
    period_start DATE,
    period_end DATE,
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- Task 98: Data Governance
CREATE TABLE IF NOT EXISTS data_catalogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(255) NOT NULL,
    schema_name VARCHAR(255),
    description TEXT,
    data_owner VARCHAR(255),
    sensitivity_level VARCHAR(50) DEFAULT 'internal',
    retention_policy VARCHAR(100),
    tags JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_quality_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255),
    rule_type VARCHAR(100),
    rule_definition JSONB,
    severity VARCHAR(20) DEFAULT 'warning',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_quality_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID REFERENCES data_quality_rules(id),
    issue_description TEXT,
    affected_records INTEGER,
    severity VARCHAR(20),
    status VARCHAR(50) DEFAULT 'open',
    detected_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

-- Task 99: Executive Dashboards
CREATE TABLE IF NOT EXISTS executive_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(255) NOT NULL,
    metric_category VARCHAR(100),
    current_value DECIMAL(15,2),
    previous_value DECIMAL(15,2),
    target_value DECIMAL(15,2),
    trend VARCHAR(20),
    period VARCHAR(50),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS executive_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(100),
    severity VARCHAR(20),
    title VARCHAR(500),
    description TEXT,
    metric_id UUID,
    threshold_breached DECIMAL(15,2),
    is_acknowledged BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 100: Analytics API
CREATE TABLE IF NOT EXISTS api_endpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint_path VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    description TEXT,
    parameters JSONB DEFAULT '[]'::jsonb,
    response_schema JSONB,
    rate_limit INTEGER DEFAULT 100,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    endpoint_id UUID REFERENCES api_endpoints(id),
    api_key VARCHAR(255),
    request_count INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    status_code INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bi_dashboards_type ON bi_dashboards(dashboard_type);
CREATE INDEX IF NOT EXISTS idx_etl_jobs_status ON data_warehouse_etl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_facts_date ON data_warehouse_facts(fact_date);
CREATE INDEX IF NOT EXISTS idx_dimensions_type ON data_warehouse_dimensions(dimension_type);
CREATE INDEX IF NOT EXISTS idx_predictions_entity ON predictions(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_real_time_metrics_timestamp ON real_time_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_kpi_values_period ON kpi_values(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_quality_issues_status ON data_quality_issues(status);
CREATE INDEX IF NOT EXISTS idx_executive_metrics_category ON executive_metrics(metric_category);
CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp);

-- Comments for documentation
COMMENT ON TABLE bi_dashboards IS 'Task 91: Business Intelligence Dashboards';
COMMENT ON TABLE data_warehouse_etl_jobs IS 'Task 92: Data Warehouse ETL Jobs';
COMMENT ON TABLE report_templates IS 'Task 93: Reporting Engine Templates';
COMMENT ON TABLE ml_models IS 'Task 94: Machine Learning Models for Predictive Analytics';
COMMENT ON TABLE real_time_metrics IS 'Task 95: Real-time Analytics Metrics';
COMMENT ON TABLE visualizations IS 'Task 96: Data Visualization Configurations';
COMMENT ON TABLE kpis IS 'Task 97: Key Performance Indicators';
COMMENT ON TABLE data_catalogs IS 'Task 98: Data Governance Catalog';
COMMENT ON TABLE executive_metrics IS 'Task 99: Executive Dashboard Metrics';
COMMENT ON TABLE api_endpoints IS 'Task 100: Analytics API Endpoints';