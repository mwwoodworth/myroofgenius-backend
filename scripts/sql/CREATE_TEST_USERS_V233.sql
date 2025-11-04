-- Create test users for authentication testing
-- Password: TestPassword123! (bcrypt hash)

-- Check if users exist first
SELECT email FROM app_users WHERE email IN ('test@brainops.com', 'admin@brainops.com', 'demo@myroofgenius.com');

-- Insert test user if not exists
INSERT INTO app_users (
    id,
    email,
    username,
    hashed_password,
    is_active,
    is_verified,
    role,
    created_at
) VALUES (
    gen_random_uuid(),
    'test@brainops.com',
    'test',
    '$2b$12$YourHashHere', -- This needs to be a real bcrypt hash
    true,
    true,
    'user',
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Note: You'll need to generate the actual bcrypt hash for the password