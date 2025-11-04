# BrainOps Database Schema Analysis Report

**Generated:** 2025-07-23T12:00:42.262023

## Executive Summary

- **Total Tables:** 92
- **Total Issues Found:** 486
  - Critical: 2
  - Major: 59
  - Minor: 191
  - Performance: 228
  - Security: 6

## Issues by Severity

### 🔴 Critical Issues
These must be fixed immediately:

- project_members: Missing PRIMARY KEY
- team_members: Missing PRIMARY KEY

### 🟠 Major Issues
These should be fixed soon:

- memory_entries.is_active: VARCHAR without length limit
- leads.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- leads.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- communications.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- communications.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- opportunities.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- opportunities.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- projects.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- projects.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- project_tasks.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- project_tasks.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- payments.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- payments.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- expenses.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- expenses.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- invoices.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- invoices.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- jobs.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- jobs.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- estimates.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- estimates.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- activities.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- task_executions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- campaigns.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- campaigns.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- reviews.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- reviews.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- memories.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- memories.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- ai_usage_logs.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- workflows.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- workflows.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- customers.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- customers.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- vendors.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- vendors.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- teams.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- teams.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- notifications.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- subscriptions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- subscriptions.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- user_sessions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- sales_goals.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- sales_goals.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- lead_sources.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- lead_sources.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- purchases.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- api_keys.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- customer_segments.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- customer_segments.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- inspections.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- task_comments.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- task_comments.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- document_templates.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- document_templates.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- integrations.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- system_config.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
- agent_executions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
- task_dependencies.created_at: Missing DEFAULT CURRENT_TIMESTAMP

