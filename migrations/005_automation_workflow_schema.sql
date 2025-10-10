-- WeatherCraft ERP Automation & Workflow Schema
-- Phase 6 & 7: Document Management, Automation Engine

-- ============================================================================
-- DOCUMENT MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Document Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    document_type VARCHAR(100), -- contract, proposal, invoice, report, photo, drawing
    
    -- File Info
    file_path VARCHAR(500),
    s3_key VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    
    -- Version Control
    version INTEGER DEFAULT 1,
    parent_document_id UUID REFERENCES documents(id),
    is_latest BOOLEAN DEFAULT TRUE,
    
    -- Associations
    entity_type VARCHAR(50), -- customer, job, estimate, invoice, vendor
    entity_id UUID,
    
    -- Metadata
    tags TEXT[],
    metadata JSONB,
    
    -- OCR/Content
    extracted_text TEXT,
    is_searchable BOOLEAN DEFAULT FALSE,
    
    -- Security
    access_level VARCHAR(50) DEFAULT 'private', -- public, internal, private, confidential
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, archived, deleted
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Document Templates
CREATE TABLE IF NOT EXISTS document_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Template Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(100), -- contract, proposal, invoice, letter
    
    -- Content
    template_content TEXT,
    html_template TEXT,
    
    -- Variables
    template_variables JSONB, -- List of merge fields
    
    -- Settings
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Contracts
CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Parties
    customer_id UUID NOT NULL REFERENCES customers(id),
    job_id UUID REFERENCES jobs(id),
    estimate_id UUID REFERENCES estimates(id),
    
    -- Contract Details
    contract_type VARCHAR(50), -- service, maintenance, warranty, installation
    title VARCHAR(255),
    
    -- Dates
    effective_date DATE,
    expiration_date DATE,
    
    -- Value
    contract_value DECIMAL(12,2),
    
    -- Terms
    payment_terms TEXT,
    scope_of_work TEXT,
    exclusions TEXT,
    terms_conditions TEXT,
    
    -- Signatures
    customer_signature_status VARCHAR(50) DEFAULT 'pending', -- pending, signed, declined
    customer_signed_at TIMESTAMPTZ,
    customer_signature_ip VARCHAR(50),
    
    company_signature_status VARCHAR(50) DEFAULT 'pending',
    company_signed_at TIMESTAMPTZ,
    company_signed_by UUID REFERENCES users(id),
    
    -- DocuSign Integration
    docusign_envelope_id VARCHAR(100),
    docusign_status VARCHAR(50),
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- draft, sent, signed, executed, expired, terminated
    
    -- Renewal
    is_renewable BOOLEAN DEFAULT FALSE,
    renewal_terms TEXT,
    renewal_notice_days INTEGER,
    
    -- Documents
    document_id UUID REFERENCES documents(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Change Orders
CREATE TABLE IF NOT EXISTS change_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    change_order_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- References
    contract_id UUID REFERENCES contracts(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    
    -- Details
    description TEXT NOT NULL,
    reason TEXT,
    
    -- Impact
    cost_impact DECIMAL(12,2),
    schedule_impact_days INTEGER,
    
    -- Approval
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected, executed
    
    customer_approved BOOLEAN DEFAULT FALSE,
    customer_approved_at TIMESTAMPTZ,
    
    internal_approved BOOLEAN DEFAULT FALSE,
    internal_approved_by UUID REFERENCES users(id),
    internal_approved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- ============================================================================
-- AUTOMATION ENGINE
-- ============================================================================

-- Workflow Definitions
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Workflow Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- lead, sales, operations, service, finance
    
    -- Trigger
    trigger_type VARCHAR(50), -- event, schedule, manual, webhook
    trigger_config JSONB,
    
    -- Conditions
    conditions JSONB, -- When to run
    
    -- Actions
    actions JSONB, -- What to do
    
    -- Settings
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE, -- System workflows can't be deleted
    
    -- Execution
    last_run TIMESTAMPTZ,
    run_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Workflow Executions
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id),
    
    -- Execution Details
    execution_number VARCHAR(50) UNIQUE NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Trigger
    trigger_source VARCHAR(100),
    trigger_data JSONB,
    
    -- Status
    status VARCHAR(50) DEFAULT 'running', -- running, completed, failed, cancelled
    
    -- Results
    steps_total INTEGER DEFAULT 0,
    steps_completed INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Context
    context_data JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow Steps
CREATE TABLE IF NOT EXISTS workflow_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    
    -- Step Info
    step_number INTEGER NOT NULL,
    step_name VARCHAR(255),
    action_type VARCHAR(100), -- email, sms, task, update, webhook, condition
    
    -- Execution
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed, skipped
    
    -- Input/Output
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Automation Rules
CREATE TABLE IF NOT EXISTS automation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Rule Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50), -- assignment, escalation, notification, update
    
    -- Target
    entity_type VARCHAR(50), -- lead, job, invoice, service_ticket
    
    -- Conditions
    conditions JSONB NOT NULL,
    /* Example:
    {
        "all": [
            {"field": "status", "operator": "equals", "value": "new"},
            {"field": "priority", "operator": "in", "value": ["high", "emergency"]}
        ]
    }
    */
    
    -- Actions
    actions JSONB NOT NULL,
    /* Example:
    [
        {"type": "assign", "user_id": "..."},
        {"type": "notify", "template": "high_priority_alert"}
    ]
    */
    
    -- Settings
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 100,
    
    -- Performance
    execution_count INTEGER DEFAULT 0,
    last_executed TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email Templates
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Template Info
    name VARCHAR(255) NOT NULL,
    template_key VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Content
    subject VARCHAR(500),
    html_body TEXT,
    text_body TEXT,
    
    -- Variables
    available_variables JSONB,
    
    -- Settings
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notification Queue
CREATE TABLE IF NOT EXISTS notification_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Recipient
    recipient_type VARCHAR(50), -- user, customer, vendor
    recipient_id UUID,
    recipient_email VARCHAR(255),
    recipient_phone VARCHAR(20),
    
    -- Notification
    notification_type VARCHAR(50), -- email, sms, push, in-app
    template_id UUID REFERENCES email_templates(id),
    
    -- Content
    subject VARCHAR(500),
    message TEXT,
    data JSONB,
    
    -- Scheduling
    scheduled_for TIMESTAMPTZ DEFAULT NOW(),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, sending, sent, failed, cancelled
    attempts INTEGER DEFAULT 0,
    
    -- Results
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    provider_response JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Task Templates
CREATE TABLE IF NOT EXISTS task_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Template Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    
    -- Task Details
    default_title VARCHAR(255),
    default_description TEXT,
    default_priority VARCHAR(20) DEFAULT 'normal',
    default_due_days INTEGER, -- Days from creation
    
    -- Assignment
    default_assignee_role VARCHAR(50),
    
    -- Checklist
    checklist_items JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Automated Tasks
