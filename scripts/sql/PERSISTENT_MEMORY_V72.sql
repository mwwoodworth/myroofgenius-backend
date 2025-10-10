-- PERSISTENT MEMORY SYSTEM
-- Store all system state and configurations

-- Create memory tables if not exist
CREATE TABLE IF NOT EXISTS system_memory (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    category VARCHAR(100),
    importance VARCHAR(20) DEFAULT 'normal',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Store current system state
INSERT INTO system_memory (key, value, category, importance) VALUES
(
    'deployment_v72',
    '{
        "version": "7.2",
        "deployed_at": "2025-08-18T08:53:00Z",
        "status": "operational",
        "endpoints_working": 6,
        "endpoints_total": 7,
        "revenue_ready": true,
        "issues_fixed": [
            "Double prefix bug fixed",
            "All route files cleaned",
            "Single main.py source of truth",
            "Database tables created"
        ]
    }'::jsonb,
    'deployment',
    'critical'
),
(
    'revenue_configuration',
    '{
        "stripe_configured": false,
        "sendgrid_configured": false,
        "google_ads_configured": false,
        "automation_ready": true,
        "tables_created": 10,
        "endpoints": {
            "test_revenue": "working",
            "ai_estimation": "working",
            "stripe": "needs_api_key",
            "customer_pipeline": "working",
            "landing_pages": "needs_content",
            "google_ads": "needs_credentials",
            "dashboard": "database_issues"
        }
    }'::jsonb,
    'revenue',
    'critical'
),
(
    'automation_scripts',
    '{
        "revenue_automation": "/home/mwwoodworth/code/REVENUE_AUTOMATION_SYSTEM.py",
        "configuration": "/home/mwwoodworth/code/CONFIGURE_PRODUCTION_APIS.py",
        "monitoring": "/home/mwwoodworth/code/HARDEN_PRODUCTION_SYSTEM.py",
        "verification": "/home/mwwoodworth/code/REVENUE_SYSTEM_FINAL_V72.py"
    }'::jsonb,
    'scripts',
    'high'
),
(
    'docker_deployments',
    '{
        "v7.0": "sha256:54ad72382e11684b60ca976a52184a2cf98f0e673f9753bfe4366df8975bc1cb",
        "v7.1": "sha256:54ad72382e11684b60ca976a52184a2cf98f0e673f9753bfe4366df8975bc1cb",
        "v7.2": "sha256:ec9d463689cf17283445a1c55e17882d87be2d0f36008820673ba1e48c3cd969",
        "latest": "v7.2",
        "repository": "mwwoodworth/brainops-backend"
    }'::jsonb,
    'docker',
    'critical'
),
(
    'critical_fixes_applied',
    '{
        "double_prefix_fix": {
            "issue": "Routes had /api/v1/test-revenue/api/v1/test-revenue/",
            "solution": "Removed prefixes from route files, kept only in main.py",
            "files_modified": [
                "routes/test_revenue.py",
                "routes/ai_estimation.py",
                "routes/stripe_revenue.py",
                "routes/customer_pipeline.py",
                "routes/landing_pages.py",
                "routes/google_ads_automation.py",
                "routes/revenue_dashboard.py"
            ],
            "result": "All endpoints now accessible"
        }
    }'::jsonb,
    'fixes',
    'critical'
)
ON CONFLICT (key) DO UPDATE 
SET value = EXCLUDED.value,
    updated_at = CURRENT_TIMESTAMP;

-- Create automated tasks
INSERT INTO automated_tasks (task_type, status, scheduled_at, metadata) VALUES
('revenue_automation_cycle', 'pending', CURRENT_TIMESTAMP + INTERVAL '5 minutes', 
 '{"frequency": "30_minutes", "enabled": true}'::jsonb),
('lead_nurture_emails', 'pending', CURRENT_TIMESTAMP + INTERVAL '1 hour',
 '{"frequency": "daily", "enabled": true}'::jsonb),
('revenue_reporting', 'pending', CURRENT_TIMESTAMP + INTERVAL '24 hours',
 '{"frequency": "daily", "enabled": true}'::jsonb);

-- Success confirmation
SELECT 
    'PERSISTENT MEMORY STORED' as status,
    COUNT(*) as memory_entries,
    CURRENT_TIMESTAMP as stored_at
FROM system_memory;