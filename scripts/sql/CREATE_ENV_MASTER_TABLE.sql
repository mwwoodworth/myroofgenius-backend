-- MASTER ENVIRONMENT VARIABLES TABLE FOR ALL APPLICATIONS
-- Single source of truth for all configuration

-- Drop existing table if exists
DROP TABLE IF EXISTS env_master CASCADE;

-- Create the master environment variables table
CREATE TABLE env_master (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100), -- API_KEYS, DATABASE, SERVICES, etc.
    project VARCHAR(100), -- backend, frontend, all, specific app
    environment VARCHAR(50) DEFAULT 'production', -- production, staging, development
    is_sensitive BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    last_rotated TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255) DEFAULT 'system',
    metadata JSONB DEFAULT '{}',
    UNIQUE(key, project, environment)
);

-- Create indexes for fast lookups
CREATE INDEX idx_env_master_key ON env_master(key);
CREATE INDEX idx_env_master_project ON env_master(project);
CREATE INDEX idx_env_master_category ON env_master(category);
CREATE INDEX idx_env_master_active ON env_master(is_active);

-- Create audit log for environment variable changes
CREATE TABLE env_master_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    env_id UUID REFERENCES env_master(id),
    action VARCHAR(50), -- CREATE, UPDATE, DELETE, ROTATE
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT NOW(),
    reason TEXT
);

-- Insert all your current environment variables
INSERT INTO env_master (key, value, description, category, project, is_sensitive) VALUES
-- API Keys
('ANTHROPIC_API_KEY', '<ANTHROPIC_API_KEY_REDACTED>', 'Anthropic Claude API', 'API_KEYS', 'all', true),
('OPENAI_API_KEY', '<OPENAI_API_KEY_REDACTED>', 'OpenAI GPT API', 'API_KEYS', 'all', true),
('GEMINI_API_KEY', '<GOOGLE_API_KEY_REDACTED>', 'Google Gemini API', 'API_KEYS', 'all', true),
('STRIPE_SECRET_KEY', '<STRIPE_KEY_REDACTED>', 'Stripe Live Secret Key', 'API_KEYS', 'all', true),
('STRIPE_WEBHOOK_SECRET', 'whsec_2NdWoNYo3VqDbvWJ2hjy5Pv0V4vLNPOL', 'Stripe Webhook Secret', 'API_KEYS', 'backend', true),
('ELEVENLABS_API_KEY', 'sk_a4be8c327484fa7d24eb94e8b16462827095939269fd6e49', 'ElevenLabs Voice API', 'API_KEYS', 'all', true),

-- Database
('DATABASE_URL', 'postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres', 'Primary database connection', 'DATABASE', 'all', true),
('SUPABASE_URL', 'https://yomagoqdmxszqtdwuhab.supabase.co', 'Supabase project URL', 'DATABASE', 'all', false),
('SUPABASE_ANON_KEY', '<JWT_REDACTED>', 'Supabase anon key', 'DATABASE', 'all', false),
('SUPABASE_SERVICE_ROLE_KEY', '<JWT_REDACTED>', 'Supabase service role key', 'DATABASE', 'backend', true),

-- CenterPoint
('CENTERPOINT_BASE_URL', 'https://api.centerpointconnect.io', 'CenterPoint API URL', 'SERVICES', 'all', false),
('CENTERPOINT_BEARER_TOKEN', 'eyJvcmciOiI2NmJlMzEwMzFiMGJjMTAwMDEwM2RiN2MiLCJpZCI6ImM4ZDdiMDIyNGQ4NDQ5OGI5M2M', 'CenterPoint Bearer Token', 'SERVICES', 'all', true),
('CENTERPOINT_TENANT_ID', '97f82b360baefdd73400ad342562586', 'CenterPoint Tenant ID', 'SERVICES', 'all', false),
('CENTERPOINT_USERNAME', 'matthew@weathercraft.net', 'CenterPoint Username', 'SERVICES', 'all', false),
('CENTERPOINT_PASSWORD', 'Matt1304', 'CenterPoint Password', 'SERVICES', 'all', true),

-- Slack
('SLACK_WEBHOOK_URL', 'https://hooks.slack.com/services/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', 'Slack webhook for notifications', 'SERVICES', 'all', true),
('SLACK_BOT_TOKEN', 'xoxb-8793573557089-9196687309280-ijiC7wnSr2spEFqzddJPAGkJ', 'Slack bot token', 'SERVICES', 'backend', true),

-- Email
('SMTP_HOST', 'smtp.gmail.com', 'SMTP server host', 'EMAIL', 'all', false),
('SMTP_PORT', '587', 'SMTP server port', 'EMAIL', 'all', false),
('SMTP_USERNAME', 'matthew@brainstackstudio.com', 'SMTP username', 'EMAIL', 'all', false),
('SMTP_PASSWORD', 'Mww00dw0rth@2O1S$', 'SMTP password', 'EMAIL', 'all', true),

