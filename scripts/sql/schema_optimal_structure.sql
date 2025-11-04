-- BrainOps Optimal Database Schema
-- Generated: 2025-07-23T12:00:57.595315
-- This represents the ideal schema structure


-- Table: activities
CREATE TABLE activities (
    id UUID NOT NULL,
    entity_type VARCHAR(20) NOT NULL,
    entity_id UUID NOT NULL,
    type ACTIVITYTYPE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    metadata JSON,
    user_id UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for activities
CREATE INDEX idx_activity_entity ON public.activities USING btree (entity_type, entity_id);
CREATE INDEX idx_activity_user ON public.activities USING btree (user_id);
CREATE INDEX idx_activity_created ON public.activities USING btree (created_at);
CREATE INDEX idx_activity_type ON public.activities USING btree (type);

-- Table: admin_action_logs
CREATE TABLE admin_action_logs (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    action_type VARCHAR(50) NOT NULL,
    action_status VARCHAR(50) NOT NULL DEFAULT 'pending'::character varying,
    user_id UUID NOT NULL,
    user_email VARCHAR(255),
    user_ip VARCHAR(45),
    user_agent TEXT,
    api_key_id VARCHAR(255) NOT NULL,
    action_target VARCHAR(255),
    action_details JSONB DEFAULT '{}'::jsonb,
    sql_executed TEXT,
    result_summary TEXT,
    result_details JSONB,
    error_message TEXT,
    error_traceback TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    render_deploy_id VARCHAR(255) NOT NULL,
    vercel_deploy_id VARCHAR(255) NOT NULL,
    github_issue_number INTEGER,
    github_pr_number INTEGER,
    backup_location TEXT,
    environment VARCHAR(50) DEFAULT 'production'::character varying,
    service_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for admin_action_logs
CREATE INDEX idx_admin_logs_action_type ON public.admin_action_logs USING btree (action_type);
CREATE INDEX idx_admin_logs_status ON public.admin_action_logs USING btree (action_status);
CREATE INDEX idx_admin_logs_user_id ON public.admin_action_logs USING btree (user_id);
CREATE INDEX idx_admin_logs_started_at ON public.admin_action_logs USING btree (started_at);
CREATE INDEX idx_admin_logs_environment ON public.admin_action_logs USING btree (environment);

-- Table: agent_executions
CREATE TABLE agent_executions (
    id UUID NOT NULL,
    task_execution_id UUID NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT,
    model_name VARCHAR(100),
    tokens_input INTEGER,
    tokens_output INTEGER,
    latency_ms INTEGER,
    cost_cents INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY (task_execution_id) REFERENCES task_executions(id)
);

-- Indexes for agent_executions

-- Table: agent_memory_access
CREATE TABLE agent_memory_access (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100) NOT NULL,
    memory_id UUID NOT NULL,
    access_type VARCHAR(50) NOT NULL,
    access_context JSONB,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for agent_memory_access
CREATE INDEX idx_agent_access_agent ON public.agent_memory_access USING btree (agent_id);
CREATE INDEX idx_agent_access_memory ON public.agent_memory_access USING btree (memory_id);
CREATE INDEX idx_agent_access_time ON public.agent_memory_access USING btree (created_at);

-- Table: agent_registry
CREATE TABLE agent_registry (
    agent_id UUID NOT NULL DEFAULT gen_random_uuid(),
    agent_type VARCHAR(100) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    configuration JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'active'::character varying,
    capabilities JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_id)
);

-- Indexes for agent_registry

-- Table: ai_agents
CREATE TABLE ai_agents (
    agent_id VARCHAR(50) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    capabilities JSONB DEFAULT '[]'::jsonb,
    last_sync TIMESTAMP WITHOUT TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (agent_id)
);

-- Indexes for ai_agents
CREATE INDEX idx_ai_agents_active ON public.ai_agents USING btree (is_active);

-- Table: ai_logs
CREATE TABLE ai_logs (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    prompt TEXT,
    response TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for ai_logs

-- Table: ai_usage_logs
CREATE TABLE ai_usage_logs (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    service VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    tokens_used INTEGER,
    input_cost DOUBLE PRECISION,
    output_cost DOUBLE PRECISION,
    total_cost DOUBLE PRECISION,
    request_id VARCHAR(255) NOT NULL,
    response_time_ms INTEGER,
    status_code INTEGER,
    error TEXT,
    meta_data JSON,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for ai_usage_logs
CREATE INDEX idx_ai_usage_user_created ON public.ai_usage_logs USING btree (user_id, created_at);
CREATE INDEX idx_ai_usage_service_model ON public.ai_usage_logs USING btree (service, model);

-- Table: alembic_version
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
);

-- Indexes for alembic_version
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);

-- Table: api_keys
CREATE TABLE api_keys (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    prefix VARCHAR(20) NOT NULL,
    scopes JSON,
    last_used_at TIMESTAMP WITHOUT TIME ZONE,
    usage_count INTEGER,
    is_active BOOLEAN,
    expires_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (key_hash),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for api_keys
CREATE UNIQUE INDEX api_keys_key_hash_key ON public.api_keys USING btree (key_hash);

-- Table: app_users
CREATE TABLE app_users (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    phone VARCHAR(50),
    avatar_url VARCHAR(500),
    bio TEXT,
    company VARCHAR(200),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_superuser BOOLEAN DEFAULT false,
    is_seller BOOLEAN DEFAULT false,
    role USERROLE DEFAULT 'user'::userrole,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    two_factor_secret_temp VARCHAR(255),
    two_factor_backup_codes JSON DEFAULT '[]'::json,
    last_login TIMESTAMP WITHOUT TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITHOUT TIME ZONE,
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(100),
    UNIQUE (email),
    PRIMARY KEY (id),
    UNIQUE (username)
);

-- Indexes for app_users
CREATE UNIQUE INDEX app_users_email_key ON public.app_users USING btree (email);
CREATE INDEX idx_app_users_email ON public.app_users USING btree (email);
CREATE UNIQUE INDEX app_users_username_key ON public.app_users USING btree (username);
CREATE INDEX idx_app_users_username ON public.app_users USING btree (username);

-- Table: auth_tokens
CREATE TABLE auth_tokens (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    token VARCHAR(500) NOT NULL,
    token_type VARCHAR(50) NOT NULL DEFAULT 'access'::character varying,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE (token),
    FOREIGN KEY (user_id) REFERENCES app_users(id) ON DELETE CASCADE
);

-- Indexes for auth_tokens
CREATE INDEX idx_auth_tokens_user ON public.auth_tokens USING btree (user_id);
CREATE INDEX idx_auth_tokens_expires ON public.auth_tokens USING btree (expires_at);
CREATE UNIQUE INDEX auth_tokens_token_key ON public.auth_tokens USING btree (token);

-- Table: automation_actions
CREATE TABLE automation_actions (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    action_config JSONB DEFAULT '{}'::jsonb,
    execution_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (rule_id) REFERENCES automation_rules(id) ON DELETE CASCADE
);

-- Indexes for automation_actions
CREATE INDEX idx_actions_rule ON public.automation_actions USING btree (rule_id);

-- Table: automation_executions
CREATE TABLE automation_executions (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL,
    trigger_data JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    execution_log JSONB DEFAULT '[]'::jsonb,
    PRIMARY KEY (id),
    FOREIGN KEY (workflow_id) REFERENCES automation_workflows(id)
);

-- Indexes for automation_executions
CREATE INDEX idx_executions_workflow ON public.automation_executions USING btree (workflow_id);
CREATE INDEX idx_executions_status ON public.automation_executions USING btree (status);

-- Table: automation_rules
CREATE TABLE automation_rules (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL,
    rule_order INTEGER NOT NULL,
    condition_type VARCHAR(100) NOT NULL,
    condition_config JSONB DEFAULT '{}'::jsonb,
    action_type VARCHAR(100) NOT NULL,
    action_config JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (workflow_id) REFERENCES automation_workflows(id) ON DELETE CASCADE
);

-- Indexes for automation_rules
CREATE INDEX idx_rules_workflow ON public.automation_rules USING btree (workflow_id);

-- Table: automation_templates
CREATE TABLE automation_templates (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    template_config JSONB NOT NULL,
    is_public BOOLEAN DEFAULT false,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES app_users(id),
    PRIMARY KEY (id)
);

-- Indexes for automation_templates
CREATE INDEX idx_templates_category ON public.automation_templates USING btree (category);

-- Table: automation_workflows
CREATE TABLE automation_workflows (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(100) NOT NULL,
    trigger_config JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES app_users(id),
    PRIMARY KEY (id)
);

-- Indexes for automation_workflows
CREATE INDEX idx_workflows_active ON public.automation_workflows USING btree (is_active);

-- Table: blog_posts
CREATE TABLE blog_posts (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE (slug)
);

-- Indexes for blog_posts
CREATE UNIQUE INDEX blog_posts_slug_key ON public.blog_posts USING btree (slug);

-- Table: businesses
CREATE TABLE businesses (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    tax_id VARCHAR(50) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA'::character varying,
    logo_url VARCHAR(500),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for businesses
CREATE INDEX idx_businesses_name ON public.businesses USING btree (name);
CREATE INDEX idx_businesses_active ON public.businesses USING btree (is_active);

-- Table: campaigns
CREATE TABLE campaigns (
    id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    budget_cents INTEGER,
    actual_cost_cents INTEGER,
    target_audience JSON,
    goals JSON,
    leads_generated INTEGER,
    opportunities_created INTEGER,
    revenue_attributed_cents INTEGER,
    content_urls JSON,
    email_templates JSON,
    status VARCHAR(20),
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    PRIMARY KEY (id)
);

-- Indexes for campaigns
CREATE INDEX idx_campaign_dates ON public.campaigns USING btree (start_date, end_date);
CREATE INDEX idx_campaign_status ON public.campaigns USING btree (status);
CREATE INDEX idx_campaign_type ON public.campaigns USING btree (type);

-- Table: communications
CREATE TABLE communications (
    id UUID NOT NULL,
    entity_type VARCHAR(20) NOT NULL,
    entity_id UUID NOT NULL,
    type COMMUNICATIONTYPE NOT NULL,
    direction VARCHAR(10),
    subject VARCHAR(200),
    content TEXT,
    duration_minutes INTEGER,
    is_completed BOOLEAN,
    scheduled_at TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    attachments JSON,
    user_id UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for communications
CREATE INDEX idx_communication_user ON public.communications USING btree (user_id);
CREATE INDEX idx_communication_scheduled ON public.communications USING btree (scheduled_at);
CREATE INDEX idx_communication_entity ON public.communications USING btree (entity_type, entity_id);
CREATE INDEX idx_communication_type ON public.communications USING btree (type);

-- Table: contacts
CREATE TABLE contacts (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for contacts

-- Table: cross_ai_memory
CREATE TABLE cross_ai_memory (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    source_agent VARCHAR(100) NOT NULL,
    target_agents ARRAY,
    memory_key VARCHAR(255) NOT NULL,
    memory_value JSONB NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    embedding VECTOR,
    importance_score DOUBLE PRECISION DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for cross_ai_memory
CREATE INDEX idx_cross_ai_source ON public.cross_ai_memory USING btree (source_agent);
CREATE INDEX idx_cross_ai_key ON public.cross_ai_memory USING btree (memory_key);
CREATE INDEX idx_cross_ai_type ON public.cross_ai_memory USING btree (memory_type);
CREATE INDEX idx_cross_ai_embedding ON public.cross_ai_memory USING ivfflat (embedding vector_cosine_ops);

-- Table: customer_segments
CREATE TABLE customer_segments (
    id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    criteria JSON NOT NULL,
    member_count INTEGER,
    last_calculated TIMESTAMP WITHOUT TIME ZONE,
    is_active BOOLEAN,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    PRIMARY KEY (id)
);

-- Indexes for customer_segments

-- Table: customers
CREATE TABLE customers (
    id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    company_name VARCHAR(200),
    billing_address TEXT,
    billing_city VARCHAR(100),
    billing_state VARCHAR(50),
    billing_zip VARCHAR(20),
    billing_country VARCHAR(2),
    service_address TEXT,
    service_city VARCHAR(100),
    service_state VARCHAR(50),
    service_zip VARCHAR(20),
    credit_limit INTEGER,
    payment_terms VARCHAR(50),
    tax_exempt BOOLEAN,
    tax_exempt_number VARCHAR(100),
    source VARCHAR(50),
    tags JSON,
    notes TEXT,
    is_active BOOLEAN,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for customers
CREATE INDEX idx_customer_active ON public.customers USING btree (is_active);
CREATE INDEX idx_customer_email ON public.customers USING btree (email);

-- Table: dashboard_insights
CREATE TABLE dashboard_insights (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    insight TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for dashboard_insights

-- Table: database_health_checks
CREATE TABLE database_health_checks (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    check_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_healthy BOOLEAN NOT NULL,
    health_score INTEGER NOT NULL,
    tables_checked INTEGER NOT NULL,
    tables_missing INTEGER NOT NULL,
    indexes_checked INTEGER NOT NULL,
    indexes_missing INTEGER NOT NULL,
    functions_checked INTEGER NOT NULL,
    functions_missing INTEGER NOT NULL,
    missing_objects JSONB,
    schema_drift JSONB,
    performance_issues JSONB,
    repair_needed BOOLEAN DEFAULT false,
    repair_recommendations JSONB,
    check_duration_ms INTEGER NOT NULL,
    environment VARCHAR(50) DEFAULT 'production'::character varying,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for database_health_checks
CREATE INDEX idx_health_checks_timestamp ON public.database_health_checks USING btree (check_timestamp);
CREATE INDEX idx_health_checks_healthy ON public.database_health_checks USING btree (is_healthy);

-- Table: deployment_records
CREATE TABLE deployment_records (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    service_type VARCHAR(50) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    service_id VARCHAR(255) NOT NULL,
    deployment_id VARCHAR(255) NOT NULL,
    deployment_url TEXT,
    deployment_status VARCHAR(50) NOT NULL,
    git_branch VARCHAR(255),
    git_commit VARCHAR(40),
    git_message TEXT,
    docker_image VARCHAR(500),
    is_rollbackable BOOLEAN DEFAULT true,
    previous_deployment_id UUID NOT NULL,
    rolled_back_at TIMESTAMP WITH TIME ZONE,
    rolled_back_by UUID,
    deployed_by UUID,
    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    environment VARCHAR(50) DEFAULT 'production'::character varying,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for deployment_records
CREATE INDEX idx_deployments_service ON public.deployment_records USING btree (service_type, service_name);
CREATE INDEX idx_deployments_status ON public.deployment_records USING btree (deployment_status);
CREATE INDEX idx_deployments_deployed_at ON public.deployment_records USING btree (deployed_at);

-- Table: digital_deliveries
CREATE TABLE digital_deliveries (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL,
    download_url TEXT NOT NULL,
    accessed BOOLEAN DEFAULT false,
    accessed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

-- Indexes for digital_deliveries

-- Table: document_chunks
CREATE TABLE document_chunks (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    document_title TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    document_metadata JSONB DEFAULT '{}'::jsonb,
    embedding VECTOR,
    tokens INTEGER,
    overlap_prev INTEGER DEFAULT 0,
    overlap_next INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for document_chunks
CREATE INDEX idx_chunks_document ON public.document_chunks USING btree (document_id);
CREATE INDEX idx_chunks_embedding ON public.document_chunks USING ivfflat (embedding vector_cosine_ops);

-- Table: document_templates
CREATE TABLE document_templates (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    template_content TEXT NOT NULL,
    template TEXT NOT NULL,
    variables JSON,
    example_context JSON,
    example_output TEXT,
    is_public BOOLEAN,
    category VARCHAR(100),
    tags JSON,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for document_templates

-- Table: documents
CREATE TABLE documents (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for documents

-- Table: embedding_models
CREATE TABLE embedding_models (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    dimension INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name),
    PRIMARY KEY (id)
);

-- Indexes for embedding_models
CREATE UNIQUE INDEX embedding_models_name_key ON public.embedding_models USING btree (name);

-- Table: embeddings
CREATE TABLE embeddings (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES embedding_models(id),
    PRIMARY KEY (id)
);

-- Indexes for embeddings
CREATE INDEX idx_embeddings_source ON public.embeddings USING btree (source_type, source_id);
CREATE INDEX idx_embeddings_vector ON public.embeddings USING ivfflat (embedding vector_cosine_ops);

-- Table: estimate_records
CREATE TABLE estimate_records (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    project_name TEXT NOT NULL,
    building_type VARCHAR(100) NOT NULL,
    roof_area_sf DOUBLE PRECISION NOT NULL,
    roof_type VARCHAR(50) NOT NULL,
    system_type VARCHAR(50) NOT NULL,
    material_cost DOUBLE PRECISION NOT NULL,
    labor_cost DOUBLE PRECISION NOT NULL,
    total_cost DOUBLE PRECISION NOT NULL,
    cost_per_sf DOUBLE PRECISION NOT NULL,
    margin_percentage DOUBLE PRECISION NOT NULL,
    scope_items ARRAY DEFAULT '{}'::text[],
    special_conditions ARRAY DEFAULT '{}'::text[],
    warranty_years INTEGER NOT NULL,
    location TEXT NOT NULL,
    estimate_date TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft'::character varying,
    won_project BOOLEAN,
    actual_cost DOUBLE PRECISION,
    embedding VECTOR,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for estimate_records
CREATE INDEX idx_estimates_project ON public.estimate_records USING btree (project_name);
CREATE INDEX idx_estimates_status ON public.estimate_records USING btree (status);
CREATE INDEX idx_estimates_embedding ON public.estimate_records USING ivfflat (embedding vector_cosine_ops);

-- Table: estimates
CREATE TABLE estimates (
    id UUID NOT NULL,
    inspection_id UUID NOT NULL,
    project_id UUID NOT NULL,
    estimate_number VARCHAR(50) NOT NULL,
    client_name VARCHAR(200) NOT NULL,
    client_email VARCHAR(255),
    client_phone VARCHAR(50),
    subtotal DOUBLE PRECISION NOT NULL,
    tax_rate DOUBLE PRECISION,
    tax_amount DOUBLE PRECISION,
    discount_amount DOUBLE PRECISION,
    total DOUBLE PRECISION NOT NULL,
    line_items JSON NOT NULL,
    status VARCHAR(20),
    valid_until DATE NOT NULL,
    created_by_id UUID NOT NULL,
    sent_at TIMESTAMP WITHOUT TIME ZONE,
    approved_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    customer_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    estimate_date DATE NOT NULL,
    subtotal_cents INTEGER NOT NULL,
    tax_cents INTEGER,
    discount_cents INTEGER,
    total_cents INTEGER NOT NULL,
    terms_conditions TEXT,
    sent_date TIMESTAMP WITHOUT TIME ZONE,
    viewed_date TIMESTAMP WITHOUT TIME ZONE,
    accepted_date TIMESTAMP WITHOUT TIME ZONE,
    declined_date TIMESTAMP WITHOUT TIME ZONE,
    converted_to_invoice_id UUID NOT NULL,
    created_by UUID NOT NULL,
    FOREIGN KEY (converted_to_invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (created_by_id) REFERENCES users(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    UNIQUE (estimate_number),
    FOREIGN KEY (inspection_id) REFERENCES inspections(id),
    PRIMARY KEY (id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Indexes for estimates
CREATE UNIQUE INDEX estimates_estimate_number_key ON public.estimates USING btree (estimate_number);
CREATE UNIQUE INDEX ix_estimates_estimate_number ON public.estimates USING btree (estimate_number);
CREATE INDEX idx_estimate_status ON public.estimates USING btree (status);
CREATE INDEX idx_estimate_customer ON public.estimates USING btree (customer_id);

-- Table: expenses
CREATE TABLE expenses (
    id UUID NOT NULL,
    expense_number VARCHAR(50) NOT NULL,
    job_id UUID NOT NULL,
    vendor_id UUID NOT NULL,
    expense_date DATE NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    tax_cents INTEGER,
    total_cents INTEGER NOT NULL,
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    receipt_url TEXT,
    receipt_stored BOOLEAN,
    is_reimbursable BOOLEAN,
    reimbursed BOOLEAN,
    reimbursement_date DATE,
    employee_id UUID NOT NULL,
    is_billable BOOLEAN,
    markup_percentage DOUBLE PRECISION,
    billed BOOLEAN,
    invoice_id UUID NOT NULL,
    quickbooks_expense_id VARCHAR(100) NOT NULL,
    notes TEXT,
    tags JSON,
    requires_approval BOOLEAN,
    approved BOOLEAN,
    approved_by UUID,
    approved_date TIMESTAMP WITHOUT TIME ZONE,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (employee_id) REFERENCES users(id),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    PRIMARY KEY (id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

-- Indexes for expenses
CREATE INDEX idx_expense_date ON public.expenses USING btree (expense_date);
CREATE UNIQUE INDEX ix_expenses_expense_number ON public.expenses USING btree (expense_number);
CREATE INDEX idx_expense_category ON public.expenses USING btree (category);
CREATE INDEX idx_expense_job ON public.expenses USING btree (job_id);
CREATE INDEX idx_expense_billable ON public.expenses USING btree (is_billable, billed);

-- Table: inspection_photos
CREATE TABLE inspection_photos (
    id UUID NOT NULL,
    inspection_id UUID NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    thumbnail_path VARCHAR(1000),
    caption TEXT,
    location JSON,
    tags JSON,
    ai_analysis JSON,
    damage_detected BOOLEAN,
    taken_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    uploaded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    FOREIGN KEY (inspection_id) REFERENCES inspections(id),
    PRIMARY KEY (id)
);

-- Indexes for inspection_photos

-- Table: inspections
CREATE TABLE inspections (
    id UUID NOT NULL,
    project_id UUID NOT NULL,
    property_address TEXT NOT NULL,
    inspector_id UUID NOT NULL,
    status VARCHAR(50),
    roof_type VARCHAR(100) NOT NULL,
    roof_age INTEGER,
    measurements JSON,
    damage_assessment JSON,
    recommendations TEXT,
    scheduled_at TIMESTAMP WITHOUT TIME ZONE,
    started_at TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inspector_id) REFERENCES users(id),
    PRIMARY KEY (id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Indexes for inspections

-- Table: integration_configs
CREATE TABLE integration_configs (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    integration_id UUID NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    config_value TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (integration_id) REFERENCES integrations(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

-- Indexes for integration_configs
CREATE INDEX idx_integration_configs ON public.integration_configs USING btree (integration_id);

-- Table: integrations
CREATE TABLE integrations (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    config JSON NOT NULL,
    is_active BOOLEAN,
    meta_data JSON,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITHOUT TIME ZONE,
    webhook_url VARCHAR(500),
    webhook_secret VARCHAR(255),
    connected_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP WITHOUT TIME ZONE,
    last_sync_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for integrations

-- Table: inventory_items
CREATE TABLE inventory_items (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL,
    sku VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    unit_price NUMERIC,
    cost NUMERIC,
    quantity_on_hand INTEGER DEFAULT 0,
    reorder_point INTEGER,
    reorder_quantity INTEGER,
    supplier VARCHAR(255),
    supplier_sku VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    PRIMARY KEY (id),
    UNIQUE (sku)
);

-- Indexes for inventory_items
CREATE INDEX idx_inventory_sku ON public.inventory_items USING btree (sku);
CREATE INDEX idx_inventory_business ON public.inventory_items USING btree (business_id);
CREATE UNIQUE INDEX inventory_items_sku_key ON public.inventory_items USING btree (sku);

-- Table: invoices
CREATE TABLE invoices (
    id UUID NOT NULL,
    invoice_number VARCHAR(50) NOT NULL,
    customer_id UUID NOT NULL,
    estimate_id UUID NOT NULL,
    job_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    subtotal_cents INTEGER NOT NULL,
    tax_cents INTEGER,
    discount_cents INTEGER,
    total_cents INTEGER NOT NULL,
    amount_paid_cents INTEGER,
    balance_cents INTEGER NOT NULL,
    line_items JSON NOT NULL,
    tax_details JSON,
    terms_conditions TEXT,
    notes TEXT,
    status VARCHAR(20),
    sent_date TIMESTAMP WITHOUT TIME ZONE,
    viewed_date TIMESTAMP WITHOUT TIME ZONE,
    paid_date TIMESTAMP WITHOUT TIME ZONE,
    void_date TIMESTAMP WITHOUT TIME ZONE,
    void_reason TEXT,
    payment_method VARCHAR(50),
    payment_reference VARCHAR(100),
    stripe_invoice_id VARCHAR(100) NOT NULL,
    quickbooks_invoice_id VARCHAR(100) NOT NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (estimate_id) REFERENCES estimates(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id),
    PRIMARY KEY (id)
);

-- Indexes for invoices
CREATE INDEX idx_invoice_customer ON public.invoices USING btree (customer_id);
CREATE UNIQUE INDEX ix_invoices_invoice_number ON public.invoices USING btree (invoice_number);
CREATE INDEX idx_invoice_due_date ON public.invoices USING btree (due_date);
CREATE INDEX idx_invoice_date ON public.invoices USING btree (invoice_date);
CREATE INDEX idx_invoice_status ON public.invoices USING btree (status);

-- Table: jobs
CREATE TABLE jobs (
    id UUID NOT NULL,
    job_number VARCHAR(50) NOT NULL,
    customer_id UUID NOT NULL,
    estimate_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    job_address TEXT,
    job_city VARCHAR(100),
    job_state VARCHAR(50),
    job_zip VARCHAR(20),
    scheduled_start DATE,
    scheduled_end DATE,
    actual_start DATE,
    actual_end DATE,
    estimated_revenue INTEGER,
    actual_revenue INTEGER,
    estimated_costs INTEGER,
    actual_costs INTEGER,
    status VARCHAR(20),
    completion_percentage INTEGER,
    invoice_id UUID NOT NULL,
    is_billable BOOLEAN,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (estimate_id) REFERENCES estimates(id),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    PRIMARY KEY (id)
);

-- Indexes for jobs
CREATE INDEX idx_job_dates ON public.jobs USING btree (scheduled_start, scheduled_end);
CREATE INDEX idx_job_customer ON public.jobs USING btree (customer_id);
CREATE INDEX idx_job_status ON public.jobs USING btree (status);
CREATE UNIQUE INDEX ix_jobs_job_number ON public.jobs USING btree (job_number);

-- Table: knowledge_entries
CREATE TABLE knowledge_entries (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    category VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    body TEXT NOT NULL,
    structured_data JSONB,
    examples JSONB DEFAULT '[]'::jsonb,
    doc_references ARRAY DEFAULT '{}'::text[],
    validated BOOLEAN DEFAULT false,
    validation_date TIMESTAMP WITH TIME ZONE,
    quality_score DOUBLE PRECISION DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    version VARCHAR(20) DEFAULT '1.0.0'::character varying,
    previous_versions ARRAY DEFAULT '{}'::uuid[],
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for knowledge_entries
CREATE INDEX idx_knowledge_category ON public.knowledge_entries USING btree (category);
CREATE INDEX idx_knowledge_validated ON public.knowledge_entries USING btree (validated);

-- Table: lead_sources
CREATE TABLE lead_sources (
    id UUID NOT NULL,
    name VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    total_leads INTEGER,
    qualified_leads INTEGER,
    converted_leads INTEGER,
    total_revenue_cents INTEGER,
    cost_cents INTEGER,
    conversion_rate DOUBLE PRECISION,
    cost_per_lead DOUBLE PRECISION,
    roi DOUBLE PRECISION,
    is_active BOOLEAN,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name),
    PRIMARY KEY (id)
);

-- Indexes for lead_sources
CREATE UNIQUE INDEX lead_sources_name_key ON public.lead_sources USING btree (name);
CREATE INDEX idx_lead_source_category ON public.lead_sources USING btree (category);

-- Table: leads
CREATE TABLE leads (
    id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    company VARCHAR(200),
    title VARCHAR(100),
    source VARCHAR(50) NOT NULL,
    campaign_id UUID NOT NULL,
    score INTEGER,
    status LEADSTATUS,
    assigned_to UUID,
    description TEXT,
    tags JSON,
    custom_fields JSON,
    converted_to_opportunity_id UUID NOT NULL,
    converted_date TIMESTAMP WITHOUT TIME ZONE,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
    FOREIGN KEY (converted_to_opportunity_id) REFERENCES opportunities(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE (email),
    PRIMARY KEY (id)
);

-- Indexes for leads
CREATE UNIQUE INDEX leads_email_key ON public.leads USING btree (email);
CREATE INDEX idx_lead_assigned ON public.leads USING btree (assigned_to);
CREATE INDEX idx_lead_status ON public.leads USING btree (status);
CREATE INDEX idx_lead_score ON public.leads USING btree (score);
CREATE INDEX idx_lead_source ON public.leads USING btree (source);

-- Table: memories
CREATE TABLE memories (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    tags JSON,
    meta_data JSON,
    embedding JSON,
    is_active BOOLEAN,
    is_pinned BOOLEAN,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for memories

-- Table: memory_access_log
CREATE TABLE memory_access_log (
    access_id INTEGER NOT NULL DEFAULT nextval('memory_access_log_access_id_seq'::regclass),
    memory_id UUID NOT NULL,
    agent_id VARCHAR(50) NOT NULL,
    access_type VARCHAR(20) NOT NULL,
    access_timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    context JSONB,
    PRIMARY KEY (access_id)
);

-- Indexes for memory_access_log

-- Table: memory_collections
CREATE TABLE memory_collections (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_type VARCHAR(50) NOT NULL,
    owner_id VARCHAR(255) NOT NULL,
    collection_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for memory_collections
CREATE INDEX idx_collections_owner ON public.memory_collections USING btree (owner_type, owner_id);
CREATE INDEX idx_collections_type ON public.memory_collections USING btree (collection_type);

-- Table: memory_contexts
CREATE TABLE memory_contexts (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    context_name VARCHAR(255) NOT NULL,
    context_type VARCHAR(100) NOT NULL,
    parent_context_id UUID NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_context_id) REFERENCES memory_contexts(id),
    PRIMARY KEY (id)
);

-- Indexes for memory_contexts
CREATE INDEX idx_contexts_parent ON public.memory_contexts USING btree (parent_context_id);
CREATE INDEX idx_contexts_type ON public.memory_contexts USING btree (context_type);

-- Table: memory_entries
CREATE TABLE memory_entries (
    memory_type VARCHAR(50) NOT NULL,
    content TEXT DEFAULT '{}'::jsonb,
    meta_data JSON,
    embedding JSON,
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    source VARCHAR(200),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITHOUT TIME ZONE,
    version INTEGER DEFAULT 1,
    tags JSON,
    importance_score INTEGER,
    owner_type VARCHAR(50) NOT NULL DEFAULT 'global'::ownertype,
    owner_id VARCHAR(255) NOT NULL DEFAULT 'system'::character varying,
    key VARCHAR(255) NOT NULL DEFAULT 'default_key'::character varying,
    context_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    category VARCHAR(100),
    accessed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    is_active TEXT DEFAULT 'true'::character varying,
    value TEXT NOT NULL,
    id UUID,
    memory_id UUID NOT NULL DEFAULT gen_random_uuid(),
    UNIQUE (owner_type, owner_id, key),
    PRIMARY KEY (memory_id),
    UNIQUE (owner_type, owner_id, key)
);

-- Indexes for memory_entries
CREATE INDEX idx_session_id ON public.memory_entries USING btree (session_id);
CREATE INDEX idx_importance ON public.memory_entries USING btree (importance_score);
CREATE INDEX ix_memory_entries_user_id ON public.memory_entries USING btree (user_id);
CREATE INDEX ix_memory_entries_session_id ON public.memory_entries USING btree (session_id);
CREATE INDEX ix_memory_entries_memory_type ON public.memory_entries USING btree (memory_type);
CREATE INDEX idx_memory_type_user ON public.memory_entries USING btree (memory_type, user_id);
CREATE INDEX idx_memory_updated ON public.memory_entries USING btree (updated_at);
CREATE INDEX idx_memory_entries_key ON public.memory_entries USING btree (key);
CREATE INDEX idx_memory_owner ON public.memory_entries USING btree (owner_type, owner_id);
CREATE UNIQUE INDEX idx_memory_key ON public.memory_entries USING btree (owner_type, owner_id, key);
CREATE INDEX idx_memory_entries_owner ON public.memory_entries USING btree (owner_type, owner_id);
CREATE INDEX idx_memory_entries_type ON public.memory_entries USING btree (memory_type);
CREATE INDEX idx_memory_entries_category ON public.memory_entries USING btree (category);
CREATE INDEX idx_memory_entries_created ON public.memory_entries USING btree (created_at DESC);
CREATE INDEX idx_memory_entries_accessed ON public.memory_entries USING btree (accessed_at DESC);
CREATE UNIQUE INDEX memory_entries_unique_key ON public.memory_entries USING btree (owner_type, owner_id, key);
CREATE INDEX idx_memory_accessed ON public.memory_entries USING btree (accessed_at DESC);
CREATE UNIQUE INDEX memory_entries_owner_type_owner_id_key_key ON public.memory_entries USING btree (owner_type, owner_id, key);
CREATE INDEX idx_memory_entries_owner_type ON public.memory_entries USING btree (owner_type);
CREATE INDEX idx_memory_entries_owner_id ON public.memory_entries USING btree (owner_id);
CREATE INDEX idx_memory_entries_memory_type ON public.memory_entries USING btree (memory_type);
CREATE INDEX idx_memory_entries_is_active ON public.memory_entries USING btree (is_active);
CREATE INDEX idx_memory_entries_created_at ON public.memory_entries USING btree (created_at DESC);
CREATE INDEX idx_memory_entries_accessed_at ON public.memory_entries USING btree (accessed_at DESC);

-- Table: memory_metadata
CREATE TABLE memory_metadata (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    memory_id UUID NOT NULL,
    metadata_key VARCHAR(255) NOT NULL,
    metadata_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for memory_metadata
CREATE INDEX idx_memory_meta_memory ON public.memory_metadata USING btree (memory_id);
CREATE INDEX idx_memory_meta_key ON public.memory_metadata USING btree (metadata_key);

-- Table: memory_records
CREATE TABLE memory_records (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    content TEXT,
    embedding VECTOR,
    type VARCHAR(50) NOT NULL DEFAULT 'general'::character varying,
    category VARCHAR(50),
    title TEXT NOT NULL DEFAULT 'Untitled'::text,
    summary TEXT,
    context JSONB DEFAULT '{}'::jsonb,
    tags ARRAY DEFAULT '{}'::text[],
    related_records ARRAY DEFAULT '{}'::uuid[],
    parent_id UUID NOT NULL,
    importance_score DOUBLE PRECISION DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    PRIMARY KEY (id)
);

-- Indexes for memory_records
CREATE INDEX idx_memory_type ON public.memory_records USING btree (type);
CREATE INDEX idx_memory_category ON public.memory_records USING btree (category);
CREATE INDEX idx_memory_tags ON public.memory_records USING gin (tags);
CREATE INDEX idx_memory_created ON public.memory_records USING btree (created_at DESC);
CREATE INDEX idx_memory_embedding ON public.memory_records USING ivfflat (embedding vector_cosine_ops);

-- Table: memory_sync
CREATE TABLE memory_sync (
    sync_id UUID NOT NULL DEFAULT gen_random_uuid(),
    source VARCHAR(100) NOT NULL,
    target VARCHAR(100) NOT NULL,
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(50),
    memory_keys JSONB,
    conflict_resolution JSONB,
    error_details TEXT,
    initiated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (sync_id)
);

-- Indexes for memory_sync
CREATE INDEX idx_memory_sync_status ON public.memory_sync USING btree (status);
CREATE INDEX idx_memory_sync_initiated_at ON public.memory_sync USING btree (initiated_at);
CREATE INDEX idx_sync_status ON public.memory_sync USING btree (status);
CREATE INDEX idx_sync_time ON public.memory_sync USING btree (initiated_at);

-- Table: multimodal_content
CREATE TABLE multimodal_content (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    content_type VARCHAR(50) NOT NULL,
    content_data BYTEA,
    content_url TEXT,
    mime_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for multimodal_content

-- Table: notifications
CREATE TABLE notifications (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    data JSON,
    action_url VARCHAR(500),
    is_read BOOLEAN,
    read_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for notifications
CREATE INDEX idx_notification_user_unread ON public.notifications USING btree (user_id, is_read);

-- Table: opportunities
CREATE TABLE opportunities (
    id UUID NOT NULL,
    customer_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    value_cents INTEGER NOT NULL,
    probability INTEGER,
    stage OPPORTUNITYSTAGE,
    expected_close_date DATE NOT NULL,
    closed_date TIMESTAMP WITHOUT TIME ZONE,
    assigned_to UUID NOT NULL,
    is_won BOOLEAN,
    lost_reason VARCHAR(100),
    competitors JSON,
    tags JSON,
    custom_fields JSON,
    is_active BOOLEAN,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    PRIMARY KEY (id)
);

-- Indexes for opportunities
CREATE INDEX idx_opportunity_customer ON public.opportunities USING btree (customer_id);
CREATE INDEX idx_opportunity_stage ON public.opportunities USING btree (stage);
CREATE INDEX idx_opportunity_assigned ON public.opportunities USING btree (assigned_to);
CREATE INDEX idx_opportunity_close_date ON public.opportunities USING btree (expected_close_date);

-- Table: orders
CREATE TABLE orders (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    product_id UUID NOT NULL,
    stripe_session_id TEXT NOT NULL,
    amount NUMERIC,
    status TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- Indexes for orders

-- Table: payments
CREATE TABLE payments (
    id UUID NOT NULL,
    payment_number VARCHAR(50) NOT NULL,
    invoice_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    payment_date DATE NOT NULL,
    amount_cents INTEGER NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    card_last_four VARCHAR(4),
    card_brand VARCHAR(20),
    bank_name VARCHAR(100),
    account_last_four VARCHAR(4),
    status VARCHAR(20),
    cleared_date DATE,
    failed_reason TEXT,
    is_refunded BOOLEAN,
    refund_amount_cents INTEGER,
    refund_date DATE,
    refund_reason TEXT,
    stripe_payment_id VARCHAR(100) NOT NULL,
    quickbooks_payment_id VARCHAR(100) NOT NULL,
    notes TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    PRIMARY KEY (id)
);

-- Indexes for payments
CREATE INDEX idx_payment_customer ON public.payments USING btree (customer_id);
CREATE INDEX idx_payment_date ON public.payments USING btree (payment_date);
CREATE INDEX idx_payment_status ON public.payments USING btree (status);
CREATE INDEX idx_payment_invoice ON public.payments USING btree (invoice_id);
CREATE UNIQUE INDEX ix_payments_payment_number ON public.payments USING btree (payment_number);

-- Table: production_memory_embeddings
CREATE TABLE production_memory_embeddings (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    memory_entry_id UUID NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    embedding_vector VECTOR,
    embedding_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_entry_id) REFERENCES production_memory_entries(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

-- Indexes for production_memory_embeddings
CREATE INDEX idx_prod_embed_memory ON public.production_memory_embeddings USING btree (memory_entry_id);
CREATE INDEX idx_prod_embed_vector ON public.production_memory_embeddings USING ivfflat (embedding_vector vector_cosine_ops);

-- Table: production_memory_entries
CREATE TABLE production_memory_entries (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    memory_key VARCHAR(500) NOT NULL,
    memory_value JSONB NOT NULL,
    memory_type VARCHAR(100) NOT NULL,
    owner_type VARCHAR(50) NOT NULL,
    owner_id VARCHAR(255) NOT NULL,
    context_id UUID NOT NULL,
    tags ARRAY,
    ttl INTEGER,
    importance_score DOUBLE PRECISION DEFAULT 0.5,
    access_pattern VARCHAR(50) DEFAULT 'read_write'::character varying,
    encryption_key VARCHAR(500),
    is_compressed BOOLEAN DEFAULT false,
    compression_type VARCHAR(50) NOT NULL,
    version INTEGER DEFAULT 1,
    previous_version_id UUID NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (context_id) REFERENCES memory_contexts(id),
    PRIMARY KEY (id),
    UNIQUE (owner_type, owner_id, memory_key)
);

-- Indexes for production_memory_entries
CREATE INDEX idx_prod_memory_owner ON public.production_memory_entries USING btree (owner_type, owner_id);
CREATE INDEX idx_prod_memory_key ON public.production_memory_entries USING btree (memory_key);
CREATE INDEX idx_prod_memory_type ON public.production_memory_entries USING btree (memory_type);
CREATE INDEX idx_prod_memory_tags ON public.production_memory_entries USING gin (tags);
CREATE UNIQUE INDEX unique_production_memory_key ON public.production_memory_entries USING btree (owner_type, owner_id, memory_key);

-- Table: production_memory_metadata
CREATE TABLE production_memory_metadata (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    memory_entry_id UUID NOT NULL,
    metadata_key VARCHAR(255) NOT NULL,
    metadata_value JSONB NOT NULL,
    metadata_type VARCHAR(50) NOT NULL,
    is_indexed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_entry_id) REFERENCES production_memory_entries(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

-- Indexes for production_memory_metadata
CREATE INDEX idx_prod_meta_memory ON public.production_memory_metadata USING btree (memory_entry_id);
CREATE INDEX idx_prod_meta_key ON public.production_memory_metadata USING btree (metadata_key);

-- Table: production_memory_sync
CREATE TABLE production_memory_sync (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    memory_entry_id UUID NOT NULL,
    sync_type VARCHAR(50) NOT NULL,
    sync_status VARCHAR(50) NOT NULL,
    sync_target VARCHAR(255),
    sync_metadata JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (memory_entry_id) REFERENCES production_memory_entries(id) ON DELETE CASCADE,
    PRIMARY KEY (id)
);

-- Indexes for production_memory_sync
CREATE INDEX idx_prod_sync_memory ON public.production_memory_sync USING btree (memory_entry_id);
CREATE INDEX idx_prod_sync_status ON public.production_memory_sync USING btree (sync_status);

-- Table: products
CREATE TABLE products (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    image_url TEXT,
    digital_file_url TEXT,
    price_cents INTEGER,
    PRIMARY KEY (id)
);

-- Indexes for products

-- Table: project_members
CREATE TABLE project_members (
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(50),
    joined_at TIMESTAMP WITHOUT TIME ZONE,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Table: project_tasks
CREATE TABLE project_tasks (
    id UUID NOT NULL,
    project_id UUID NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    priority VARCHAR(20),
    assignee_id UUID NOT NULL,
    created_by UUID NOT NULL,
    due_date TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    estimated_hours DOUBLE PRECISION,
    actual_hours DOUBLE PRECISION,
    tags JSON,
    checklist JSON,
    attachments JSON,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    PRIMARY KEY (id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Indexes for project_tasks
CREATE INDEX idx_task_project_status ON public.project_tasks USING btree (project_id, status);
CREATE INDEX idx_task_assignee ON public.project_tasks USING btree (assignee_id);

-- Table: projects
CREATE TABLE projects (
    id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    project_type VARCHAR(50) NOT NULL,
    status VARCHAR(50),
    priority VARCHAR(20),
    owner_id UUID NOT NULL,
    team_id UUID NOT NULL,
    start_date TIMESTAMP WITHOUT TIME ZONE,
    due_date TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    archived_at TIMESTAMP WITHOUT TIME ZONE,
    meta_data JSON,
    tags JSON,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    PRIMARY KEY (id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Indexes for projects
CREATE INDEX idx_project_owner_status ON public.projects USING btree (owner_id, status);
CREATE INDEX idx_project_status ON public.projects USING btree (status);

-- Table: purchases
CREATE TABLE purchases (
    id UUID NOT NULL,
    product_id UUID NOT NULL,
    buyer_id UUID NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    currency VARCHAR(3),
    status VARCHAR(50),
    transaction_id VARCHAR(255) NOT NULL,
    payment_method VARCHAR(50),
    payment_id VARCHAR(255) NOT NULL,
    license_key VARCHAR(255),
    license_expires_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    FOREIGN KEY (buyer_id) REFERENCES users(id),
    UNIQUE (license_key),
    PRIMARY KEY (id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Indexes for purchases
CREATE UNIQUE INDEX purchases_license_key_key ON public.purchases USING btree (license_key);

-- Table: retrieval_sessions
CREATE TABLE retrieval_sessions (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    query_embedding VECTOR,
    filters JSONB DEFAULT '{}'::jsonb,
    retrieved_records ARRAY DEFAULT '{}'::uuid[],
    relevance_scores ARRAY DEFAULT '{}'::double precision[],
    retrieval_time_ms INTEGER,
    reranking_applied BOOLEAN DEFAULT false,
    selected_records ARRAY DEFAULT '{}'::uuid[],
    feedback_score DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for retrieval_sessions

-- Table: reviews
CREATE TABLE reviews (
    id UUID NOT NULL,
    product_id UUID NOT NULL,
    reviewer_id UUID NOT NULL,
    rating INTEGER NOT NULL,
    title VARCHAR(200),
    comment TEXT,
    is_verified_purchase BOOLEAN,
    helpful_count INTEGER,
    pros JSON,
    cons JSON,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

-- Indexes for reviews
CREATE INDEX idx_review_rating ON public.reviews USING btree (rating);
CREATE INDEX idx_review_product ON public.reviews USING btree (product_id);

-- Table: sales_goals
CREATE TABLE sales_goals (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    team_id UUID NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    revenue_target_cents INTEGER NOT NULL,
    deals_target INTEGER,
    activities_target INTEGER,
    revenue_actual_cents INTEGER,
    deals_actual INTEGER,
    activities_actual INTEGER,
    is_active BOOLEAN,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    PRIMARY KEY (id),
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for sales_goals
CREATE INDEX idx_sales_goal_user ON public.sales_goals USING btree (user_id);
CREATE INDEX idx_sales_goal_period ON public.sales_goals USING btree (period_start, period_end);

-- Table: security_events
CREATE TABLE security_events (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL,
    ip_address VARCHAR(45),
    request_path VARCHAR(255),
    details JSONB,
    severity VARCHAR(20) DEFAULT 'low'::character varying,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID,
    notes TEXT,
    PRIMARY KEY (id)
);

-- Indexes for security_events
CREATE INDEX idx_security_events_created_at ON public.security_events USING btree (created_at DESC);
CREATE INDEX idx_security_events_event_type ON public.security_events USING btree (event_type);
CREATE INDEX idx_security_events_user_id ON public.security_events USING btree (user_id);
CREATE INDEX idx_security_events_ip_address ON public.security_events USING btree (ip_address);

-- Table: spatial_ref_sys
CREATE TABLE spatial_ref_sys (
    srid INTEGER NOT NULL,
    auth_name VARCHAR(256),
    auth_srid INTEGER,
    srtext VARCHAR(2048),
    proj4text VARCHAR(2048),
    PRIMARY KEY (srid)
);

-- Indexes for spatial_ref_sys

-- Table: subscriptions
CREATE TABLE subscriptions (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    tier SUBSCRIPTIONTIER,
    status VARCHAR(50),
    stripe_customer_id VARCHAR(255) NOT NULL,
    stripe_subscription_id VARCHAR(255) NOT NULL,
    monthly_ai_requests INTEGER,
    used_ai_requests INTEGER,
    storage_limit_gb DOUBLE PRECISION,
    used_storage_gb DOUBLE PRECISION,
    monthly_budget DOUBLE PRECISION,
    current_period_start TIMESTAMP WITHOUT TIME ZONE,
    current_period_end TIMESTAMP WITHOUT TIME ZONE,
    canceled_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE (user_id)
);

-- Indexes for subscriptions
CREATE UNIQUE INDEX subscriptions_user_id_key ON public.subscriptions USING btree (user_id);

-- Table: summarizations
CREATE TABLE summarizations (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    source_type VARCHAR(100) NOT NULL,
    source_id UUID NOT NULL,
    summary_type VARCHAR(50) NOT NULL,
    summary_text TEXT NOT NULL,
    summary_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for summarizations
CREATE INDEX idx_summaries_source ON public.summarizations USING btree (source_type, source_id);

-- Table: system_config
CREATE TABLE system_config (
    key VARCHAR(100) NOT NULL,
    value JSON NOT NULL,
    description TEXT,
    config_type VARCHAR(50) NOT NULL,
    is_secret BOOLEAN,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    PRIMARY KEY (key)
);

-- Indexes for system_config

-- Table: system_secrets
CREATE TABLE system_secrets (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    secret_name VARCHAR(255) NOT NULL,
    secret_type VARCHAR(50) NOT NULL,
    encrypted_value TEXT NOT NULL,
    encryption_method VARCHAR(50) DEFAULT 'aes256'::character varying,
    service_name VARCHAR(255) NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_rotated_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE (secret_name)
);

-- Indexes for system_secrets
CREATE UNIQUE INDEX system_secrets_secret_name_key ON public.system_secrets USING btree (secret_name);
CREATE INDEX idx_secrets_name ON public.system_secrets USING btree (secret_name);
CREATE INDEX idx_secrets_service ON public.system_secrets USING btree (service_name);
CREATE INDEX idx_secrets_active ON public.system_secrets USING btree (is_active);

-- Table: task_comments
CREATE TABLE task_comments (
    id UUID NOT NULL,
    task_id UUID NOT NULL,
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    attachments JSON,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (task_id) REFERENCES project_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for task_comments

-- Table: task_dependencies
CREATE TABLE task_dependencies (
    id UUID NOT NULL,
    task_id UUID NOT NULL,
    predecessor_id UUID NOT NULL,
    dependency_type VARCHAR(20) NOT NULL,
    lag_hours DOUBLE PRECISION,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (predecessor_id) REFERENCES project_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES project_tasks(id) ON DELETE CASCADE
);

-- Indexes for task_dependencies

-- Table: task_executions
CREATE TABLE task_executions (
    id UUID NOT NULL,
    task_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    parameters JSON,
    result JSON,
    error_message TEXT,
    triggered_by VARCHAR(100),
    trigger_source VARCHAR(200),
    execution_time_ms INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITHOUT TIME ZONE,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id)
);

-- Indexes for task_executions
CREATE INDEX ix_task_executions_task_id ON public.task_executions USING btree (task_id);
CREATE INDEX idx_created_at ON public.task_executions USING btree (created_at);
CREATE INDEX idx_task_status ON public.task_executions USING btree (task_id, status);

-- Table: tasks
CREATE TABLE tasks (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to UUID,
    related_to_type VARCHAR(50) NOT NULL,
    related_to_id UUID NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    priority INTEGER DEFAULT 3,
    status VARCHAR(50) DEFAULT 'pending'::character varying,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES app_users(id),
    FOREIGN KEY (created_by) REFERENCES app_users(id),
    PRIMARY KEY (id)
);

-- Indexes for tasks
CREATE INDEX idx_tasks_assigned ON public.tasks USING btree (assigned_to);
CREATE INDEX idx_tasks_related ON public.tasks USING btree (related_to_type, related_to_id);
CREATE INDEX idx_tasks_status ON public.tasks USING btree (status);

-- Table: team_members
CREATE TABLE team_members (
    team_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(50),
    joined_at TIMESTAMP WITHOUT TIME ZONE,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Table: teams
CREATE TABLE teams (
    id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    logo_url VARCHAR(500),
    website VARCHAR(255),
    max_members INTEGER,
    owner_id UUID NOT NULL,
    is_active BOOLEAN,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    PRIMARY KEY (id)
);

-- Indexes for teams
CREATE UNIQUE INDEX ix_teams_slug ON public.teams USING btree (slug);

-- Table: user_sessions
CREATE TABLE user_sessions (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    refresh_token_hash VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    is_active BOOLEAN,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITHOUT TIME ZONE,
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (refresh_token_hash),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for user_sessions
CREATE UNIQUE INDEX user_sessions_refresh_token_hash_key ON public.user_sessions USING btree (refresh_token_hash);

-- Table: users
CREATE TABLE users (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (email),
    PRIMARY KEY (id)
);

-- Indexes for users
CREATE UNIQUE INDEX users_email_key ON public.users USING btree (email);

-- Table: vector_memories
CREATE TABLE vector_memories (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (collection_id) REFERENCES memory_collections(id),
    PRIMARY KEY (id)
);

-- Indexes for vector_memories
CREATE INDEX idx_vector_collection ON public.vector_memories USING btree (collection_id);
CREATE INDEX idx_vector_embedding ON public.vector_memories USING ivfflat (embedding vector_cosine_ops);

-- Table: vendors
CREATE TABLE vendors (
    id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(2),
    tax_id VARCHAR(50) NOT NULL,
    payment_terms VARCHAR(50),
    account_number VARCHAR(100),
    categories JSON,
    preferred BOOLEAN,
    is_active BOOLEAN,
    notes TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for vendors
CREATE INDEX idx_vendor_active ON public.vendors USING btree (is_active);
CREATE INDEX idx_vendor_name ON public.vendors USING btree (name);

-- Table: webhook_events
CREATE TABLE webhook_events (
    id UUID NOT NULL,
    source VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    headers JSON,
    payload JSON NOT NULL,
    signature VARCHAR(500),
    processed BOOLEAN,
    processing_result JSON,
    error_message TEXT,
    received_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITHOUT TIME ZONE,
    task_execution_id UUID NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (task_execution_id) REFERENCES task_executions(id)
);

-- Indexes for webhook_events
CREATE INDEX ix_webhook_events_processed ON public.webhook_events USING btree (processed);
CREATE INDEX ix_webhook_events_source ON public.webhook_events USING btree (source);

-- Table: webhooks
CREATE TABLE webhooks (
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    secret VARCHAR(255),
    events ARRAY,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for webhooks
CREATE INDEX idx_webhooks_active ON public.webhooks USING btree (is_active);

-- Table: workflow_runs
CREATE TABLE workflow_runs (
    id UUID NOT NULL,
    workflow_id UUID NOT NULL,
    status VARCHAR(50),
    trigger_data JSON,
    steps_completed INTEGER,
    steps_total INTEGER NOT NULL,
    output JSON,
    error TEXT,
    logs JSON,
    parent_run_id UUID NOT NULL,
    started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    duration_ms INTEGER,
    FOREIGN KEY (parent_run_id) REFERENCES workflow_runs(id),
    PRIMARY KEY (id),
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

-- Indexes for workflow_runs

-- Table: workflows
CREATE TABLE workflows (
    id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_config JSON NOT NULL,
    steps JSON NOT NULL,
    owner_id UUID NOT NULL,
    team_id UUID NOT NULL,
    is_active BOOLEAN,
    is_public BOOLEAN,
    tags JSON,
    meta_data JSON,
    version VARCHAR(20),
    run_count INTEGER,
    success_count INTEGER,
    last_run_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id),
    PRIMARY KEY (id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- Indexes for workflows
