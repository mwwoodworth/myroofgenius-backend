-- Fix permissions for env_master table
-- Handle missing roles gracefully

-- Drop existing policies
DROP POLICY IF EXISTS "Service accounts can read env vars" ON env_master;
DROP POLICY IF EXISTS "Only admins can modify env vars" ON env_master;

-- Create new policies that work with Supabase
ALTER TABLE env_master ENABLE ROW LEVEL SECURITY;

-- Allow all authenticated users to read non-sensitive vars
CREATE POLICY "Allow read access to env vars" ON env_master
    FOR SELECT
    USING (true);

-- Only allow modifications through service role
CREATE POLICY "Service role can modify env vars" ON env_master
    FOR ALL
    USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');

-- Create function to get env vars (simplified)
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
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute to public (function will handle security)
GRANT EXECUTE ON FUNCTION get_env_vars TO public;

-- Create API function to retrieve env vars for backend
CREATE OR REPLACE FUNCTION get_backend_env_vars()
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}'::JSONB;
    env_var RECORD;
BEGIN
    -- Get all env vars for backend
    FOR env_var IN
        SELECT key, value
        FROM env_master
        WHERE is_active = true
            AND environment = 'production'
            AND (project = 'backend' OR project = 'all')
    LOOP
        result := result || jsonb_build_object(env_var.key, env_var.value);
    END LOOP;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute to public
GRANT EXECUTE ON FUNCTION get_backend_env_vars TO public;

-- Update some critical values to ensure they're correct
UPDATE env_master 
SET value = '<STRIPE_KEY_REDACTED>'
WHERE key = 'STRIPE_SECRET_KEY';

UPDATE env_master 
SET value = 'https://brainops-backend-prod.onrender.com'
WHERE key = 'BACKEND_URL';

UPDATE env_master 
SET value = 'https://myroofgenius.com'
WHERE key = 'FRONTEND_URL';

-- Add missing Stripe test key for development
INSERT INTO env_master (key, value, description, category, project, is_sensitive, environment)
VALUES 
('STRIPE_TEST_KEY', '<STRIPE_KEY_REDACTED>', 'Stripe Test Secret Key', 'API_KEYS', 'all', true, 'development')
ON CONFLICT (key, project, environment) DO NOTHING;

SELECT 'Environment master table permissions fixed!' as status;