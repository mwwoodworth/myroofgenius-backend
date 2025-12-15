-- MASTER ENVIRONMENT VARIABLE TRACKING SYSTEM
-- Store all environment variables and configurations in database

CREATE TABLE IF NOT EXISTS env_master (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    service VARCHAR(100) NOT NULL, -- 'render', 'vercel', 'supabase'
    category VARCHAR(100), -- 'api_keys', 'database', 'features', 'revenue'
    is_secret BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    last_verified TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert known environment variables
INSERT INTO env_master (key, value, service, category, is_secret, description, last_verified) VALUES
-- Stripe (YOU SAID THESE ARE ALREADY IN RENDER!)
('STRIPE_SECRET_KEY', 'CONFIGURED_IN_RENDER', 'render', 'api_keys', true, 
 'Live Stripe secret key - ALREADY SET IN RENDER FOR A WEEK+', CURRENT_TIMESTAMP),
('STRIPE_PUBLISHABLE_KEY', 'CONFIGURED_IN_RENDER', 'render', 'api_keys', false,
 'Live Stripe publishable key - ALREADY SET IN RENDER', CURRENT_TIMESTAMP),
('STRIPE_WEBHOOK_SECRET', 'CONFIGURED_IN_RENDER', 'render', 'api_keys', true,
 'Stripe webhook secret - CHECK RENDER', CURRENT_TIMESTAMP),

-- Database
('DATABASE_URL', 'postgresql://postgres:<DB_PASSWORD_REDACTED>@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres', 
 'render', 'database', true, 'Primary database connection', CURRENT_TIMESTAMP),

-- CenterPoint Integration
('CENTERPOINT_API_KEY', 'NEEDS_CONFIGURATION', 'render', 'api_keys', true,
 'CenterPoint CRM API key for ETL', NULL),
('CENTERPOINT_SYNC_ENABLED', 'true', 'render', 'features', false,
 'Enable CenterPoint data synchronization', CURRENT_TIMESTAMP),

-- SendGrid
('SENDGRID_API_KEY', 'NEEDS_CONFIGURATION', 'render', 'api_keys', true,
 'SendGrid for email automation', NULL),
('SENDGRID_FROM_EMAIL', 'matthew@brainstackstudio.com', 'render', 'api_keys', false,
 'From email address', CURRENT_TIMESTAMP),

-- Google Ads
('GOOGLE_ADS_DEVELOPER_TOKEN', 'NEEDS_CONFIGURATION', 'render', 'api_keys', true,
 'Google Ads API developer token', NULL),

-- System Features
('REVENUE_AUTOMATION_ENABLED', 'true', 'render', 'features', false,
 'Enable automated revenue generation', CURRENT_TIMESTAMP),
('LANGGRAPH_ENABLED', 'true', 'render', 'features', false,
 'Enable LangGraph orchestration', CURRENT_TIMESTAMP),
('AI_CAPABILITIES_ENABLED', 'true', 'render', 'features', false,
 'Enable full AI capabilities', CURRENT_TIMESTAMP),

-- Render Deployment
('RENDER_API_KEY', 'rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx', 'local', 'api_keys', true,
 'Render API for deployments', CURRENT_TIMESTAMP),
('RENDER_SERVICE_ID', 'srv-d1tfs4idbo4c73di6k00', 'local', 'api_keys', false,
 'Render service ID', CURRENT_TIMESTAMP),

-- Docker
('DOCKER_USERNAME', 'mwwoodworth', 'local', 'api_keys', false,
 'Docker Hub username', CURRENT_TIMESTAMP),
('DOCKER_PAT', 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho', 'local', 'api_keys', true,
 'Docker Hub access token', CURRENT_TIMESTAMP)

ON CONFLICT (key) DO UPDATE 
SET value = EXCLUDED.value,
    updated_at = CURRENT_TIMESTAMP;

-- Create function to get env var
CREATE OR REPLACE FUNCTION get_env_var(var_key VARCHAR)
RETURNS TEXT AS $$
BEGIN
    RETURN (SELECT value FROM env_master WHERE key = var_key AND is_active = TRUE LIMIT 1);
END;
$$ LANGUAGE plpgsql;

-- Create view for quick status check
CREATE OR REPLACE VIEW env_status AS
SELECT 
    category,
    COUNT(*) as total_vars,
    COUNT(CASE WHEN value NOT LIKE '%NEEDS%' THEN 1 END) as configured,
    COUNT(CASE WHEN value LIKE '%NEEDS%' THEN 1 END) as needs_config,
    COUNT(CASE WHEN last_verified > CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as recently_verified
FROM env_master
WHERE is_active = TRUE
GROUP BY category;

-- Check what needs configuration
SELECT 
    'ENVIRONMENT VARIABLE STATUS' as report,
    CURRENT_TIMESTAMP as checked_at;

SELECT * FROM env_status;

SELECT 
    key,
    CASE 
        WHEN value LIKE '%CONFIGURED_IN_RENDER%' THEN '✅ Already in Render'
        WHEN value LIKE '%NEEDS%' THEN '❌ Needs Configuration'
        ELSE '✅ Configured'
    END as status,
    description
FROM env_master
WHERE is_active = TRUE
ORDER BY 
    CASE WHEN value LIKE '%NEEDS%' THEN 0 ELSE 1 END,
    category, key;