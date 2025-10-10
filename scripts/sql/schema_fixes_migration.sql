-- BrainOps Database Schema Fixes
-- Generated: 2025-07-23T12:00:57.593652
-- This migration fixes all identified issues

BEGIN;

-- Create migration tracking table if not exists
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========== CRITICAL FIXES ==========

-- Fix: project_members: Missing PRIMARY KEY
ALTER TABLE project_members ADD COLUMN id UUID DEFAULT gen_random_uuid() PRIMARY KEY;

-- Fix: team_members: Missing PRIMARY KEY
ALTER TABLE team_members ADD COLUMN id UUID DEFAULT gen_random_uuid() PRIMARY KEY;

-- ========== MAJOR FIXES ==========

-- Fix: memory_entries.is_active: VARCHAR without length limit
ALTER TABLE memory_entries ALTER COLUMN is_active TYPE TEXT;

-- Fix: leads.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE leads ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE leads SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: leads.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE leads ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE leads SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: communications.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE communications ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE communications SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: communications.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE communications ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE communications SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: opportunities.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE opportunities ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE opportunities SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: opportunities.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE opportunities ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE opportunities SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: projects.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE projects ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE projects SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: projects.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE projects ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: project_tasks.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE project_tasks ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE project_tasks SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: project_tasks.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE project_tasks ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE project_tasks SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: payments.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE payments ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE payments SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: payments.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE payments ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE payments SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: expenses.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE expenses ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE expenses SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: expenses.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE expenses ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE expenses SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: invoices.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE invoices ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE invoices SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: invoices.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE invoices ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE invoices SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: jobs.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE jobs ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE jobs SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: jobs.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE jobs ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: estimates.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE estimates ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE estimates SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: estimates.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE estimates ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE estimates SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: activities.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE activities ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE activities SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: task_executions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE task_executions ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE task_executions SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: campaigns.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE campaigns ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE campaigns SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: campaigns.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE campaigns ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE campaigns SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: reviews.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE reviews ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE reviews SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: reviews.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE reviews ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE reviews SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: memories.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE memories ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE memories SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: memories.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE memories ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE memories SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: ai_usage_logs.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE ai_usage_logs ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE ai_usage_logs SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: workflows.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE workflows ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE workflows SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: workflows.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE workflows ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE workflows SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: customers.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE customers ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE customers SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: customers.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE customers ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: vendors.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE vendors ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE vendors SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: vendors.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE vendors ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE vendors SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: teams.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE teams ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE teams SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: teams.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE teams ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE teams SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: notifications.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE notifications ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE notifications SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: subscriptions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE subscriptions ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE subscriptions SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: subscriptions.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE subscriptions ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE subscriptions SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: user_sessions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE user_sessions ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE user_sessions SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: sales_goals.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE sales_goals ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE sales_goals SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: sales_goals.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE sales_goals ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE sales_goals SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: lead_sources.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE lead_sources ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE lead_sources SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: lead_sources.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE lead_sources ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE lead_sources SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: purchases.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE purchases ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE purchases SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: api_keys.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE api_keys ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE api_keys SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: customer_segments.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE customer_segments ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE customer_segments SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: customer_segments.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE customer_segments ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE customer_segments SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: inspections.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE inspections ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE inspections SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: task_comments.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE task_comments ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE task_comments SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: task_comments.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE task_comments ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE task_comments SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: document_templates.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE document_templates ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE document_templates SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: document_templates.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE document_templates ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE document_templates SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: integrations.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE integrations ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE integrations SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: system_config.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE system_config ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE system_config SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- Fix: agent_executions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE agent_executions ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE agent_executions SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- Fix: task_dependencies.created_at: Missing DEFAULT CURRENT_TIMESTAMP
ALTER TABLE task_dependencies ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
UPDATE task_dependencies SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;

-- ========== PERFORMANCE FIXES ==========

