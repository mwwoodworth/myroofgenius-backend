-- Migration: 20251225_missing_tables.sql
-- Description: Create missing tables identified in AUDIT_REPORT.md
-- Author: Gemini 3.0 Pro
-- Date: 2025-12-25

-- Enable pgcrypto for UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- 1. Stripe Automation Tables
-- Source: routes/stripe_automation.py
-- ==========================================

CREATE TABLE IF NOT EXISTS stripe_revenue_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mrr BIGINT DEFAULT 0,
    arr BIGINT DEFAULT 0,
    total_revenue BIGINT DEFAULT 0,
    metric_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID, -- For multi-tenancy
    data JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS stripe_subscription_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_tier TEXT,
    active_count INT DEFAULT 0,
    mrr BIGINT DEFAULT 0,
    churn_rate NUMERIC(10, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID,
    data JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS stripe_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT,
    payload JSONB,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);


-- ==========================================
-- 2. Warehouse & Inventory Management Tables
-- Source: routes/warehouse_management.py & routes/inventory_management.py
-- ==========================================

-- Core Warehouse Tables (referenced but potentially missing)
CREATE TABLE IF NOT EXISTS warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_code TEXT,
    name TEXT,
    warehouse_type TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    country TEXT,
    phone TEXT,
    email TEXT,
    manager TEXT,
    capacity_sqft INT,
    operating_hours JSONB,
    features TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS warehouse_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id),
    zone_code TEXT,
    zone_name TEXT,
    zone_type TEXT,
    area_sqft INT,
    temperature_range JSONB,
    humidity_range JSONB,
    security_level INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS warehouse_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id),
    zone_id UUID REFERENCES warehouse_zones(id),
    location_code TEXT,
    full_path TEXT,
    aisle TEXT,
    rack TEXT,
    shelf TEXT,
    bin TEXT,
    storage_type TEXT,
    max_weight NUMERIC,
    max_volume NUMERIC,
    is_available BOOLEAN DEFAULT TRUE,
    is_occupied BOOLEAN DEFAULT FALSE,
    current_item_id UUID,
    current_quantity INT DEFAULT 0,
    last_activity_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Warehouse Transfers
CREATE TABLE IF NOT EXISTS warehouse_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_number TEXT,
    from_warehouse_id UUID REFERENCES warehouses(id),
    to_warehouse_id UUID REFERENCES warehouses(id),
    transfer_date DATE,
    reason TEXT,
    priority INT DEFAULT 5,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS warehouse_transfer_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_id UUID REFERENCES warehouse_transfers(id),
    item_id UUID,
    quantity INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Warehouse Discrepancies
CREATE TABLE IF NOT EXISTS warehouse_discrepancies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id),
    reference_type TEXT,
    reference_id UUID,
    description TEXT,
    reported_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Picking Tasks / Orders
CREATE TABLE IF NOT EXISTS picking_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    picking_number TEXT,
    warehouse_id UUID REFERENCES warehouses(id),
    order_id TEXT,
    customer_id UUID,
    method TEXT,
    priority INT,
    required_date DATE,
    assigned_to TEXT,
    status TEXT,
    picker TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS picking_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    picking_order_id UUID REFERENCES picking_orders(id),
    item_id UUID,
    quantity INT,
    location_id UUID,
    picked_quantity INT DEFAULT 0,
    picked_from_location UUID,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS picking_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id),
    picking_order_id UUID REFERENCES picking_orders(id),
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS picking_exceptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    picking_order_id UUID REFERENCES picking_orders(id),
    description TEXT,
    reported_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Receiving Orders
CREATE TABLE IF NOT EXISTS receiving_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receiving_number TEXT,
    warehouse_id UUID REFERENCES warehouses(id),
    supplier_id UUID,
    purchase_order_id UUID,
    expected_date DATE,
    actual_date DATE,
    carrier TEXT,
    tracking_number TEXT,
    status TEXT,
    received_by TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS receiving_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receiving_order_id UUID REFERENCES receiving_orders(id),
    item_id UUID,
    expected_quantity INT,
    received_quantity INT DEFAULT 0,
    unit TEXT,
    condition TEXT,
    discrepancy BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Putaway Tasks
CREATE TABLE IF NOT EXISTS putaway_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receiving_id UUID REFERENCES receiving_orders(id),
    item_id UUID,
    quantity INT,
    from_location TEXT,
    to_location TEXT,
    strategy TEXT,
    assigned_to TEXT,
    priority INT,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Shipping Orders
