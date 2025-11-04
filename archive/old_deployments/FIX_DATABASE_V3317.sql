-- Fix missing vector_data_metadata column in ai_memories table
ALTER TABLE ai_memories 
ADD COLUMN IF NOT EXISTS vector_data_metadata JSONB DEFAULT '{}';

-- Create index on the column
CREATE INDEX IF NOT EXISTS idx_ai_memories_vector_metadata 
ON ai_memories USING gin(vector_data_metadata);

-- Update any NULL values to empty JSON
UPDATE ai_memories 
SET vector_data_metadata = '{}' 
WHERE vector_data_metadata IS NULL;