-- Fix: memory_sync.idx_memory_sync_initiated_at: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_sync_initiated_at; -- Uncomment after review

-- Fix: memory_sync.idx_sync_time: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_sync_time; -- Uncomment after review

-- Fix: memory_entries.idx_session_id: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_session_id; -- Uncomment after review

-- Fix: memory_entries.idx_importance: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_importance; -- Uncomment after review

-- Fix: memory_entries.ix_memory_entries_user_id: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_memory_entries_user_id; -- Uncomment after review

-- Fix: memory_entries.ix_memory_entries_session_id: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_memory_entries_session_id; -- Uncomment after review

-- Fix: memory_entries.ix_memory_entries_memory_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_memory_entries_memory_type; -- Uncomment after review

-- Fix: memory_entries.idx_memory_owner: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_owner; -- Uncomment after review

-- Fix: memory_entries.idx_memory_entries_category: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_entries_category; -- Uncomment after review

-- Fix: memory_entries.idx_memory_entries_accessed: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_entries_accessed; -- Uncomment after review

-- Fix: memory_entries.idx_memory_accessed: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_accessed; -- Uncomment after review

-- Fix: cross_ai_memory.idx_cross_ai_source: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_cross_ai_source; -- Uncomment after review

-- Fix: cross_ai_memory.idx_cross_ai_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_cross_ai_key; -- Uncomment after review

-- Fix: cross_ai_memory.idx_cross_ai_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_cross_ai_type; -- Uncomment after review

-- Fix: cross_ai_memory.idx_cross_ai_embedding: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_cross_ai_embedding; -- Uncomment after review

-- Fix: memory_records.idx_memory_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_type; -- Uncomment after review

-- Fix: memory_records.idx_memory_category: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_category; -- Uncomment after review

-- Fix: memory_records.idx_memory_tags: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_tags; -- Uncomment after review

-- Fix: memory_records.idx_memory_created: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_created; -- Uncomment after review

-- Fix: memory_records.idx_memory_embedding: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_embedding; -- Uncomment after review

-- Fix: estimate_records.idx_estimates_project: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_estimates_project; -- Uncomment after review

-- Fix: estimate_records.idx_estimates_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_estimates_status; -- Uncomment after review

-- Fix: estimate_records.idx_estimates_embedding: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_estimates_embedding; -- Uncomment after review

-- Fix: embeddings.idx_embeddings_source: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_embeddings_source; -- Uncomment after review

-- Fix: embeddings.idx_embeddings_vector: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_embeddings_vector; -- Uncomment after review

-- Fix: vector_memories.idx_vector_collection: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_vector_collection; -- Uncomment after review

-- Fix: vector_memories.idx_vector_embedding: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_vector_embedding; -- Uncomment after review

-- Fix: production_memory_embeddings.idx_prod_embed_memory: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_embed_memory; -- Uncomment after review

-- Fix: production_memory_embeddings.idx_prod_embed_vector: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_embed_vector; -- Uncomment after review

-- Fix: document_chunks.idx_chunks_document: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_chunks_document; -- Uncomment after review

-- Fix: document_chunks.idx_chunks_embedding: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_chunks_embedding; -- Uncomment after review

-- Fix: app_users.app_users_email_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS app_users_email_key; -- Uncomment after review

-- Fix: app_users.app_users_username_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS app_users_username_key; -- Uncomment after review

-- Fix: app_users.idx_app_users_username: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_app_users_username; -- Uncomment after review

-- Fix: leads.leads_email_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS leads_email_key; -- Uncomment after review

-- Fix: leads.idx_lead_assigned: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_lead_assigned; -- Uncomment after review

-- Fix: leads.idx_lead_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_lead_status; -- Uncomment after review

-- Fix: leads.idx_lead_score: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_lead_score; -- Uncomment after review

-- Fix: leads.idx_lead_source: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_lead_source; -- Uncomment after review

-- Fix: communications.idx_communication_user: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_communication_user; -- Uncomment after review