CREATE TABLE IF NOT EXISTS shipping_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipping_number TEXT,
    warehouse_id UUID REFERENCES warehouses(id),
    order_id TEXT,
    customer_id UUID,
    ship_to_address TEXT,
    carrier TEXT,
    service_type TEXT,
    ship_date DATE,
    tracking_number TEXT,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS shipping_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipping_order_id UUID REFERENCES shipping_orders(id),
    item_id UUID,
    quantity INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Inventory Adjustments
CREATE TABLE IF NOT EXISTS inventory_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id),
    location_id UUID REFERENCES warehouse_locations(id),
    item_id UUID,
    previous_quantity INT,
    new_quantity INT,
    variance INT,
    reason TEXT,
    approved_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Generic 'stock' table for audit compliance, though likely covered by inventory_stock in code
CREATE TABLE IF NOT EXISTS stock (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID,
    quantity INT DEFAULT 0,
    location_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);


-- ==========================================
-- 3. Generic/Placeholder Tables for Missing Features
-- Source: AUDIT_REPORT.md (various modules)
-- ==========================================

-- Common helper for creating generic tables
-- Defines: id, name, status, description, created_at, updated_at, tenant_id, data (JSONB)

-- AB Testing
CREATE TABLE IF NOT EXISTS ab_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    status TEXT,
    description TEXT,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID,
    data JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ab_test_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID REFERENCES ab_tests(id),
    user_id UUID,
    variant TEXT,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Assets
CREATE TABLE IF NOT EXISTS asset_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    asset_type TEXT,
    status TEXT,
    serial_number TEXT,
    purchase_date DATE,
    value NUMERIC(12, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID,
    data JSONB DEFAULT '{}'::jsonb
);

-- Budget
CREATE TABLE IF NOT EXISTS budget (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    period TEXT,
    amount NUMERIC(12, 2),
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID,
    data JSONB DEFAULT '{}'::jsonb
);

-- Collections
CREATE TABLE IF NOT EXISTS collection_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID,
    amount_due NUMERIC(12, 2),
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID,
    data JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS collection_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES collection_cases(id),
    action_type TEXT,
    performed_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS payment_arrangements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES collection_cases(id),
    amount NUMERIC(12, 2),
    due_date DATE,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Content Management
CREATE TABLE IF NOT EXISTS content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    slug TEXT,
    body TEXT,
    content_type TEXT,
    status TEXT,
    author_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID,
    data JSONB DEFAULT '{}'::jsonb
);

-- Customer Feedback
CREATE TABLE IF NOT EXISTS nps_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID,
    score INT,
    comment TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID,
    data JSONB DEFAULT '{}'::jsonb
);

-- Data Governance
CREATE TABLE IF NOT EXISTS data_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    policy_text TEXT,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS consent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    policy_id UUID REFERENCES data_policies(id),
    granted BOOLEAN,
    granted_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Data Warehouse / ETL
CREATE TABLE IF NOT EXISTS data_sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name TEXT,
    status TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    rows_processed INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS etl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    schedule TEXT,
    last_run_status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Project Management / Gantt