### ⚡ Performance Issues
- memory_sync.idx_memory_sync_initiated_at: Unused index (0 scans)
- memory_sync.idx_sync_time: Unused index (0 scans)
- memory_entries.idx_session_id: Unused index (0 scans)
- memory_entries.idx_importance: Unused index (0 scans)
- memory_entries.ix_memory_entries_user_id: Unused index (0 scans)
- memory_entries.ix_memory_entries_session_id: Unused index (0 scans)
- memory_entries.ix_memory_entries_memory_type: Unused index (0 scans)
- memory_entries.idx_memory_owner: Unused index (0 scans)
- memory_entries.idx_memory_entries_category: Unused index (0 scans)
- memory_entries.idx_memory_entries_accessed: Unused index (0 scans)
- memory_entries.idx_memory_accessed: Unused index (0 scans)
- cross_ai_memory.idx_cross_ai_source: Unused index (0 scans)
- cross_ai_memory.idx_cross_ai_key: Unused index (0 scans)
- cross_ai_memory.idx_cross_ai_type: Unused index (0 scans)
- cross_ai_memory.idx_cross_ai_embedding: Unused index (0 scans)
- memory_records.idx_memory_type: Unused index (0 scans)
- memory_records.idx_memory_category: Unused index (0 scans)
- memory_records.idx_memory_tags: Unused index (0 scans)
- memory_records.idx_memory_created: Unused index (0 scans)
- memory_records.idx_memory_embedding: Unused index (0 scans)
- estimate_records.idx_estimates_project: Unused index (0 scans)
- estimate_records.idx_estimates_status: Unused index (0 scans)
- estimate_records.idx_estimates_embedding: Unused index (0 scans)
- embeddings.idx_embeddings_source: Unused index (0 scans)
- embeddings.idx_embeddings_vector: Unused index (0 scans)
- vector_memories.idx_vector_collection: Unused index (0 scans)
- vector_memories.idx_vector_embedding: Unused index (0 scans)
- production_memory_embeddings.idx_prod_embed_memory: Unused index (0 scans)
- production_memory_embeddings.idx_prod_embed_vector: Unused index (0 scans)
- document_chunks.idx_chunks_document: Unused index (0 scans)
- document_chunks.idx_chunks_embedding: Unused index (0 scans)
- app_users.app_users_email_key: Unused index (0 scans)
- app_users.app_users_username_key: Unused index (0 scans)
- app_users.idx_app_users_username: Unused index (0 scans)
- leads.leads_email_key: Unused index (0 scans)
- leads.idx_lead_assigned: Unused index (0 scans)
- leads.idx_lead_status: Unused index (0 scans)
- leads.idx_lead_score: Unused index (0 scans)
- leads.idx_lead_source: Unused index (0 scans)
- communications.idx_communication_user: Unused index (0 scans)
- communications.idx_communication_scheduled: Unused index (0 scans)
- communications.idx_communication_entity: Unused index (0 scans)
- communications.idx_communication_type: Unused index (0 scans)
- security_events.idx_security_events_created_at: Unused index (0 scans)
- security_events.idx_security_events_event_type: Unused index (0 scans)
- security_events.idx_security_events_user_id: Unused index (0 scans)
- security_events.idx_security_events_ip_address: Unused index (0 scans)
- opportunities.idx_opportunity_customer: Unused index (0 scans)
- opportunities.idx_opportunity_stage: Unused index (0 scans)
- opportunities.idx_opportunity_assigned: Unused index (0 scans)
- projects.idx_project_owner_status: Unused index (0 scans)
- project_tasks.idx_task_assignee: Unused index (0 scans)
- production_memory_entries.idx_prod_memory_owner: Unused index (0 scans)
- production_memory_entries.idx_prod_memory_key: Unused index (0 scans)
- production_memory_entries.idx_prod_memory_type: Unused index (0 scans)
- production_memory_entries.idx_prod_memory_tags: Unused index (0 scans)
- production_memory_entries.unique_production_memory_key: Unused index (0 scans)
- payments.idx_payment_customer: Unused index (0 scans)
- payments.idx_payment_date: Unused index (0 scans)
- payments.idx_payment_status: Unused index (0 scans)
- payments.idx_payment_invoice: Unused index (0 scans)
- payments.ix_payments_payment_number: Unused index (0 scans)
- expenses.idx_expense_date: Unused index (0 scans)
- expenses.ix_expenses_expense_number: Unused index (0 scans)
- expenses.idx_expense_category: Unused index (0 scans)
- expenses.idx_expense_job: Unused index (0 scans)
- expenses.idx_expense_billable: Unused index (0 scans)
- admin_action_logs.idx_admin_logs_action_type: Unused index (0 scans)
- admin_action_logs.idx_admin_logs_status: Unused index (0 scans)
- admin_action_logs.idx_admin_logs_user_id: Unused index (0 scans)
- admin_action_logs.idx_admin_logs_started_at: Unused index (0 scans)
- admin_action_logs.idx_admin_logs_environment: Unused index (0 scans)
- invoices.idx_invoice_customer: Unused index (0 scans)
- invoices.ix_invoices_invoice_number: Unused index (0 scans)
- invoices.idx_invoice_due_date: Unused index (0 scans)
- invoices.idx_invoice_date: Unused index (0 scans)
- invoices.idx_invoice_status: Unused index (0 scans)
- jobs.idx_job_dates: Unused index (0 scans)
- jobs.idx_job_customer: Unused index (0 scans)
- jobs.idx_job_status: Unused index (0 scans)
- jobs.ix_jobs_job_number: Unused index (0 scans)
- system_secrets.system_secrets_secret_name_key: Unused index (0 scans)
- system_secrets.idx_secrets_name: Unused index (0 scans)
- system_secrets.idx_secrets_service: Unused index (0 scans)
- system_secrets.idx_secrets_active: Unused index (0 scans)
- ai_agents.idx_ai_agents_active: Unused index (0 scans)
- estimates.estimates_estimate_number_key: Unused index (0 scans)
- estimates.ix_estimates_estimate_number: Unused index (0 scans)
- estimates.idx_estimate_status: Unused index (0 scans)
- estimates.idx_estimate_customer: Unused index (0 scans)
- activities.idx_activity_entity: Unused index (0 scans)
- activities.idx_activity_user: Unused index (0 scans)
- activities.idx_activity_created: Unused index (0 scans)
- activities.idx_activity_type: Unused index (0 scans)
- inventory_items.idx_inventory_sku: Unused index (0 scans)
- inventory_items.idx_inventory_business: Unused index (0 scans)
- inventory_items.inventory_items_sku_key: Unused index (0 scans)
- tasks.idx_tasks_assigned: Unused index (0 scans)
- tasks.idx_tasks_related: Unused index (0 scans)
- tasks.idx_tasks_status: Unused index (0 scans)
- deployment_records.idx_deployments_service: Unused index (0 scans)
- deployment_records.idx_deployments_status: Unused index (0 scans)
- deployment_records.idx_deployments_deployed_at: Unused index (0 scans)
- agent_memory_access.idx_agent_access_agent: Unused index (0 scans)
- agent_memory_access.idx_agent_access_memory: Unused index (0 scans)
- agent_memory_access.idx_agent_access_time: Unused index (0 scans)
- task_executions.ix_task_executions_task_id: Unused index (0 scans)
- task_executions.idx_created_at: Unused index (0 scans)
- task_executions.idx_task_status: Unused index (0 scans)
- campaigns.idx_campaign_dates: Unused index (0 scans)
- campaigns.idx_campaign_status: Unused index (0 scans)
- campaigns.idx_campaign_type: Unused index (0 scans)
- auth_tokens.idx_auth_tokens_user: Unused index (0 scans)
- auth_tokens.idx_auth_tokens_expires: Unused index (0 scans)
- auth_tokens.auth_tokens_token_key: Unused index (0 scans)
- memory_contexts.idx_contexts_parent: Unused index (0 scans)
- memory_contexts.idx_contexts_type: Unused index (0 scans)
- reviews.idx_review_rating: Unused index (0 scans)
- reviews.idx_review_product: Unused index (0 scans)
- knowledge_entries.idx_knowledge_category: Unused index (0 scans)
- knowledge_entries.idx_knowledge_validated: Unused index (0 scans)
- ai_usage_logs.idx_ai_usage_user_created: Unused index (0 scans)
- ai_usage_logs.idx_ai_usage_service_model: Unused index (0 scans)
- webhook_events.ix_webhook_events_processed: Unused index (0 scans)
- webhook_events.ix_webhook_events_source: Unused index (0 scans)
- customers.idx_customer_active: Unused index (0 scans)
- customers.idx_customer_email: Unused index (0 scans)
- vendors.idx_vendor_active: Unused index (0 scans)
- vendors.idx_vendor_name: Unused index (0 scans)
- businesses.idx_businesses_name: Unused index (0 scans)
- businesses.idx_businesses_active: Unused index (0 scans)
- memory_collections.idx_collections_owner: Unused index (0 scans)
- memory_collections.idx_collections_type: Unused index (0 scans)
- memory_metadata.idx_memory_meta_memory: Unused index (0 scans)
- memory_metadata.idx_memory_meta_key: Unused index (0 scans)
- production_memory_metadata.idx_prod_meta_memory: Unused index (0 scans)
- production_memory_metadata.idx_prod_meta_key: Unused index (0 scans)
- production_memory_sync.idx_prod_sync_memory: Unused index (0 scans)
- production_memory_sync.idx_prod_sync_status: Unused index (0 scans)
- automation_executions.idx_executions_workflow: Unused index (0 scans)
- automation_executions.idx_executions_status: Unused index (0 scans)
- database_health_checks.idx_health_checks_timestamp: Unused index (0 scans)
- database_health_checks.idx_health_checks_healthy: Unused index (0 scans)
- teams.ix_teams_slug: Unused index (0 scans)
- notifications.idx_notification_user_unread: Unused index (0 scans)
- summarizations.idx_summaries_source: Unused index (0 scans)
- automation_workflows.idx_workflows_active: Unused index (0 scans)
- automation_templates.idx_templates_category: Unused index (0 scans)
- automation_rules.idx_rules_workflow: Unused index (0 scans)
- automation_actions.idx_actions_rule: Unused index (0 scans)
- user_sessions.user_sessions_refresh_token_hash_key: Unused index (0 scans)
- webhooks.idx_webhooks_active: Unused index (0 scans)
- integration_configs.idx_integration_configs: Unused index (0 scans)
- embedding_models.embedding_models_name_key: Unused index (0 scans)
- sales_goals.idx_sales_goal_user: Unused index (0 scans)
- sales_goals.idx_sales_goal_period: Unused index (0 scans)
- lead_sources.lead_sources_name_key: Unused index (0 scans)
- lead_sources.idx_lead_source_category: Unused index (0 scans)
- purchases.purchases_license_key_key: Unused index (0 scans)
- api_keys.api_keys_key_hash_key: Unused index (0 scans)
- teams.owner_id: Foreign key without index
- orders.product_id: Foreign key without index
- contacts.user_id: Foreign key without index
- ai_logs.user_id: Foreign key without index
- dashboard_insights.user_id: Foreign key without index
- digital_deliveries.order_id: Foreign key without index
- purchases.product_id: Foreign key without index
- purchases.buyer_id: Foreign key without index
- reviews.reviewer_id: Foreign key without index
- api_keys.user_id: Foreign key without index
- user_sessions.user_id: Foreign key without index
- notifications.user_id: Foreign key without index
- integrations.user_id: Foreign key without index
- memories.user_id: Foreign key without index
- document_templates.user_id: Foreign key without index
- ai_usage_logs.user_id: Foreign key without index
- campaigns.created_by: Foreign key without index
- customer_segments.created_by: Foreign key without index
- agent_executions.task_execution_id: Foreign key without index
- webhook_events.task_execution_id: Foreign key without index
- team_members.team_id: Foreign key without index
- team_members.user_id: Foreign key without index
- projects.owner_id: Foreign key without index
- projects.team_id: Foreign key without index
- workflows.owner_id: Foreign key without index
- workflows.team_id: Foreign key without index
- payments.created_by: Foreign key without index
- expenses.vendor_id: Foreign key without index
- expenses.employee_id: Foreign key without index
- expenses.invoice_id: Foreign key without index
- expenses.approved_by: Foreign key without index
- expenses.created_by: Foreign key without index
- sales_goals.team_id: Foreign key without index
- sales_goals.created_by: Foreign key without index
- project_members.project_id: Foreign key without index
- project_members.user_id: Foreign key without index
- project_tasks.project_id: Foreign key without index
- project_tasks.created_by: Foreign key without index
- inspections.project_id: Foreign key without index
- inspections.inspector_id: Foreign key without index
- workflow_runs.workflow_id: Foreign key without index
- workflow_runs.parent_run_id: Foreign key without index
- task_comments.task_id: Foreign key without index
- task_comments.user_id: Foreign key without index
- inspection_photos.inspection_id: Foreign key without index
- task_dependencies.task_id: Foreign key without index
- task_dependencies.predecessor_id: Foreign key without index
- jobs.created_by: Foreign key without index
- estimates.converted_to_invoice_id: Foreign key without index
- leads.campaign_id: Foreign key without index
- invoices.estimate_id: Foreign key without index
- opportunities.lead_id: Foreign key without index
- invoices.job_id: Foreign key without index
- leads.created_by: Foreign key without index
- invoices.created_by: Foreign key without index
- estimates.inspection_id: Foreign key without index
- leads.converted_to_opportunity_id: Foreign key without index
- jobs.estimate_id: Foreign key without index
- opportunities.created_by: Foreign key without index
- estimates.project_id: Foreign key without index
- jobs.invoice_id: Foreign key without index
- estimates.created_by_id: Foreign key without index
- estimates.created_by: Foreign key without index
- tasks.created_by: Foreign key without index
- production_memory_entries.context_id: Foreign key without index
- automation_workflows.created_by: Foreign key without index
- automation_templates.created_by: Foreign key without index
- embeddings.model_id: Foreign key without index