-- Fix: communications.idx_communication_scheduled: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_communication_scheduled; -- Uncomment after review

-- Fix: communications.idx_communication_entity: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_communication_entity; -- Uncomment after review

-- Fix: communications.idx_communication_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_communication_type; -- Uncomment after review

-- Fix: security_events.idx_security_events_created_at: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_security_events_created_at; -- Uncomment after review

-- Fix: security_events.idx_security_events_event_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_security_events_event_type; -- Uncomment after review

-- Fix: security_events.idx_security_events_user_id: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_security_events_user_id; -- Uncomment after review

-- Fix: security_events.idx_security_events_ip_address: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_security_events_ip_address; -- Uncomment after review

-- Fix: opportunities.idx_opportunity_customer: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_opportunity_customer; -- Uncomment after review

-- Fix: opportunities.idx_opportunity_stage: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_opportunity_stage; -- Uncomment after review

-- Fix: opportunities.idx_opportunity_assigned: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_opportunity_assigned; -- Uncomment after review

-- Fix: projects.idx_project_owner_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_project_owner_status; -- Uncomment after review

-- Fix: project_tasks.idx_task_assignee: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_task_assignee; -- Uncomment after review

-- Fix: production_memory_entries.idx_prod_memory_owner: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_memory_owner; -- Uncomment after review

-- Fix: production_memory_entries.idx_prod_memory_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_memory_key; -- Uncomment after review

-- Fix: production_memory_entries.idx_prod_memory_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_memory_type; -- Uncomment after review

-- Fix: production_memory_entries.idx_prod_memory_tags: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_memory_tags; -- Uncomment after review

-- Fix: production_memory_entries.unique_production_memory_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS unique_production_memory_key; -- Uncomment after review

-- Fix: payments.idx_payment_customer: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_payment_customer; -- Uncomment after review

-- Fix: payments.idx_payment_date: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_payment_date; -- Uncomment after review

-- Fix: payments.idx_payment_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_payment_status; -- Uncomment after review

-- Fix: payments.idx_payment_invoice: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_payment_invoice; -- Uncomment after review

-- Fix: payments.ix_payments_payment_number: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_payments_payment_number; -- Uncomment after review

-- Fix: expenses.idx_expense_date: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_expense_date; -- Uncomment after review

-- Fix: expenses.ix_expenses_expense_number: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_expenses_expense_number; -- Uncomment after review

-- Fix: expenses.idx_expense_category: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_expense_category; -- Uncomment after review

-- Fix: expenses.idx_expense_job: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_expense_job; -- Uncomment after review

-- Fix: expenses.idx_expense_billable: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_expense_billable; -- Uncomment after review

-- Fix: admin_action_logs.idx_admin_logs_action_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_admin_logs_action_type; -- Uncomment after review

-- Fix: admin_action_logs.idx_admin_logs_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_admin_logs_status; -- Uncomment after review

-- Fix: admin_action_logs.idx_admin_logs_user_id: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_admin_logs_user_id; -- Uncomment after review

-- Fix: admin_action_logs.idx_admin_logs_started_at: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_admin_logs_started_at; -- Uncomment after review

-- Fix: admin_action_logs.idx_admin_logs_environment: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_admin_logs_environment; -- Uncomment after review

-- Fix: invoices.idx_invoice_customer: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_invoice_customer; -- Uncomment after review

-- Fix: invoices.ix_invoices_invoice_number: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_invoices_invoice_number; -- Uncomment after review

-- Fix: invoices.idx_invoice_due_date: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_invoice_due_date; -- Uncomment after review

-- Fix: invoices.idx_invoice_date: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_invoice_date; -- Uncomment after review

-- Fix: invoices.idx_invoice_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_invoice_status; -- Uncomment after review

-- Fix: jobs.idx_job_dates: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_job_dates; -- Uncomment after review

-- Fix: jobs.idx_job_customer: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_job_customer; -- Uncomment after review

