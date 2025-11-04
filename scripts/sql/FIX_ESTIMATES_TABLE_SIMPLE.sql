-- Simplify estimates table for ERP API
-- Make all the extra required fields optional or have defaults

-- First ensure we have a default user
INSERT INTO app_users (id, email, created_at)
VALUES ('00000000-0000-0000-0000-000000000000', 'system@brainops.com', CURRENT_TIMESTAMP)
ON CONFLICT (id) DO NOTHING;

-- Now alter the estimates table to make fields optional
ALTER TABLE estimates ALTER COLUMN client_name DROP NOT NULL;
ALTER TABLE estimates ALTER COLUMN created_by_id SET DEFAULT '00000000-0000-0000-0000-000000000000';
ALTER TABLE estimates ALTER COLUMN valid_until SET DEFAULT (CURRENT_DATE + INTERVAL '30 days');
ALTER TABLE estimates ALTER COLUMN total DROP NOT NULL;