### 🔒 Security Issues
- security_events: Row Level Security disabled
- agent_registry: Row Level Security disabled
- admin_action_logs: Row Level Security disabled
- database_health_checks: Row Level Security disabled
- deployment_records: Row Level Security disabled
- system_secrets: Row Level Security disabled

## Table Analysis

### activities
- **Size:** 48 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 6
  - activities.created_at: Should be NOT NULL
  - activities.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - activities.idx_activity_entity: Unused index (0 scans)
  - activities.idx_activity_user: Unused index (0 scans)
  - activities.idx_activity_created: Unused index (0 scans)
  - activities.idx_activity_type: Unused index (0 scans)

### admin_action_logs
- **Size:** 56 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 11
  - admin_action_logs.user_id: Should be NOT NULL
  - admin_action_logs.api_key_id: Should be NOT NULL
  - admin_action_logs.render_deploy_id: Should be NOT NULL
  - admin_action_logs.vercel_deploy_id: Should be NOT NULL
  - admin_action_logs.created_at: Should be NOT NULL
  - admin_action_logs.updated_at: Should be NOT NULL
  - admin_action_logs.idx_admin_logs_action_type: Unused index (0 scans)
  - admin_action_logs.idx_admin_logs_status: Unused index (0 scans)
  - admin_action_logs.idx_admin_logs_user_id: Unused index (0 scans)
  - admin_action_logs.idx_admin_logs_started_at: Unused index (0 scans)
  - admin_action_logs.idx_admin_logs_environment: Unused index (0 scans)