-- Fix: jobs.idx_job_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_job_status; -- Uncomment after review

-- Fix: jobs.ix_jobs_job_number: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_jobs_job_number; -- Uncomment after review

-- Fix: system_secrets.system_secrets_secret_name_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS system_secrets_secret_name_key; -- Uncomment after review

-- Fix: system_secrets.idx_secrets_name: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_secrets_name; -- Uncomment after review

-- Fix: system_secrets.idx_secrets_service: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_secrets_service; -- Uncomment after review

-- Fix: system_secrets.idx_secrets_active: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_secrets_active; -- Uncomment after review

-- Fix: ai_agents.idx_ai_agents_active: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_ai_agents_active; -- Uncomment after review

-- Fix: estimates.estimates_estimate_number_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS estimates_estimate_number_key; -- Uncomment after review

-- Fix: estimates.ix_estimates_estimate_number: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_estimates_estimate_number; -- Uncomment after review

-- Fix: estimates.idx_estimate_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_estimate_status; -- Uncomment after review

-- Fix: estimates.idx_estimate_customer: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_estimate_customer; -- Uncomment after review

-- Fix: activities.idx_activity_entity: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_activity_entity; -- Uncomment after review

-- Fix: activities.idx_activity_user: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_activity_user; -- Uncomment after review

-- Fix: activities.idx_activity_created: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_activity_created; -- Uncomment after review

-- Fix: activities.idx_activity_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_activity_type; -- Uncomment after review

-- Fix: inventory_items.idx_inventory_sku: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_inventory_sku; -- Uncomment after review

-- Fix: inventory_items.idx_inventory_business: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_inventory_business; -- Uncomment after review

-- Fix: inventory_items.inventory_items_sku_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS inventory_items_sku_key; -- Uncomment after review

-- Fix: tasks.idx_tasks_assigned: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_tasks_assigned; -- Uncomment after review

-- Fix: tasks.idx_tasks_related: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_tasks_related; -- Uncomment after review

-- Fix: tasks.idx_tasks_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_tasks_status; -- Uncomment after review

-- Fix: deployment_records.idx_deployments_service: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_deployments_service; -- Uncomment after review

-- Fix: deployment_records.idx_deployments_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_deployments_status; -- Uncomment after review

-- Fix: deployment_records.idx_deployments_deployed_at: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_deployments_deployed_at; -- Uncomment after review

-- Fix: agent_memory_access.idx_agent_access_agent: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_agent_access_agent; -- Uncomment after review

-- Fix: agent_memory_access.idx_agent_access_memory: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_agent_access_memory; -- Uncomment after review

-- Fix: agent_memory_access.idx_agent_access_time: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_agent_access_time; -- Uncomment after review

-- Fix: task_executions.ix_task_executions_task_id: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_task_executions_task_id; -- Uncomment after review

-- Fix: task_executions.idx_created_at: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_created_at; -- Uncomment after review

-- Fix: task_executions.idx_task_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_task_status; -- Uncomment after review

-- Fix: campaigns.idx_campaign_dates: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_campaign_dates; -- Uncomment after review

-- Fix: campaigns.idx_campaign_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_campaign_status; -- Uncomment after review

-- Fix: campaigns.idx_campaign_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_campaign_type; -- Uncomment after review

-- Fix: auth_tokens.idx_auth_tokens_user: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_auth_tokens_user; -- Uncomment after review

-- Fix: auth_tokens.idx_auth_tokens_expires: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_auth_tokens_expires; -- Uncomment after review

-- Fix: auth_tokens.auth_tokens_token_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS auth_tokens_token_key; -- Uncomment after review

-- Fix: memory_contexts.idx_contexts_parent: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_contexts_parent; -- Uncomment after review

-- Fix: memory_contexts.idx_contexts_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_contexts_type; -- Uncomment after review

-- Fix: reviews.idx_review_rating: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_review_rating; -- Uncomment after review

