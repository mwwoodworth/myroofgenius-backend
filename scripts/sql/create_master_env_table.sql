-- Create Master Environment Variables Table
-- This table will serve as the single source of truth for all environment variables
-- across Vercel, Render, and other services

-- Drop existing table if it exists
DROP TABLE IF EXISTS master_env_vars CASCADE;

-- Create the master environment variables table
CREATE TABLE master_env_vars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT NOT NULL,
    service VARCHAR(100) NOT NULL, -- 'vercel', 'render', 'supabase', 'global'
    environment VARCHAR(50) NOT NULL DEFAULT 'production', -- 'production', 'staging', 'development'
    description TEXT,
    is_secret BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    last_synced TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_key_service_env UNIQUE(key, service, environment)
);

-- Create indexes for performance
CREATE INDEX idx_master_env_vars_key ON master_env_vars(key);
CREATE INDEX idx_master_env_vars_service ON master_env_vars(service);
CREATE INDEX idx_master_env_vars_environment ON master_env_vars(environment);
CREATE INDEX idx_master_env_vars_active ON master_env_vars(is_active);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_master_env_vars_updated_at 
    BEFORE UPDATE ON master_env_vars 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create a view for easy access to active production variables
CREATE VIEW active_env_vars AS
SELECT 
    key,
    value,
    service,
    description,
    is_secret
FROM master_env_vars
WHERE is_active = true 
AND environment = 'production'
ORDER BY service, key;

-- Create a function to get env vars for a specific service
CREATE OR REPLACE FUNCTION get_service_env_vars(
    p_service VARCHAR,
    p_environment VARCHAR DEFAULT 'production'
)
RETURNS TABLE(key VARCHAR, value TEXT, is_secret BOOLEAN) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mev.key,
        CASE 
            WHEN mev.is_secret THEN '***REDACTED***'
            ELSE mev.value
        END as value,
        mev.is_secret
    FROM master_env_vars mev
    WHERE mev.service = p_service
    AND mev.environment = p_environment
    AND mev.is_active = true
    ORDER BY mev.key;
END;
$$ LANGUAGE plpgsql;

-- Create a function to sync environment variables
CREATE OR REPLACE FUNCTION sync_env_var(
    p_key VARCHAR,
    p_value TEXT,
    p_service VARCHAR,
    p_environment VARCHAR DEFAULT 'production',
    p_description TEXT DEFAULT NULL,
    p_is_secret BOOLEAN DEFAULT false
)
RETURNS UUID AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO master_env_vars (key, value, service, environment, description, is_secret, last_synced)
    VALUES (p_key, p_value, p_service, p_environment, p_description, p_is_secret, CURRENT_TIMESTAMP)
    ON CONFLICT (key, service, environment) 
    DO UPDATE SET 
        value = EXCLUDED.value,
        description = COALESCE(EXCLUDED.description, master_env_vars.description),
        is_secret = EXCLUDED.is_secret,
        last_synced = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- Insert critical environment variables
INSERT INTO master_env_vars (key, value, service, environment, description, is_secret) VALUES
-- Database
('DATABASE_URL', 'postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require', 'global', 'production', 'Main PostgreSQL database connection string', true),
('DIRECT_URL', 'postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres', 'global', 'production', 'Direct database connection for migrations', true),

-- Supabase
('NEXT_PUBLIC_SUPABASE_URL', 'https://yomagoqdmxszqtdwuhab.supabase.co', 'global', 'production', 'Supabase project URL', false),
('NEXT_PUBLIC_SUPABASE_ANON_KEY', '<JWT_REDACTED>', 'global', 'production', 'Supabase anonymous key', false),
('SUPABASE_SERVICE_ROLE_KEY', '<JWT_REDACTED>', 'global', 'production', 'Supabase service role key', true),

-- API Keys
('OPENAI_API_KEY', '<OPENAI_API_KEY_REDACTED>', 'global', 'production', 'OpenAI API key', true),
('ANTHROPIC_API_KEY', '<ANTHROPIC_API_KEY_REDACTED>', 'global', 'production', 'Anthropic Claude API key', true),
('GOOGLE_GENERATIVE_AI_API_KEY', '<GOOGLE_API_KEY_REDACTED>', 'global', 'production', 'Google Gemini API key', true),