CREATE TABLE IF NOT EXISTS gantt_charts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    name TEXT,
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS milestone_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    name TEXT,
    due_date DATE,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS project_creation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    status TEXT,
    template_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS project_planning (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    plan_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Advertising
CREATE TABLE IF NOT EXISTS ad_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    platform TEXT,
    status TEXT,
    budget NUMERIC(12, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID,
    data JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ad_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES ad_campaigns(id),
    date DATE,
    impressions INT,
    clicks INT,
    conversions INT,
    spend NUMERIC(12, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- HR / Recruitment
CREATE TABLE IF NOT EXISTS leave (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    start_date DATE,
    end_date DATE,
    leave_type TEXT,
    status TEXT,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS leave_management_extended (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    policy_id UUID,
    balance NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS interview (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID,
    job_id UUID,
    interviewer_id UUID,
    scheduled_at TIMESTAMPTZ,
    status TEXT,
    feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS application (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID,
    candidate_name TEXT,
    email TEXT,
    resume_url TEXT,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS shift_management (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS overtime_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    date DATE,
    hours NUMERIC,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Incident / Inspection / Quality
CREATE TABLE IF NOT EXISTS incident (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    severity TEXT,
    status TEXT,
    description TEXT,
    reported_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS inspection (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_type TEXT,
    reference_id UUID,
    inspector_id UUID,
    status TEXT,
    result TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS quality_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_type TEXT,
    reference_id UUID,
    check_name TEXT,
    passed BOOLEAN,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS risk (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    category TEXT,
    probability TEXT,
    impact TEXT,
    mitigation_plan TEXT,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- KPI / Metrics / Scoring
CREATE TABLE IF NOT EXISTS kpi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    value NUMERIC,
    target NUMERIC,
    period TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS metric_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name TEXT,
    value NUMERIC,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    tags JSONB,
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS scoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_type TEXT,
    reference_id UUID,
    score NUMERIC,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Sales / CRM / Opportunity
CREATE TABLE IF NOT EXISTS opportunity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    customer_id UUID,
    value NUMERIC(12, 2),
    stage TEXT,
    probability INT,
    close_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Purchasing
CREATE TABLE IF NOT EXISTS purchase_requisitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id UUID,
    item_description TEXT,
    quantity INT,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);
-- purchase_orders is covered in warehouse section via receiving_orders relation, but ensuring it exists generic if needed
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number TEXT,
    supplier_id UUID,
    status TEXT,
    order_date DATE,
    expected_date DATE,
    subtotal NUMERIC,
    shipping_cost NUMERIC,
    tax_amount NUMERIC,
    total_amount NUMERIC,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

CREATE TABLE IF NOT EXISTS purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID REFERENCES purchase_orders(id),
    item_id UUID,
    quantity INT,
    unit_cost NUMERIC,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Resource Allocation
CREATE TABLE IF NOT EXISTS resource_allocation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id UUID,
    project_id UUID,
    start_date DATE,
    end_date DATE,
    allocation_percent INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Scheduled Tasks
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_name TEXT,
    schedule TEXT,
    last_run TIMESTAMPTZ,
    next_run TIMESTAMPTZ,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- SLA
CREATE TABLE IF NOT EXISTS sla (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    description TEXT,
    response_time_minutes INT,
    resolution_time_minutes INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Notifications
CREATE TABLE IF NOT EXISTS push_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    title TEXT,
    body TEXT,
    sent_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Warranty
CREATE TABLE IF NOT EXISTS warranty (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID,
    start_date DATE,
    end_date DATE,
    provider TEXT,
    status TEXT,
    coverage_details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- Workflow Automation
CREATE TABLE IF NOT EXISTS workflow_automation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    trigger_type TEXT,
    config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID
);

-- ==========================================
-- 4. Enable Row Level Security (RLS)
-- ==========================================

DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN (
            'stripe_revenue_metrics', 'stripe_subscription_analytics', 'stripe_logs',
            'warehouses', 'warehouse_zones', 'warehouse_locations', 'warehouse_transfers', 
            'warehouse_transfer_items', 'warehouse_discrepancies', 'picking_orders', 
            'picking_order_items', 'picking_tasks', 'picking_exceptions', 'receiving_orders', 
            'receiving_order_items', 'putaway_tasks', 'shipping_orders', 'shipping_order_items', 
            'inventory_adjustments', 'stock', 'ab_tests', 'ab_test_assignments', 'asset_registry', 
            'budget', 'collection_cases', 'collection_actions', 'payment_arrangements', 'content', 
            'nps_responses', 'data_policies', 'consent', 'data_sync_jobs', 'etl_jobs', 'gantt_charts', 
            'milestone_tracking', 'project_creation', 'project_planning', 'ad_campaigns', 
            'ad_performance', 'leave', 'leave_management_extended', 'interview', 'application', 
            'shift_management', 'overtime_tracking', 'incident', 'inspection', 'quality_checks', 
            'risk', 'kpi', 'metric_tracking', 'scoring', 'opportunity', 'purchase_requisitions', 
            'purchase_orders', 'purchase_order_items', 'resource_allocation', 'scheduled_tasks', 
            'sla', 'push_notifications', 'warranty', 'workflow_automation'
        )
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY;', t);
        
        -- Policy: Users can only see data for their tenant
        -- Assumes current_setting('app.current_tenant') is set by middleware/backend
        -- We use a DO block safely; if policy exists it might fail so we wrap or use specific naming
        -- Simpler to just create if not exists using a check or just try-catch in real migration logic, 
        -- but for this SQL script we will trust the DO block environment or let it fail if policy exists (which it shouldn't as these are new tables)
        
        BEGIN
            EXECUTE format('
                CREATE POLICY tenant_isolation_policy ON %I
                USING (tenant_id = current_setting(''app.current_tenant'', true)::uuid);
            ', t);
        EXCEPTION WHEN duplicate_object THEN
            NULL; -- Policy already exists
        END;
        
        -- Index on tenant_id for performance
        EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_tenant_id ON %I (tenant_id);', t, t);
    END LOOP;
END $$;