-- Fix: reviews.idx_review_product: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_review_product; -- Uncomment after review

-- Fix: knowledge_entries.idx_knowledge_category: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_knowledge_category; -- Uncomment after review

-- Fix: knowledge_entries.idx_knowledge_validated: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_knowledge_validated; -- Uncomment after review

-- Fix: ai_usage_logs.idx_ai_usage_user_created: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_ai_usage_user_created; -- Uncomment after review

-- Fix: ai_usage_logs.idx_ai_usage_service_model: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_ai_usage_service_model; -- Uncomment after review

-- Fix: webhook_events.ix_webhook_events_processed: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_webhook_events_processed; -- Uncomment after review

-- Fix: webhook_events.ix_webhook_events_source: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_webhook_events_source; -- Uncomment after review

-- Fix: customers.idx_customer_active: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_customer_active; -- Uncomment after review

-- Fix: customers.idx_customer_email: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_customer_email; -- Uncomment after review

-- Fix: vendors.idx_vendor_active: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_vendor_active; -- Uncomment after review

-- Fix: vendors.idx_vendor_name: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_vendor_name; -- Uncomment after review

-- Fix: businesses.idx_businesses_name: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_businesses_name; -- Uncomment after review

-- Fix: businesses.idx_businesses_active: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_businesses_active; -- Uncomment after review

-- Fix: memory_collections.idx_collections_owner: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_collections_owner; -- Uncomment after review

-- Fix: memory_collections.idx_collections_type: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_collections_type; -- Uncomment after review

-- Fix: memory_metadata.idx_memory_meta_memory: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_meta_memory; -- Uncomment after review

-- Fix: memory_metadata.idx_memory_meta_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_memory_meta_key; -- Uncomment after review

-- Fix: production_memory_metadata.idx_prod_meta_memory: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_meta_memory; -- Uncomment after review

-- Fix: production_memory_metadata.idx_prod_meta_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_meta_key; -- Uncomment after review

-- Fix: production_memory_sync.idx_prod_sync_memory: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_sync_memory; -- Uncomment after review

-- Fix: production_memory_sync.idx_prod_sync_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_prod_sync_status; -- Uncomment after review

-- Fix: automation_executions.idx_executions_workflow: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_executions_workflow; -- Uncomment after review

-- Fix: automation_executions.idx_executions_status: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_executions_status; -- Uncomment after review

-- Fix: database_health_checks.idx_health_checks_timestamp: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_health_checks_timestamp; -- Uncomment after review

-- Fix: database_health_checks.idx_health_checks_healthy: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_health_checks_healthy; -- Uncomment after review

-- Fix: teams.ix_teams_slug: Unused index (0 scans)
-- DROP INDEX IF EXISTS ix_teams_slug; -- Uncomment after review

-- Fix: notifications.idx_notification_user_unread: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_notification_user_unread; -- Uncomment after review

-- Fix: summarizations.idx_summaries_source: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_summaries_source; -- Uncomment after review

-- Fix: automation_workflows.idx_workflows_active: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_workflows_active; -- Uncomment after review

-- Fix: automation_templates.idx_templates_category: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_templates_category; -- Uncomment after review

-- Fix: automation_rules.idx_rules_workflow: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_rules_workflow; -- Uncomment after review

-- Fix: automation_actions.idx_actions_rule: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_actions_rule; -- Uncomment after review

-- Fix: user_sessions.user_sessions_refresh_token_hash_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS user_sessions_refresh_token_hash_key; -- Uncomment after review

-- Fix: webhooks.idx_webhooks_active: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_webhooks_active; -- Uncomment after review

-- Fix: integration_configs.idx_integration_configs: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_integration_configs; -- Uncomment after review

-- Fix: embedding_models.embedding_models_name_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS embedding_models_name_key; -- Uncomment after review

-- Fix: sales_goals.idx_sales_goal_user: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_sales_goal_user; -- Uncomment after review

