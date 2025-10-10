-- Fix Lead Capture Schema Issues
-- This migration adds missing columns that the lead capture endpoint expects

-- First check what columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'leads';

-- Add missing columns if they don't exist
ALTER TABLE leads
ADD COLUMN IF NOT EXISTS project_type VARCHAR(255),
ADD COLUMN IF NOT EXISTS message TEXT,
ADD COLUMN IF NOT EXISTS source VARCHAR(100) DEFAULT 'website',
ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 50,
ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 50,
ADD COLUMN IF NOT EXISTS ai_enriched BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Ensure all required columns have proper defaults
ALTER TABLE leads
ALTER COLUMN phone SET DEFAULT '',
ALTER COLUMN company SET DEFAULT '',
ALTER COLUMN created_at SET DEFAULT NOW();

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);

-- Verify the schema is correct
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'leads'
ORDER BY ordinal_position;