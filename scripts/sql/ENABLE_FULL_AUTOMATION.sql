-- ENABLE ALL AUTOMATIONS AND AI DECISION LOGGING

-- Create automations if they don't exist
INSERT INTO automations (name, description, type, trigger, actions, config, enabled, created_at, updated_at)
VALUES
  ('Health Check Monitor', 'Monitor system health every 5 minutes', 'monitoring', 
   '{"type": "schedule", "cron": "*/5 * * * *"}'::jsonb, 
   '["check_health", "auto_restart", "alert_on_failure"]'::jsonb, 
   '{"active": true, "auto_heal": true, "max_retries": 3}'::jsonb, 
   true, NOW(), NOW()),
   
  ('Self-Healing System', 'Automatically fix common issues', 'maintenance', 
   '{"type": "event", "on": ["error", "timeout", "failure"]}'::jsonb, 
   '["diagnose_issue", "apply_fix", "verify_fix", "log_action"]'::jsonb, 
   '{"active": true, "autonomous": true}'::jsonb, 
   true, NOW(), NOW()),
   
  ('Data Sync Monitor', 'Ensure CenterPoint sync is running', 'integration', 
   '{"type": "schedule", "cron": "*/30 * * * *"}'::jsonb, 
   '["check_sync_status", "restart_if_needed", "log_metrics"]'::jsonb, 
   '{"active": true, "critical": true}'::jsonb, 
   true, NOW(), NOW()),
   
  ('AI Decision Logger', 'Log all AI agent decisions', 'logging', 
   '{"type": "event", "on": "ai_decision"}'::jsonb, 
   '["capture_decision", "store_in_db", "analyze_pattern"]'::jsonb, 
   '{"active": true, "learning_enabled": true}'::jsonb, 
   true, NOW(), NOW()),
   
  ('Revenue Optimization', 'Optimize pricing and conversions', 'revenue', 
   '{"type": "continuous", "analyze_interval": "1h"}'::jsonb, 
   '["analyze_metrics", "adjust_pricing", "test_variations", "report_results"]'::jsonb, 
   '{"active": true, "auto_optimize": true}'::jsonb, 
   true, NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET 
  enabled = true,
  config = EXCLUDED.config,
  updated_at = NOW();

-- Configure all AI agents to log decisions
UPDATE ai_agents SET
  capabilities = COALESCE(capabilities, '{}'::jsonb) || 
    '{"decision_logging": true, "auto_learn": true, "self_improve": true}'::jsonb,
  config = COALESCE(config, '{}'::jsonb) || 
    '{"log_all_decisions": true, "store_context": true, "learn_from_outcomes": true}'::jsonb,
  status = 'active',
  updated_at = NOW()
WHERE name IN (
  'AUREA Executive AI',
  'Revenue Optimization Agent',
  'Customer Success Agent',
  'Operations Agent',
  'Analytics Agent',
  'Security Agent',
  'Integration Agent'
);

-- Create AI decision log entries for testing
INSERT INTO ai_decision_logs (
  agent_id, 
  decision_type, 
  context, 
  decision, 
  confidence_score, 
  outcome,
  created_at
)
SELECT 
  id as agent_id,
  'initialization' as decision_type,
  '{"action": "startup", "mode": "autonomous"}'::jsonb as context,
  '{"action": "activate", "logging": "enabled"}'::jsonb as decision,
  0.95 as confidence_score,
  'success' as outcome,
  NOW() as created_at
FROM ai_agents
WHERE status = 'active';

-- Store automation status in persistent memory
INSERT INTO copilot_messages (
  title, content, memory_type, role, is_pinned, tags, meta_data, is_active, created_at, updated_at
) VALUES (
  'AUTOMATION SYSTEM STATUS',
  E'# AUTOMATION SYSTEM ACTIVATED\n\n## Active Automations:\n1. Health Check Monitor - Every 5 minutes\n2. Self-Healing System - Event-driven\n3. Data Sync Monitor - Every 30 minutes\n4. AI Decision Logger - Continuous\n5. Revenue Optimization - Hourly analysis\n\n## AI Agents Configured:\nAll 7 agents now logging decisions to database\n\n## Status: FULLY OPERATIONAL',
  'automation_status',
  'system',
  true,
  '{automation,status,operational}',
  '{"enabled": true, "timestamp": "' || NOW()::text || '"}'::jsonb,
  true,
  NOW(),
  NOW()
) ON CONFLICT (title) DO UPDATE SET
  content = EXCLUDED.content,
  meta_data = EXCLUDED.meta_data,
  updated_at = NOW();

-- Summary report
SELECT 
  'Automation Status Report' as report,
  (SELECT COUNT(*) FROM automations WHERE enabled = true) as active_automations,
  (SELECT COUNT(*) FROM ai_agents WHERE status = 'active') as active_agents,
  (SELECT COUNT(*) FROM ai_decision_logs WHERE created_at > NOW() - INTERVAL '1 hour') as recent_decisions,
  NOW() as timestamp;
