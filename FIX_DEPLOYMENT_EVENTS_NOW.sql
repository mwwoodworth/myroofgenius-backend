-- Fix deployment_events table schema
ALTER TABLE deployment_events 
ADD COLUMN IF NOT EXISTS platform VARCHAR(50) DEFAULT 'render';

ALTER TABLE deployment_events 
ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add any other missing columns
ALTER TABLE deployment_events 
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_deployment_events_timestamp 
ON deployment_events(timestamp DESC);

-- Verify the fix
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'deployment_events'
ORDER BY ordinal_position;
