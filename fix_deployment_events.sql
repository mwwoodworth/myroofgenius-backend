-- Fix deployment_events table
ALTER TABLE deployment_events ADD COLUMN IF NOT EXISTS platform VARCHAR(50);
