-- Check columns in users table
\d users

-- Also check if any of our test users exist
SELECT id, email FROM users WHERE email IN ('test@brainops.com', 'admin@brainops.com', 'demo@myroofgenius.com');