### agent_executions
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 1
  - agent_executions.created_at: Missing DEFAULT CURRENT_TIMESTAMP

### agent_memory_access
- **Size:** 40 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - agent_memory_access.created_at: Should be NOT NULL
  - agent_memory_access.idx_agent_access_agent: Unused index (0 scans)
  - agent_memory_access.idx_agent_access_memory: Unused index (0 scans)
  - agent_memory_access.idx_agent_access_time: Unused index (0 scans)

### agent_registry
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - agent_registry.created_at: Should be NOT NULL
  - agent_registry.updated_at: Should be NOT NULL

### ai_agents
- **Size:** 48 kB
- **Rows:** 4
- **Dead Rows:** 37
- **Issues:** 2
  - ai_agents.created_at: Should be NOT NULL
  - ai_agents.idx_ai_agents_active: Unused index (0 scans)

### ai_logs
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - ai_logs.user_id: Should be NOT NULL
  - ai_logs.created_at: Should be NOT NULL

### ai_usage_logs
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 5
  - ai_usage_logs.request_type: Should be NOT NULL
  - ai_usage_logs.request_id: Should be NOT NULL
  - ai_usage_logs.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - ai_usage_logs.idx_ai_usage_user_created: Unused index (0 scans)
  - ai_usage_logs.idx_ai_usage_service_model: Unused index (0 scans)

### alembic_version
- **Size:** 24 kB
- **Rows:** 2
- **Dead Rows:** 13

### api_keys
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - api_keys.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - api_keys.api_keys_key_hash_key: Unused index (0 scans)

### app_users
- **Size:** 136 kB
- **Rows:** 90
- **Dead Rows:** 12
- **Issues:** 4
  - app_users.updated_at: Should be NOT NULL
  - app_users.app_users_email_key: Unused index (0 scans)
  - app_users.app_users_username_key: Unused index (0 scans)
  - app_users.idx_app_users_username: Unused index (0 scans)

### auth_tokens
- **Size:** 40 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - auth_tokens.created_at: Should be NOT NULL
  - auth_tokens.idx_auth_tokens_user: Unused index (0 scans)
  - auth_tokens.idx_auth_tokens_expires: Unused index (0 scans)
  - auth_tokens.auth_tokens_token_key: Unused index (0 scans)

### automation_actions
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - automation_actions.rule_id: Should be NOT NULL
  - automation_actions.created_at: Should be NOT NULL
  - automation_actions.idx_actions_rule: Unused index (0 scans)

### automation_executions
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - automation_executions.workflow_id: Should be NOT NULL
  - automation_executions.idx_executions_workflow: Unused index (0 scans)
  - automation_executions.idx_executions_status: Unused index (0 scans)

### automation_rules
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - automation_rules.workflow_id: Should be NOT NULL
  - automation_rules.created_at: Should be NOT NULL
  - automation_rules.updated_at: Should be NOT NULL
  - automation_rules.idx_rules_workflow: Unused index (0 scans)

### automation_templates
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - automation_templates.created_at: Should be NOT NULL
  - automation_templates.updated_at: Should be NOT NULL
  - automation_templates.idx_templates_category: Unused index (0 scans)

### automation_workflows
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - automation_workflows.created_at: Should be NOT NULL
  - automation_workflows.updated_at: Should be NOT NULL
  - automation_workflows.idx_workflows_active: Unused index (0 scans)

### blog_posts
- **Size:** 48 kB
- **Rows:** 3
- **Dead Rows:** 4
- **Issues:** 1
  - blog_posts.created_at: Should be NOT NULL

### businesses
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 5
  - businesses.tax_id: Should be NOT NULL
  - businesses.created_at: Should be NOT NULL
  - businesses.updated_at: Should be NOT NULL
  - businesses.idx_businesses_name: Unused index (0 scans)
  - businesses.idx_businesses_active: Unused index (0 scans)

### campaigns
- **Size:** 40 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 7
  - campaigns.created_at: Should be NOT NULL
  - campaigns.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - campaigns.updated_at: Should be NOT NULL
  - campaigns.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - campaigns.idx_campaign_dates: Unused index (0 scans)
  - campaigns.idx_campaign_status: Unused index (0 scans)
  - campaigns.idx_campaign_type: Unused index (0 scans)

### communications
- **Size:** 96 kB
- **Rows:** 0
- **Dead Rows:** 1
- **Issues:** 8
  - communications.created_at: Should be NOT NULL
  - communications.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - communications.updated_at: Should be NOT NULL
  - communications.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - communications.idx_communication_user: Unused index (0 scans)
  - communications.idx_communication_scheduled: Unused index (0 scans)
  - communications.idx_communication_entity: Unused index (0 scans)
  - communications.idx_communication_type: Unused index (0 scans)

### contacts
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - contacts.user_id: Should be NOT NULL
  - contacts.created_at: Should be NOT NULL

### cross_ai_memory
- **Size:** 1688 kB
- **Rows:** 1
- **Dead Rows:** 0
- **Issues:** 6
  - cross_ai_memory.created_at: Should be NOT NULL
  - cross_ai_memory.updated_at: Should be NOT NULL
  - cross_ai_memory.idx_cross_ai_source: Unused index (0 scans)
  - cross_ai_memory.idx_cross_ai_key: Unused index (0 scans)
  - cross_ai_memory.idx_cross_ai_type: Unused index (0 scans)
  - cross_ai_memory.idx_cross_ai_embedding: Unused index (0 scans)