-- Application URLs
('FRONTEND_URL', 'https://myroofgenius.com', 'Frontend application URL', 'APPLICATION', 'all', false),
('BACKEND_URL', 'https://brainops-backend-prod.onrender.com', 'Backend API URL', 'APPLICATION', 'all', false),
('NEXT_PUBLIC_API_URL', 'https://brainops-backend-prod.onrender.com', 'Next.js public API URL', 'APPLICATION', 'frontend', false),

-- Other Services
('NOTION_API_KEY', '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', 'Notion API key', 'SERVICES', 'all', true),
('CLICKUP_API_KEY', 'pk_87973158_072HQ07UJ40CGO1EI9BY5SGK2IZHADL4', 'ClickUp API key', 'SERVICES', 'all', true),
('GITHUB_TOKEN', '<GITHUB_TOKEN_REDACTED>', 'GitHub personal access token', 'SERVICES', 'all', true),
('SENTRY_DSN', 'https://992d4db49f680aa437e79c137466a083@o4509510470860800.ingest.us.sentry.io/4509510476300288', 'Sentry error tracking', 'SERVICES', 'all', false),

-- Security
('JWT_SECRET_KEY', 'brainops-jwt-secret-2025-production', 'JWT signing secret', 'SECURITY', 'backend', true),
('NEXTAUTH_SECRET', 'pWyEdzAzwDm79hqYblm/ROotd1Z4GMOHheJcKh3sffw=', 'NextAuth secret', 'SECURITY', 'frontend', true),

-- Redis
('REDIS_URL', 'redis://localhost:6379/0', 'Redis connection URL', 'DATABASE', 'backend', false),

-- AWS
('AWS_ACCESS_KEY_ID', 'YOUR_AWS_ACCESS_KEY_ID_HERE', 'AWS access key', 'SERVICES', 'all', true),
('AWS_SECRET_ACCESS_KEY', 'YOUR_AWS_SECRET_ACCESS_KEY_HERE', 'AWS secret key', 'SERVICES', 'all', true),
('AWS_DEFAULT_REGION', 'us-east-2', 'AWS region', 'SERVICES', 'all', false),

-- System
('ENVIRONMENT', 'production', 'Environment name', 'SYSTEM', 'all', false),
('DEBUG', 'false', 'Debug mode', 'SYSTEM', 'all', false),
('PORT', '10000', 'Application port', 'SYSTEM', 'backend', false),
('LOG_LEVEL', 'INFO', 'Logging level', 'SYSTEM', 'all', false);

-- Create function to get environment variables for a project
CREATE OR REPLACE FUNCTION get_env_vars(
    p_project VARCHAR DEFAULT 'all',
    p_environment VARCHAR DEFAULT 'production'
)
RETURNS TABLE (
    key VARCHAR,
    value TEXT,
    is_sensitive BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.key,
        CASE 
            WHEN e.is_sensitive THEN '***SENSITIVE***'
            ELSE e.value
        END as value,
        e.is_sensitive
    FROM env_master e
    WHERE e.is_active = true
        AND e.environment = p_environment
        AND (e.project = p_project OR e.project = 'all')
    ORDER BY e.category, e.key;
END;
$$ LANGUAGE plpgsql;

-- Create function to rotate a key
CREATE OR REPLACE FUNCTION rotate_env_key(
    p_key VARCHAR,
    p_new_value TEXT,
    p_reason TEXT DEFAULT 'Scheduled rotation'
)
RETURNS BOOLEAN AS $$
DECLARE
    v_old_value TEXT;
    v_env_id UUID;
BEGIN
    -- Get current value
    SELECT value, id INTO v_old_value, v_env_id
    FROM env_master
    WHERE key = p_key AND is_active = true
    LIMIT 1;
    
    -- Update the value
    UPDATE env_master
    SET 
        value = p_new_value,
        last_rotated = NOW(),
        updated_at = NOW()
    WHERE id = v_env_id;
    
    -- Log the change
    INSERT INTO env_master_audit (env_id, action, old_value, new_value, changed_by, reason)
    VALUES (v_env_id, 'ROTATE', v_old_value, p_new_value, 'system', p_reason);
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT ON env_master TO authenticated;
GRANT EXECUTE ON FUNCTION get_env_vars TO authenticated;

-- Add RLS policies
ALTER TABLE env_master ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service accounts can read env vars" ON env_master
    FOR SELECT
    USING (true);

CREATE POLICY "Only admins can modify env vars" ON env_master
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Create view for non-sensitive variables
CREATE VIEW public_env_vars AS
SELECT 
    key,
    value,
    description,
    category,
    project
FROM env_master
WHERE is_sensitive = false
    AND is_active = true;