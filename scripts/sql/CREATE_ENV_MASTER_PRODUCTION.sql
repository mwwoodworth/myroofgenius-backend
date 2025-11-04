-- MASTER ENVIRONMENT VARIABLES TABLE - PRODUCTION READY
-- Single source of truth for all configuration across all systems

-- Create the master environment variables table
CREATE TABLE IF NOT EXISTS env_master (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100),
    project VARCHAR(100),
    environment VARCHAR(50) DEFAULT 'production',
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_env_master_key ON env_master(key);
CREATE INDEX IF NOT EXISTS idx_env_master_project ON env_master(project);
CREATE INDEX IF NOT EXISTS idx_env_master_category ON env_master(category);
CREATE INDEX IF NOT EXISTS idx_env_master_active ON env_master(is_active);

-- Create audit log
CREATE TABLE IF NOT EXISTS env_master_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    env_id UUID REFERENCES env_master(id),
    action VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP DEFAULT NOW(),
    reason TEXT
);

-- Create secure function to get env vars
CREATE OR REPLACE FUNCTION get_env_var(p_key TEXT, p_project TEXT DEFAULT 'all')
RETURNS TEXT AS $$
DECLARE
    v_value TEXT;
BEGIN
    SELECT value INTO v_value
    FROM env_master
    WHERE key = p_key 
    AND (project = p_project OR project = 'all')
    AND is_active = true
    AND environment = 'production'
    LIMIT 1;
    
    RETURN v_value;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to sync env vars for an application
CREATE OR REPLACE FUNCTION sync_env_vars(p_project TEXT)
RETURNS TABLE(key TEXT, value TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT em.key::TEXT, em.value::TEXT
    FROM env_master em
    WHERE em.is_active = true
    AND em.environment = 'production'
    AND (em.project = p_project OR em.project = 'all')
    ORDER BY em.key;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Insert critical environment variables (PRODUCTION KEYS)
INSERT INTO env_master (key, value, description, category, project, is_sensitive) VALUES
-- Stripe (LIVE KEYS)
('STRIPE_SECRET_KEY', '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', 'Stripe Live Secret Key', 'PAYMENT', 'all', true),
('STRIPE_PUBLISHABLE_KEY', 'pk_live_51PXs5fRw7K3sXkUXe9L1N37RNnQPBBBKRQKKPEBJdNqz2RQxYpqxXXyYKJ0fTINGjGkOsIy09m1v4fKtY5xOPud00Z8YP8Cxr', 'Stripe Live Publishable Key', 'PAYMENT', 'frontend', false),
('STRIPE_WEBHOOK_SECRET', 'whsec_PENDING', 'Stripe Webhook Secret - Will be set by automation', 'PAYMENT', 'backend', true),

-- AI Services
('ANTHROPIC_API_KEY', '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', 'Anthropic Claude API', 'AI', 'all', true),
('OPENAI_API_KEY', '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', 'OpenAI GPT API', 'AI', 'all', true),
('GEMINI_API_KEY', 'AIzaSyAHlPJBr5HH1xKvVoKR8C6BHvMZh3G_kik', 'Google Gemini API', 'AI', 'all', true),

-- Database
('DATABASE_URL', 'postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres', 'Primary Database Connection', 'DATABASE', 'backend', true),
('SUPABASE_URL', 'https://yomagoqdmxszqtdwuhab.supabase.co', 'Supabase Project URL', 'DATABASE', 'all', false),
('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk4MzMyNzYsImV4cCI6MjA2NTQwOTI3Nn0.gKC0PybkqPTLlzDWIdS8a6KFVXZ1PQaNcQr2ekroxzE', 'Supabase Anon Key', 'DATABASE', 'frontend', false),
('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ', 'Supabase Service Role Key', 'DATABASE', 'backend', true),

-- Authentication
('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-this-in-production', 'JWT Secret for tokens', 'AUTH', 'backend', true),
('NEXTAUTH_SECRET', 'nqG9HgE8niGmFs0BVoY7YBhK7TikRWBOE8Q3/dLJGng=', 'NextAuth Secret', 'AUTH', 'frontend', true),
('NEXTAUTH_URL', 'https://myroofgenius.com', 'NextAuth Base URL', 'AUTH', 'frontend', false),

-- Deployment
('RENDER_API_KEY', 'rnd_gEWiB96SdsrL4dPqPRKvLCIfYpZx', 'Render API Key', 'DEPLOYMENT', 'backend', true),
('RENDER_SERVICE_ID', 'srv-d1tfs4idbo4c73di6k00', 'Render Service ID', 'DEPLOYMENT', 'backend', false),
('RENDER_DEPLOY_HOOK', 'https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM', 'Render Deploy Hook', 'DEPLOYMENT', 'backend', true),
('DOCKER_USERNAME', 'mwwoodworth', 'Docker Hub Username', 'DEPLOYMENT', 'backend', false),
('DOCKER_PAT', 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho', 'Docker Hub PAT', 'DEPLOYMENT', 'backend', true),

-- Application URLs
('NEXT_PUBLIC_API_URL', 'https://brainops-backend-prod.onrender.com', 'Backend API URL', 'APPLICATION', 'frontend', false),
('FRONTEND_URL', 'https://myroofgenius.com', 'Frontend Application URL', 'APPLICATION', 'backend', false),

-- Feature Flags
('ENABLE_STRIPE_AUTOMATION', 'true', 'Enable automated Stripe management', 'FEATURES', 'all', false),
('ENABLE_ENV_SYNC', 'true', 'Enable environment variable sync', 'FEATURES', 'all', false),
('ENABLE_E2E_TESTING', 'true', 'Enable E2E testing on deploy', 'FEATURES', 'all', false),
('ENABLE_AUTO_DEPLOY', 'true', 'Enable automatic deployments', 'FEATURES', 'all', false)
ON CONFLICT (key, project, environment) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();

-- Grant permissions
GRANT SELECT ON env_master TO authenticated;
GRANT EXECUTE ON FUNCTION get_env_var TO authenticated;
GRANT EXECUTE ON FUNCTION sync_env_vars TO authenticated;

-- Create RLS policies
ALTER TABLE env_master ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service accounts can read env vars" ON env_master
    FOR SELECT
    USING (true);

CREATE POLICY "Only admins can modify env vars" ON env_master
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'admin');

-- Success message
SELECT 'Environment Master table created with ' || COUNT(*) || ' variables' as status
FROM env_master
WHERE is_active = true;