-- Fix: sales_goals.idx_sales_goal_period: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_sales_goal_period; -- Uncomment after review

-- Fix: lead_sources.lead_sources_name_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS lead_sources_name_key; -- Uncomment after review

-- Fix: lead_sources.idx_lead_source_category: Unused index (0 scans)
-- DROP INDEX IF EXISTS idx_lead_source_category; -- Uncomment after review

-- Fix: purchases.purchases_license_key_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS purchases_license_key_key; -- Uncomment after review

-- Fix: api_keys.api_keys_key_hash_key: Unused index (0 scans)
-- DROP INDEX IF EXISTS api_keys_key_hash_key; -- Uncomment after review

-- Fix: teams.owner_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_teams_owner_id ON teams(owner_id);

-- Fix: orders.product_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id);

-- Fix: contacts.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id);

-- Fix: ai_logs.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_ai_logs_user_id ON ai_logs(user_id);

-- Fix: dashboard_insights.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_dashboard_insights_user_id ON dashboard_insights(user_id);

-- Fix: digital_deliveries.order_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_digital_deliveries_order_id ON digital_deliveries(order_id);

-- Fix: purchases.product_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_purchases_product_id ON purchases(product_id);

-- Fix: purchases.buyer_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_purchases_buyer_id ON purchases(buyer_id);

-- Fix: reviews.reviewer_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_reviews_reviewer_id ON reviews(reviewer_id);

-- Fix: api_keys.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);

-- Fix: user_sessions.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

-- Fix: notifications.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);

-- Fix: integrations.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_integrations_user_id ON integrations(user_id);

-- Fix: memories.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);

-- Fix: document_templates.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_document_templates_user_id ON document_templates(user_id);

-- Fix: ai_usage_logs.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_user_id ON ai_usage_logs(user_id);

-- Fix: campaigns.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_campaigns_created_by ON campaigns(created_by);

-- Fix: customer_segments.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_customer_segments_created_by ON customer_segments(created_by);

-- Fix: agent_executions.task_execution_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_agent_executions_task_execution_id ON agent_executions(task_execution_id);

-- Fix: webhook_events.task_execution_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_webhook_events_task_execution_id ON webhook_events(task_execution_id);

-- Fix: team_members.team_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);

-- Fix: team_members.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);

-- Fix: projects.owner_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);

-- Fix: projects.team_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_projects_team_id ON projects(team_id);

-- Fix: workflows.owner_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_workflows_owner_id ON workflows(owner_id);

-- Fix: workflows.team_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_workflows_team_id ON workflows(team_id);

-- Fix: payments.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_payments_created_by ON payments(created_by);

-- Fix: expenses.vendor_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_expenses_vendor_id ON expenses(vendor_id);

-- Fix: expenses.employee_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_expenses_employee_id ON expenses(employee_id);

-- Fix: expenses.invoice_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_expenses_invoice_id ON expenses(invoice_id);

-- Fix: expenses.approved_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_expenses_approved_by ON expenses(approved_by);

-- Fix: expenses.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_expenses_created_by ON expenses(created_by);

-- Fix: sales_goals.team_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_sales_goals_team_id ON sales_goals(team_id);

-- Fix: sales_goals.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_sales_goals_created_by ON sales_goals(created_by);

-- Fix: project_members.project_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id);

-- Fix: project_members.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id);

-- Fix: project_tasks.project_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_project_tasks_project_id ON project_tasks(project_id);

-- Fix: project_tasks.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_project_tasks_created_by ON project_tasks(created_by);

-- Fix: inspections.project_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_inspections_project_id ON inspections(project_id);

-- Fix: inspections.inspector_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_inspections_inspector_id ON inspections(inspector_id);

-- Fix: workflow_runs.workflow_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow_id ON workflow_runs(workflow_id);

-- Fix: workflow_runs.parent_run_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_workflow_runs_parent_run_id ON workflow_runs(parent_run_id);

