-- Production Database Migrations for BrainOps
-- Version: 5.05
-- Date: 2025-08-18
-- CRITICAL: Run on production Supabase

BEGIN;

-- 1. Ensure AI monitoring columns exist
ALTER TABLE ai_agents 
ADD COLUMN IF NOT EXISTS last_active TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS total_executions INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS success_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS average_response_time_ms INTEGER DEFAULT 0;

-- 2. Create AI metrics table
CREATE TABLE IF NOT EXISTS ai_agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_id UUID REFERENCES ai_agents(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    execution_time_ms INTEGER,
    success BOOLEAN,
    tokens_used INTEGER,
    error_message TEXT,
    metadata JSONB
);

-- 3. Create system logs table for centralized logging
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    source VARCHAR(100),
    level VARCHAR(20),
    message TEXT,
    metadata JSONB
);

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_metrics_timestamp ON ai_agent_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_centerpoint_sync_log_started ON centerpoint_sync_log(started_at DESC);

-- 5. Add revenue tracking tables for MyRoofGenius
CREATE TABLE IF NOT EXISTS revenue_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    amount_cents BIGINT NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50),
    stripe_payment_intent_id VARCHAR(255),
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Add service tracking tables for WeatherCraft ERP
CREATE TABLE IF NOT EXISTS service_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id),
    service_type VARCHAR(100),
    scheduled_date DATE,
    completed_date DATE,
    technician_id UUID,
    labor_hours DECIMAL(10,2),
    materials_cost_cents BIGINT,
    labor_cost_cents BIGINT,
    status VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Update existing AI agents with proper data
UPDATE ai_agents 
SET last_active = NOW(),
    status = 'active'
WHERE status IS NULL OR status = '';

-- 8. Insert default AI agents if none exist
INSERT INTO ai_agents (id, name, type, status, capabilities, last_active)
SELECT * FROM (VALUES
    (gen_random_uuid(), 'Revenue Optimizer', 'revenue', 'active', '{"model": "claude-3-opus", "focus": "myroofgenius"}'::jsonb, NOW()),
    (gen_random_uuid(), 'Service Scheduler', 'operations', 'active', '{"model": "gpt-4", "focus": "weathercraft"}'::jsonb, NOW()),
    (gen_random_uuid(), 'Customer Success AI', 'support', 'active', '{"model": "claude-3-opus", "focus": "both"}'::jsonb, NOW()),
    (gen_random_uuid(), 'Sales Assistant', 'sales', 'active', '{"model": "claude-3-opus", "focus": "myroofgenius"}'::jsonb, NOW()),
    (gen_random_uuid(), 'Field Operations AI', 'field_ops', 'active', '{"model": "gpt-4", "focus": "weathercraft"}'::jsonb, NOW())
) AS t(id, name, type, status, capabilities, last_active)
WHERE NOT EXISTS (SELECT 1 FROM ai_agents WHERE type IN ('revenue', 'operations', 'support', 'sales', 'field_ops'));

-- 9. Create view for MyRoofGenius revenue dashboard
CREATE OR REPLACE VIEW myroofgenius_revenue_metrics AS
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as transaction_count,
    SUM(amount_cents) / 100.0 as revenue_usd,
    AVG(amount_cents) / 100.0 as avg_transaction_value
FROM revenue_transactions
WHERE status = 'completed'
GROUP BY DATE_TRUNC('month', created_at);

-- 10. Create view for WeatherCraft service metrics
CREATE OR REPLACE VIEW weathercraft_service_metrics AS
SELECT 
    DATE_TRUNC('month', scheduled_date) as month,
    COUNT(*) as jobs_count,
    SUM(labor_hours) as total_labor_hours,
    SUM(materials_cost_cents + labor_cost_cents) / 100.0 as total_revenue,
    COUNT(DISTINCT technician_id) as active_technicians
FROM service_jobs
WHERE status IN ('completed', 'invoiced')
GROUP BY DATE_TRUNC('month', scheduled_date);

COMMIT;

-- Verification queries
SELECT 'AI Agents' as table_name, COUNT(*) as count FROM ai_agents WHERE status = 'active'
UNION ALL
SELECT 'Revenue Transactions', COUNT(*) FROM revenue_transactions
UNION ALL
SELECT 'Service Jobs', COUNT(*) FROM service_jobs
UNION ALL
SELECT 'System Logs', COUNT(*) FROM system_logs;