### customer_segments
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - customer_segments.created_at: Should be NOT NULL
  - customer_segments.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - customer_segments.updated_at: Should be NOT NULL
  - customer_segments.updated_at: Missing DEFAULT CURRENT_TIMESTAMP

### customers
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 6
  - customers.created_at: Should be NOT NULL
  - customers.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - customers.updated_at: Should be NOT NULL
  - customers.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - customers.idx_customer_active: Unused index (0 scans)
  - customers.idx_customer_email: Unused index (0 scans)

### dashboard_insights
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - dashboard_insights.user_id: Should be NOT NULL
  - dashboard_insights.created_at: Should be NOT NULL

### database_health_checks
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - database_health_checks.created_at: Should be NOT NULL
  - database_health_checks.idx_health_checks_timestamp: Unused index (0 scans)
  - database_health_checks.idx_health_checks_healthy: Unused index (0 scans)

### deployment_records
- **Size:** 40 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 6
  - deployment_records.service_id: Should be NOT NULL
  - deployment_records.previous_deployment_id: Should be NOT NULL
  - deployment_records.created_at: Should be NOT NULL
  - deployment_records.idx_deployments_service: Unused index (0 scans)
  - deployment_records.idx_deployments_status: Unused index (0 scans)
  - deployment_records.idx_deployments_deployed_at: Unused index (0 scans)

### digital_deliveries
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - digital_deliveries.order_id: Should be NOT NULL
  - digital_deliveries.created_at: Should be NOT NULL

### document_chunks
- **Size:** 1632 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - document_chunks.created_at: Should be NOT NULL
  - document_chunks.idx_chunks_document: Unused index (0 scans)
  - document_chunks.idx_chunks_embedding: Unused index (0 scans)

### document_templates
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 5
  - document_templates.template_type: Should be NOT NULL
  - document_templates.document_type: Should be NOT NULL
  - document_templates.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - document_templates.updated_at: Should be NOT NULL
  - document_templates.updated_at: Missing DEFAULT CURRENT_TIMESTAMP

### documents
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 1
  - documents.created_at: Should be NOT NULL

### embedding_models
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - embedding_models.created_at: Should be NOT NULL
  - embedding_models.embedding_models_name_key: Unused index (0 scans)

### embeddings
- **Size:** 1632 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - embeddings.model_id: Should be NOT NULL
  - embeddings.created_at: Should be NOT NULL
  - embeddings.idx_embeddings_source: Unused index (0 scans)
  - embeddings.idx_embeddings_vector: Unused index (0 scans)

### estimate_records
- **Size:** 1640 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 5
  - estimate_records.created_at: Should be NOT NULL
  - estimate_records.updated_at: Should be NOT NULL
  - estimate_records.idx_estimates_project: Unused index (0 scans)
  - estimate_records.idx_estimates_status: Unused index (0 scans)
  - estimate_records.idx_estimates_embedding: Unused index (0 scans)

### estimates
- **Size:** 48 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 11
  - estimates.inspection_id: Should be NOT NULL
  - estimates.project_id: Should be NOT NULL
  - estimates.created_at: Should be NOT NULL
  - estimates.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - estimates.updated_at: Should be NOT NULL
  - estimates.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - estimates.converted_to_invoice_id: Should be NOT NULL
  - estimates.estimates_estimate_number_key: Unused index (0 scans)
  - estimates.ix_estimates_estimate_number: Unused index (0 scans)
  - estimates.idx_estimate_status: Unused index (0 scans)
  - estimates.idx_estimate_customer: Unused index (0 scans)

### expenses
- **Size:** 56 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 14
  - expenses.job_id: Should be NOT NULL
  - expenses.vendor_id: Should be NOT NULL
  - expenses.employee_id: Should be NOT NULL
  - expenses.invoice_id: Should be NOT NULL
  - expenses.quickbooks_expense_id: Should be NOT NULL
  - expenses.created_at: Should be NOT NULL
  - expenses.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - expenses.updated_at: Should be NOT NULL
  - expenses.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - expenses.idx_expense_date: Unused index (0 scans)
  - expenses.ix_expenses_expense_number: Unused index (0 scans)
  - expenses.idx_expense_category: Unused index (0 scans)
  - expenses.idx_expense_job: Unused index (0 scans)
  - expenses.idx_expense_billable: Unused index (0 scans)

### inspection_photos
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0

### inspections
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - inspections.project_id: Should be NOT NULL
  - inspections.roof_type: Should be NOT NULL
  - inspections.created_at: Missing DEFAULT CURRENT_TIMESTAMP

### integration_configs
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - integration_configs.integration_id: Should be NOT NULL
  - integration_configs.created_at: Should be NOT NULL
  - integration_configs.updated_at: Should be NOT NULL
  - integration_configs.idx_integration_configs: Unused index (0 scans)

### integrations
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 1
  - integrations.created_at: Missing DEFAULT CURRENT_TIMESTAMP

### inventory_items
- **Size:** 40 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 6
  - inventory_items.business_id: Should be NOT NULL
  - inventory_items.created_at: Should be NOT NULL
  - inventory_items.updated_at: Should be NOT NULL
  - inventory_items.idx_inventory_sku: Unused index (0 scans)
  - inventory_items.idx_inventory_business: Unused index (0 scans)
  - inventory_items.inventory_items_sku_key: Unused index (0 scans)