-- Fix: task_comments.task_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_task_comments_task_id ON task_comments(task_id);

-- Fix: task_comments.user_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_task_comments_user_id ON task_comments(user_id);

-- Fix: inspection_photos.inspection_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_inspection_photos_inspection_id ON inspection_photos(inspection_id);

-- Fix: task_dependencies.task_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task_id ON task_dependencies(task_id);

-- Fix: task_dependencies.predecessor_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_task_dependencies_predecessor_id ON task_dependencies(predecessor_id);

-- Fix: jobs.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON jobs(created_by);

-- Fix: estimates.converted_to_invoice_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_estimates_converted_to_invoice_id ON estimates(converted_to_invoice_id);

-- Fix: leads.campaign_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_leads_campaign_id ON leads(campaign_id);

-- Fix: invoices.estimate_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_invoices_estimate_id ON invoices(estimate_id);

-- Fix: opportunities.lead_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_opportunities_lead_id ON opportunities(lead_id);

-- Fix: invoices.job_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_invoices_job_id ON invoices(job_id);

-- Fix: leads.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_leads_created_by ON leads(created_by);

-- Fix: invoices.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_invoices_created_by ON invoices(created_by);

-- Fix: estimates.inspection_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_estimates_inspection_id ON estimates(inspection_id);

-- Fix: leads.converted_to_opportunity_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_leads_converted_to_opportunity_id ON leads(converted_to_opportunity_id);

-- Fix: jobs.estimate_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_jobs_estimate_id ON jobs(estimate_id);

-- Fix: opportunities.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_opportunities_created_by ON opportunities(created_by);

-- Fix: estimates.project_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_estimates_project_id ON estimates(project_id);

-- Fix: jobs.invoice_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_jobs_invoice_id ON jobs(invoice_id);

-- Fix: estimates.created_by_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_estimates_created_by_id ON estimates(created_by_id);

-- Fix: estimates.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_estimates_created_by ON estimates(created_by);

-- Fix: tasks.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by);

-- Fix: production_memory_entries.context_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_production_memory_entries_context_id ON production_memory_entries(context_id);

-- Fix: automation_workflows.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_automation_workflows_created_by ON automation_workflows(created_by);

-- Fix: automation_templates.created_by: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_automation_templates_created_by ON automation_templates(created_by);

-- Fix: embeddings.model_id: Foreign key without index
CREATE INDEX IF NOT EXISTS idx_embeddings_model_id ON embeddings(model_id);

-- ========== ADD UPDATE TRIGGERS ==========