CREATE TABLE IF NOT EXISTS automated_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Task Info
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Source
    source_type VARCHAR(50), -- workflow, rule, schedule
    source_id UUID,
    
    -- Assignment
    assigned_to UUID REFERENCES users(id),
    assigned_role VARCHAR(50),
    
    -- Timing
    due_date DATE,
    priority VARCHAR(20) DEFAULT 'normal',
    
    -- Reference
    entity_type VARCHAR(50),
    entity_id UUID,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, in-progress, completed, cancelled
    completed_at TIMESTAMPTZ,
    completed_by UUID REFERENCES users(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- BUSINESS AUTOMATIONS
-- ============================================================================

-- Lead Nurturing Campaigns
CREATE TABLE IF NOT EXISTS nurture_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Campaign Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Target
    target_criteria JSONB, -- Lead scoring, source, etc.
    
    -- Sequence
    email_sequence JSONB, -- Array of emails with delays
    
    -- Settings
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Performance
    leads_enrolled INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaign Enrollments
CREATE TABLE IF NOT EXISTS campaign_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES nurture_campaigns(id),
    lead_id UUID NOT NULL REFERENCES leads(id),
    
    -- Status
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),
    current_step INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active', -- active, paused, completed, unsubscribed
    
    -- Results
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    links_clicked INTEGER DEFAULT 0,
    
    converted BOOLEAN DEFAULT FALSE,
    converted_at TIMESTAMPTZ,
    
    UNIQUE(campaign_id, lead_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Document Indexes
CREATE INDEX idx_documents_entity ON documents(entity_type, entity_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_tags ON documents USING GIN(tags);
CREATE INDEX idx_contracts_customer ON contracts(customer_id);
CREATE INDEX idx_contracts_status ON contracts(status);

-- Workflow Indexes
CREATE INDEX idx_workflows_active ON workflows(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_workflow_executions_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_automation_rules_entity ON automation_rules(entity_type);
CREATE INDEX idx_notification_queue_status ON notification_queue(status);
CREATE INDEX idx_notification_queue_scheduled ON notification_queue(scheduled_for)
    WHERE status = 'pending';

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Generate document numbers
CREATE OR REPLACE FUNCTION generate_document_number() RETURNS trigger AS $$
BEGIN
    IF NEW.document_number IS NULL THEN
        NEW.document_number := 'DOC-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || 
                               LPAD(nextval('document_number_seq')::text, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE IF NOT EXISTS document_number_seq START 1;

CREATE TRIGGER generate_document_number_trigger
    BEFORE INSERT ON documents
    FOR EACH ROW
    EXECUTE FUNCTION generate_document_number();

-- Update workflow execution counts
CREATE OR REPLACE FUNCTION update_workflow_counts() RETURNS trigger AS $$
BEGIN
    UPDATE workflows
    SET 
        run_count = run_count + 1,
        success_count = CASE 
            WHEN NEW.status = 'completed' THEN success_count + 1 
            ELSE success_count 
        END,
        error_count = CASE 
            WHEN NEW.status = 'failed' THEN error_count + 1 
            ELSE error_count 
        END,
        last_run = NEW.started_at,
        updated_at = NOW()
    WHERE id = NEW.workflow_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_workflow_counts_trigger
    AFTER UPDATE OF status ON workflow_executions
    FOR EACH ROW
    WHEN (OLD.status = 'running' AND NEW.status IN ('completed', 'failed'))
    EXECUTE FUNCTION update_workflow_counts();

-- Process notification queue
CREATE OR REPLACE FUNCTION process_notification_queue() RETURNS INTEGER AS $$
DECLARE
    processed_count INTEGER := 0;
    notification RECORD;
BEGIN
    FOR notification IN 
        SELECT * FROM notification_queue
        WHERE status = 'pending'
        AND scheduled_for <= NOW()
        ORDER BY scheduled_for
        LIMIT 100
    LOOP
        -- Mark as sending
        UPDATE notification_queue
        SET status = 'sending', attempts = attempts + 1
        WHERE id = notification.id;
        
        -- Here you would call the actual notification service
        -- For now, just mark as sent
        UPDATE notification_queue
        SET status = 'sent', sent_at = NOW()
        WHERE id = notification.id;
        
        processed_count := processed_count + 1;
    END LOOP;
    
    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- Auto-expire contracts
CREATE OR REPLACE FUNCTION auto_expire_contracts() RETURNS void AS $$
BEGIN
    UPDATE contracts
    SET status = 'expired', updated_at = NOW()
    WHERE status IN ('executed', 'signed')
    AND expiration_date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;