### invoices
- **Size:** 56 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 13
  - invoices.estimate_id: Should be NOT NULL
  - invoices.job_id: Should be NOT NULL
  - invoices.stripe_invoice_id: Should be NOT NULL
  - invoices.quickbooks_invoice_id: Should be NOT NULL
  - invoices.created_at: Should be NOT NULL
  - invoices.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - invoices.updated_at: Should be NOT NULL
  - invoices.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - invoices.idx_invoice_customer: Unused index (0 scans)
  - invoices.ix_invoices_invoice_number: Unused index (0 scans)
  - invoices.idx_invoice_due_date: Unused index (0 scans)
  - invoices.idx_invoice_date: Unused index (0 scans)
  - invoices.idx_invoice_status: Unused index (0 scans)

### jobs
- **Size:** 48 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 10
  - jobs.estimate_id: Should be NOT NULL
  - jobs.invoice_id: Should be NOT NULL
  - jobs.created_at: Should be NOT NULL
  - jobs.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - jobs.updated_at: Should be NOT NULL
  - jobs.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - jobs.idx_job_dates: Unused index (0 scans)
  - jobs.idx_job_customer: Unused index (0 scans)
  - jobs.idx_job_status: Unused index (0 scans)
  - jobs.ix_jobs_job_number: Unused index (0 scans)

### knowledge_entries
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - knowledge_entries.created_at: Should be NOT NULL
  - knowledge_entries.updated_at: Should be NOT NULL
  - knowledge_entries.idx_knowledge_category: Unused index (0 scans)
  - knowledge_entries.idx_knowledge_validated: Unused index (0 scans)

### lead_sources
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 6
  - lead_sources.created_at: Should be NOT NULL
  - lead_sources.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - lead_sources.updated_at: Should be NOT NULL
  - lead_sources.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - lead_sources.lead_sources_name_key: Unused index (0 scans)
  - lead_sources.idx_lead_source_category: Unused index (0 scans)

### leads
- **Size:** 112 kB
- **Rows:** 0
- **Dead Rows:** 5
- **Issues:** 11
  - leads.campaign_id: Should be NOT NULL
  - leads.converted_to_opportunity_id: Should be NOT NULL
  - leads.created_at: Should be NOT NULL
  - leads.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - leads.updated_at: Should be NOT NULL
  - leads.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - leads.leads_email_key: Unused index (0 scans)
  - leads.idx_lead_assigned: Unused index (0 scans)
  - leads.idx_lead_status: Unused index (0 scans)
  - leads.idx_lead_score: Unused index (0 scans)
  - leads.idx_lead_source: Unused index (0 scans)

### memories
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 7
- **Issues:** 4
  - memories.memory_type: Should be NOT NULL
  - memories.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - memories.updated_at: Should be NOT NULL
  - memories.updated_at: Missing DEFAULT CURRENT_TIMESTAMP

### memory_access_log
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0

### memory_collections
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 5
  - memory_collections.collection_type: Should be NOT NULL
  - memory_collections.created_at: Should be NOT NULL
  - memory_collections.updated_at: Should be NOT NULL
  - memory_collections.idx_collections_owner: Unused index (0 scans)
  - memory_collections.idx_collections_type: Unused index (0 scans)

### memory_contexts
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 6
  - memory_contexts.context_type: Should be NOT NULL
  - memory_contexts.parent_context_id: Should be NOT NULL
  - memory_contexts.created_at: Should be NOT NULL
  - memory_contexts.updated_at: Should be NOT NULL
  - memory_contexts.idx_contexts_parent: Unused index (0 scans)
  - memory_contexts.idx_contexts_type: Unused index (0 scans)

### memory_entries
- **Size:** 58 MB
- **Rows:** 31,247
- **Dead Rows:** 5
- **Issues:** 13
  - memory_entries.user_id: Should be NOT NULL
  - memory_entries.session_id: Should be NOT NULL
  - memory_entries.updated_at: Should be NOT NULL
  - memory_entries.is_active: VARCHAR without length limit
  - memory_entries.idx_session_id: Unused index (0 scans)
  - memory_entries.idx_importance: Unused index (0 scans)
  - memory_entries.ix_memory_entries_user_id: Unused index (0 scans)
  - memory_entries.ix_memory_entries_session_id: Unused index (0 scans)
  - memory_entries.ix_memory_entries_memory_type: Unused index (0 scans)
  - memory_entries.idx_memory_owner: Unused index (0 scans)
  - memory_entries.idx_memory_entries_category: Unused index (0 scans)
  - memory_entries.idx_memory_entries_accessed: Unused index (0 scans)
  - memory_entries.idx_memory_accessed: Unused index (0 scans)

### memory_metadata
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - memory_metadata.created_at: Should be NOT NULL
  - memory_metadata.updated_at: Should be NOT NULL
  - memory_metadata.idx_memory_meta_memory: Unused index (0 scans)
  - memory_metadata.idx_memory_meta_key: Unused index (0 scans)

### memory_records
- **Size:** 1664 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 8
  - memory_records.created_at: Should be NOT NULL
  - memory_records.parent_id: Should be NOT NULL
  - memory_records.updated_at: Should be NOT NULL
  - memory_records.idx_memory_type: Unused index (0 scans)
  - memory_records.idx_memory_category: Unused index (0 scans)
  - memory_records.idx_memory_tags: Unused index (0 scans)
  - memory_records.idx_memory_created: Unused index (0 scans)
  - memory_records.idx_memory_embedding: Unused index (0 scans)

### memory_sync
- **Size:** 74 MB
- **Rows:** 69,548
- **Dead Rows:** 0
- **Issues:** 3
  - memory_sync.sync_type: Should be NOT NULL
  - memory_sync.idx_memory_sync_initiated_at: Unused index (0 scans)
  - memory_sync.idx_sync_time: Unused index (0 scans)

### multimodal_content
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - multimodal_content.mime_type: Should be NOT NULL
  - multimodal_content.created_at: Should be NOT NULL