-- Stripe
('STRIPE_SECRET_KEY', '<STRIPE_KEY_REDACTED>', 'global', 'production', 'Stripe secret key', true),
('STRIPE_PUBLISHABLE_KEY', 'pk_live_51QeWdBKXziJdvOrvD8eGx6UQlJWOUoJ1l7DvqPmMRdHBCK2VJrrcMQ6ILWnxVeSJZznqoNrOZdcTRJwlHoyNyKIY00wPxUbmU8', 'global', 'production', 'Stripe publishable key', false),
('STRIPE_WEBHOOK_SECRET', 'whsec_production_secret', 'global', 'production', 'Stripe webhook secret', true),

-- JWT & Auth
('JWT_SECRET', 'your-super-secret-jwt-key-2024-production', 'render', 'production', 'JWT secret for authentication', true),
('SECRET_KEY', 'your-super-secret-key-2024-production', 'render', 'production', 'Application secret key', true),

-- Render
('RENDER_API_KEY', 'rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx', 'render', 'production', 'Render API key', true),
('RENDER_DEPLOY_HOOK', 'https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM', 'render', 'production', 'Render deployment webhook', true),

-- Docker
('DOCKER_USERNAME', 'mwwoodworth', 'global', 'production', 'Docker Hub username', false),
('DOCKER_TOKEN', 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho', 'global', 'production', 'Docker Hub access token', true),

-- CenterPoint
('CENTERPOINT_BASE_URL', 'https://api.centerpointconnect.io', 'weathercraft', 'production', 'CenterPoint API base URL', false),
('CENTERPOINT_BEARER_TOKEN', 'eyJvcmciOiI2NmJlMzEwMzFiMGJjMTAwMDEwM2RiN2MiLCJpZCI6ImM4ZDdiMDIyNGQ4NDQ5OGI5M2MwYzY4MTc0NWU5M2Y0IiwiaCI6Im11cm11cjEyOCJ9', 'weathercraft', 'production', 'CenterPoint bearer token', true),
('CENTERPOINT_TENANT_ID', '97f82b360baefdd73400ad342562586', 'weathercraft', 'production', 'CenterPoint tenant ID', true),

-- Application URLs
('NEXT_PUBLIC_APP_URL', 'https://myroofgenius.com', 'vercel', 'production', 'MyRoofGenius app URL', false),
('NEXT_PUBLIC_API_URL', 'https://brainops-backend-prod.onrender.com', 'vercel', 'production', 'Backend API URL', false),
('BACKEND_URL', 'https://brainops-backend-prod.onrender.com', 'global', 'production', 'Backend service URL', false),

-- Email
('RESEND_API_KEY', 're_123456789', 'global', 'production', 'Resend email service API key', true),
('EMAIL_FROM', 'noreply@myroofgenius.com', 'global', 'production', 'Default from email address', false),

-- Feature Flags
('ENABLE_AI_FEATURES', 'true', 'global', 'production', 'Enable AI features', false),
('ENABLE_PERSISTENT_MEMORY', 'true', 'global', 'production', 'Enable persistent memory system', false),
('ENABLE_CRON_JOBS', 'true', 'global', 'production', 'Enable cron jobs', false),
('ENABLE_QUEUES', 'true', 'global', 'production', 'Enable queue processing', false)
ON CONFLICT (key, service, environment) DO UPDATE
SET 
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    is_secret = EXCLUDED.is_secret,
    last_synced = CURRENT_TIMESTAMP;

-- Create a monitoring view to check sync status
CREATE VIEW env_sync_status AS
SELECT 
    service,
    environment,
    COUNT(*) as total_vars,
    COUNT(CASE WHEN last_synced > NOW() - INTERVAL '1 day' THEN 1 END) as recently_synced,
    COUNT(CASE WHEN is_secret THEN 1 END) as secret_vars,
    MAX(last_synced) as last_sync_time
FROM master_env_vars
WHERE is_active = true
GROUP BY service, environment
ORDER BY service, environment;

-- Grant appropriate permissions
GRANT SELECT ON master_env_vars TO authenticated;
GRANT SELECT ON active_env_vars TO authenticated;
GRANT SELECT ON env_sync_status TO authenticated;
GRANT EXECUTE ON FUNCTION get_service_env_vars TO authenticated;

-- Add row level security
ALTER TABLE master_env_vars ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for reading non-secret values
CREATE POLICY "Allow reading non-secret env vars" ON master_env_vars
    FOR SELECT
    USING (is_secret = false OR auth.role() = 'service_role');

-- Create RLS policy for service role to manage all
CREATE POLICY "Service role can manage all env vars" ON master_env_vars
    FOR ALL
    USING (auth.role() = 'service_role');