-- Create update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_memory_entries_updated_at ON memory_entries;
CREATE TRIGGER update_memory_entries_updated_at BEFORE UPDATE ON memory_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_cross_ai_memory_updated_at ON cross_ai_memory;
CREATE TRIGGER update_cross_ai_memory_updated_at BEFORE UPDATE ON cross_ai_memory FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_memory_records_updated_at ON memory_records;
CREATE TRIGGER update_memory_records_updated_at BEFORE UPDATE ON memory_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_estimate_records_updated_at ON estimate_records;
CREATE TRIGGER update_estimate_records_updated_at BEFORE UPDATE ON estimate_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_app_users_updated_at ON app_users;
CREATE TRIGGER update_app_users_updated_at BEFORE UPDATE ON app_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_communications_updated_at ON communications;
CREATE TRIGGER update_communications_updated_at BEFORE UPDATE ON communications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_opportunities_updated_at ON opportunities;
CREATE TRIGGER update_opportunities_updated_at BEFORE UPDATE ON opportunities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_project_tasks_updated_at ON project_tasks;
CREATE TRIGGER update_project_tasks_updated_at BEFORE UPDATE ON project_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_production_memory_entries_updated_at ON production_memory_entries;
CREATE TRIGGER update_production_memory_entries_updated_at BEFORE UPDATE ON production_memory_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_payments_updated_at ON payments;
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_expenses_updated_at ON expenses;
CREATE TRIGGER update_expenses_updated_at BEFORE UPDATE ON expenses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_admin_action_logs_updated_at ON admin_action_logs;
CREATE TRIGGER update_admin_action_logs_updated_at BEFORE UPDATE ON admin_action_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_invoices_updated_at ON invoices;
CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_system_secrets_updated_at ON system_secrets;
CREATE TRIGGER update_system_secrets_updated_at BEFORE UPDATE ON system_secrets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_estimates_updated_at ON estimates;
CREATE TRIGGER update_estimates_updated_at BEFORE UPDATE ON estimates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_inventory_items_updated_at ON inventory_items;
CREATE TRIGGER update_inventory_items_updated_at BEFORE UPDATE ON inventory_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_campaigns_updated_at ON campaigns;
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_memory_contexts_updated_at ON memory_contexts;
CREATE TRIGGER update_memory_contexts_updated_at BEFORE UPDATE ON memory_contexts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_reviews_updated_at ON reviews;
CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_knowledge_entries_updated_at ON knowledge_entries;
CREATE TRIGGER update_knowledge_entries_updated_at BEFORE UPDATE ON knowledge_entries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_memories_updated_at ON memories;
CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_workflows_updated_at ON workflows;
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_vendors_updated_at ON vendors;
CREATE TRIGGER update_vendors_updated_at BEFORE UPDATE ON vendors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_businesses_updated_at ON businesses;
CREATE TRIGGER update_businesses_updated_at BEFORE UPDATE ON businesses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_memory_collections_updated_at ON memory_collections;
CREATE TRIGGER update_memory_collections_updated_at BEFORE UPDATE ON memory_collections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_memory_metadata_updated_at ON memory_metadata;
CREATE TRIGGER update_memory_metadata_updated_at BEFORE UPDATE ON memory_metadata FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_production_memory_metadata_updated_at ON production_memory_metadata;
CREATE TRIGGER update_production_memory_metadata_updated_at BEFORE UPDATE ON production_memory_metadata FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_teams_updated_at ON teams;
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_automation_workflows_updated_at ON automation_workflows;
CREATE TRIGGER update_automation_workflows_updated_at BEFORE UPDATE ON automation_workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_automation_templates_updated_at ON automation_templates;
CREATE TRIGGER update_automation_templates_updated_at BEFORE UPDATE ON automation_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_automation_rules_updated_at ON automation_rules;
CREATE TRIGGER update_automation_rules_updated_at BEFORE UPDATE ON automation_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_webhooks_updated_at ON webhooks;
CREATE TRIGGER update_webhooks_updated_at BEFORE UPDATE ON webhooks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_integration_configs_updated_at ON integration_configs;
CREATE TRIGGER update_integration_configs_updated_at BEFORE UPDATE ON integration_configs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_sales_goals_updated_at ON sales_goals;
CREATE TRIGGER update_sales_goals_updated_at BEFORE UPDATE ON sales_goals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_lead_sources_updated_at ON lead_sources;
CREATE TRIGGER update_lead_sources_updated_at BEFORE UPDATE ON lead_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_customer_segments_updated_at ON customer_segments;
CREATE TRIGGER update_customer_segments_updated_at BEFORE UPDATE ON customer_segments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_agent_registry_updated_at ON agent_registry;
CREATE TRIGGER update_agent_registry_updated_at BEFORE UPDATE ON agent_registry FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_task_comments_updated_at ON task_comments;
CREATE TRIGGER update_task_comments_updated_at BEFORE UPDATE ON task_comments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_document_templates_updated_at ON document_templates;
CREATE TRIGGER update_document_templates_updated_at BEFORE UPDATE ON document_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
DROP TRIGGER IF EXISTS update_system_config_updated_at ON system_config;
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Record migration
INSERT INTO schema_migrations (migration_name) VALUES ('brainops_schema_fixes_001') ON CONFLICT DO NOTHING;

COMMIT;