### notifications
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - notifications.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - notifications.idx_notification_user_unread: Unused index (0 scans)

### opportunities
- **Size:** 96 kB
- **Rows:** 0
- **Dead Rows:** 1
- **Issues:** 8
  - opportunities.lead_id: Should be NOT NULL
  - opportunities.created_at: Should be NOT NULL
  - opportunities.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - opportunities.updated_at: Should be NOT NULL
  - opportunities.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - opportunities.idx_opportunity_customer: Unused index (0 scans)
  - opportunities.idx_opportunity_stage: Unused index (0 scans)
  - opportunities.idx_opportunity_assigned: Unused index (0 scans)

### orders
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - orders.user_id: Should be NOT NULL
  - orders.product_id: Should be NOT NULL
  - orders.stripe_session_id: Should be NOT NULL
  - orders.created_at: Should be NOT NULL

### payments
- **Size:** 56 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 11
  - payments.stripe_payment_id: Should be NOT NULL
  - payments.quickbooks_payment_id: Should be NOT NULL
  - payments.created_at: Should be NOT NULL
  - payments.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - payments.updated_at: Should be NOT NULL
  - payments.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - payments.idx_payment_customer: Unused index (0 scans)
  - payments.idx_payment_date: Unused index (0 scans)
  - payments.idx_payment_status: Unused index (0 scans)
  - payments.idx_payment_invoice: Unused index (0 scans)
  - payments.ix_payments_payment_number: Unused index (0 scans)

### production_memory_embeddings
- **Size:** 1632 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - production_memory_embeddings.created_at: Should be NOT NULL
  - production_memory_embeddings.idx_prod_embed_memory: Unused index (0 scans)
  - production_memory_embeddings.idx_prod_embed_vector: Unused index (0 scans)

### production_memory_entries
- **Size:** 64 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 10
  - production_memory_entries.context_id: Should be NOT NULL
  - production_memory_entries.compression_type: Should be NOT NULL
  - production_memory_entries.previous_version_id: Should be NOT NULL
  - production_memory_entries.created_at: Should be NOT NULL
  - production_memory_entries.updated_at: Should be NOT NULL
  - production_memory_entries.idx_prod_memory_owner: Unused index (0 scans)
  - production_memory_entries.idx_prod_memory_key: Unused index (0 scans)
  - production_memory_entries.idx_prod_memory_type: Unused index (0 scans)
  - production_memory_entries.idx_prod_memory_tags: Unused index (0 scans)
  - production_memory_entries.unique_production_memory_key: Unused index (0 scans)

### production_memory_metadata
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 5
  - production_memory_metadata.metadata_type: Should be NOT NULL
  - production_memory_metadata.created_at: Should be NOT NULL
  - production_memory_metadata.updated_at: Should be NOT NULL
  - production_memory_metadata.idx_prod_meta_memory: Unused index (0 scans)
  - production_memory_metadata.idx_prod_meta_key: Unused index (0 scans)

### production_memory_sync
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - production_memory_sync.created_at: Should be NOT NULL
  - production_memory_sync.idx_prod_sync_memory: Unused index (0 scans)
  - production_memory_sync.idx_prod_sync_status: Unused index (0 scans)

### products
- **Size:** 32 kB
- **Rows:** 14
- **Dead Rows:** 3
- **Issues:** 1
  - products.created_at: Should be NOT NULL

### project_members
- **Size:** 0 bytes
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - project_members.project_id: Should be NOT NULL
  - project_members.user_id: Should be NOT NULL
  - project_members: Missing PRIMARY KEY

### project_tasks
- **Size:** 64 kB
- **Rows:** 3
- **Dead Rows:** 0
- **Issues:** 5
  - project_tasks.assignee_id: Should be NOT NULL
  - project_tasks.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - project_tasks.updated_at: Should be NOT NULL
  - project_tasks.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - project_tasks.idx_task_assignee: Unused index (0 scans)

### projects
- **Size:** 64 kB
- **Rows:** 1
- **Dead Rows:** 17
- **Issues:** 6
  - projects.project_type: Should be NOT NULL
  - projects.team_id: Should be NOT NULL
  - projects.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - projects.updated_at: Should be NOT NULL
  - projects.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - projects.idx_project_owner_status: Unused index (0 scans)

### purchases
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - purchases.transaction_id: Should be NOT NULL
  - purchases.payment_id: Should be NOT NULL
  - purchases.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - purchases.purchases_license_key_key: Unused index (0 scans)

### retrieval_sessions
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - retrieval_sessions.user_id: Should be NOT NULL
  - retrieval_sessions.task_id: Should be NOT NULL
  - retrieval_sessions.created_at: Should be NOT NULL

### reviews
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 5
  - reviews.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - reviews.updated_at: Should be NOT NULL
  - reviews.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - reviews.idx_review_rating: Unused index (0 scans)
  - reviews.idx_review_product: Unused index (0 scans)

### sales_goals
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 8
  - sales_goals.user_id: Should be NOT NULL
  - sales_goals.team_id: Should be NOT NULL
  - sales_goals.created_at: Should be NOT NULL
  - sales_goals.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - sales_goals.updated_at: Should be NOT NULL
  - sales_goals.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - sales_goals.idx_sales_goal_user: Unused index (0 scans)
  - sales_goals.idx_sales_goal_period: Unused index (0 scans)

### security_events
- **Size:** 96 kB
- **Rows:** 7
- **Dead Rows:** 0
- **Issues:** 6
  - security_events.user_id: Should be NOT NULL
  - security_events.created_at: Should be NOT NULL
  - security_events.idx_security_events_created_at: Unused index (0 scans)
  - security_events.idx_security_events_event_type: Unused index (0 scans)
  - security_events.idx_security_events_user_id: Unused index (0 scans)
  - security_events.idx_security_events_ip_address: Unused index (0 scans)

### spatial_ref_sys
- **Size:** 7144 kB
- **Rows:** 8,500
- **Dead Rows:** 0

### subscriptions
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 5
  - subscriptions.stripe_customer_id: Should be NOT NULL
  - subscriptions.stripe_subscription_id: Should be NOT NULL
  - subscriptions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - subscriptions.updated_at: Should be NOT NULL
  - subscriptions.updated_at: Missing DEFAULT CURRENT_TIMESTAMP

### summarizations
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - summarizations.created_at: Should be NOT NULL
  - summarizations.idx_summaries_source: Unused index (0 scans)

### system_config
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - system_config.config_type: Should be NOT NULL
  - system_config.updated_at: Should be NOT NULL
  - system_config.updated_at: Missing DEFAULT CURRENT_TIMESTAMP

### system_secrets
- **Size:** 48 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 6
  - system_secrets.created_at: Should be NOT NULL
  - system_secrets.updated_at: Should be NOT NULL
  - system_secrets.system_secrets_secret_name_key: Unused index (0 scans)
  - system_secrets.idx_secrets_name: Unused index (0 scans)
  - system_secrets.idx_secrets_service: Unused index (0 scans)
  - system_secrets.idx_secrets_active: Unused index (0 scans)

### task_comments
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - task_comments.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - task_comments.updated_at: Should be NOT NULL
  - task_comments.updated_at: Missing DEFAULT CURRENT_TIMESTAMP

### task_dependencies
- **Size:** 8192 bytes
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - task_dependencies.dependency_type: Should be NOT NULL
  - task_dependencies.created_at: Should be NOT NULL
  - task_dependencies.created_at: Missing DEFAULT CURRENT_TIMESTAMP

### task_executions
- **Size:** 40 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - task_executions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - task_executions.ix_task_executions_task_id: Unused index (0 scans)
  - task_executions.idx_created_at: Unused index (0 scans)
  - task_executions.idx_task_status: Unused index (0 scans)

### tasks
- **Size:** 40 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 7
  - tasks.related_to_type: Should be NOT NULL
  - tasks.related_to_id: Should be NOT NULL
  - tasks.created_at: Should be NOT NULL
  - tasks.updated_at: Should be NOT NULL
  - tasks.idx_tasks_assigned: Unused index (0 scans)
  - tasks.idx_tasks_related: Unused index (0 scans)
  - tasks.idx_tasks_status: Unused index (0 scans)

### team_members
- **Size:** 0 bytes
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - team_members.team_id: Should be NOT NULL
  - team_members.user_id: Should be NOT NULL
  - team_members: Missing PRIMARY KEY

### teams
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - teams.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - teams.updated_at: Should be NOT NULL
  - teams.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - teams.ix_teams_slug: Unused index (0 scans)

### user_sessions
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 2
  - user_sessions.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - user_sessions.user_sessions_refresh_token_hash_key: Unused index (0 scans)

### users
- **Size:** 48 kB
- **Rows:** 4
- **Dead Rows:** 7
- **Issues:** 2
  - users.created_at: Should be NOT NULL
  - users.created_at: Should be NOT NULL

### vector_memories
- **Size:** 1632 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 4
  - vector_memories.collection_id: Should be NOT NULL
  - vector_memories.created_at: Should be NOT NULL
  - vector_memories.idx_vector_collection: Unused index (0 scans)
  - vector_memories.idx_vector_embedding: Unused index (0 scans)

### vendors
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 7
  - vendors.tax_id: Should be NOT NULL
  - vendors.created_at: Should be NOT NULL
  - vendors.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - vendors.updated_at: Should be NOT NULL
  - vendors.updated_at: Missing DEFAULT CURRENT_TIMESTAMP
  - vendors.idx_vendor_active: Unused index (0 scans)
  - vendors.idx_vendor_name: Unused index (0 scans)

### webhook_events
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - webhook_events.task_execution_id: Should be NOT NULL
  - webhook_events.ix_webhook_events_processed: Unused index (0 scans)
  - webhook_events.ix_webhook_events_source: Unused index (0 scans)

### webhooks
- **Size:** 24 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 3
  - webhooks.created_at: Should be NOT NULL
  - webhooks.updated_at: Should be NOT NULL
  - webhooks.idx_webhooks_active: Unused index (0 scans)

### workflow_runs
- **Size:** 16 kB
- **Rows:** 0
- **Dead Rows:** 0
- **Issues:** 1
  - workflow_runs.parent_run_id: Should be NOT NULL

### workflows
- **Size:** 32 kB
- **Rows:** 0
- **Dead Rows:** 2
- **Issues:** 4
  - workflows.team_id: Should be NOT NULL
  - workflows.created_at: Missing DEFAULT CURRENT_TIMESTAMP
  - workflows.updated_at: Should be NOT NULL
  - workflows.updated_at: Missing DEFAULT CURRENT_TIMESTAMP

## Recommendations

1. **Immediate Actions:**
   - Run `schema_fixes_migration.sql` to fix all critical and major issues
   - Enable Row Level Security on all user-facing tables
   - Add missing indexes on foreign key columns

2. **Best Practices:**
   - Always use UUID for ID columns in new tables
   - Add `created_at` and `updated_at` timestamps to all tables
   - Use TEXT instead of VARCHAR without length
   - Create indexes on all foreign key columns
   - Enable RLS and create appropriate policies

3. **Performance Optimization:**
   - Review and drop unused indexes
   - Consider partitioning large tables
   - Add indexes for common query patterns
   - Regular VACUUM and ANALYZE

