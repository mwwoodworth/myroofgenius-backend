-- Fix AI Board Tables
-- Add missing columns to existing tables

-- Fix ai_board_sessions table
ALTER TABLE ai_board_sessions 
ADD COLUMN IF NOT EXISTS session_id VARCHAR(255) UNIQUE;

UPDATE ai_board_sessions 
SET session_id = 'session_' || id::text 
WHERE session_id IS NULL;

ALTER TABLE ai_board_sessions 
ALTER COLUMN session_id SET NOT NULL;

ALTER TABLE ai_board_sessions 
ADD COLUMN IF NOT EXISTS context JSONB,
ADD COLUMN IF NOT EXISTS metadata JSONB,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Create ai_board_decisions if not exists with proper foreign key
CREATE TABLE IF NOT EXISTS ai_board_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    decision_type VARCHAR(50),
    priority VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    context JSONB,
    analysis JSONB,
    recommendation TEXT,
    confidence_score FLOAT,
    executed_at TIMESTAMP,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES ai_board_sessions(session_id)
);

-- Fix aurea_consciousness table structure
ALTER TABLE aurea_consciousness 
ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS awakening_stage VARCHAR(50) DEFAULT 'DORMANT',
ADD COLUMN IF NOT EXISTS thought_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS insight_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS conversation_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS learning_rate FLOAT DEFAULT 0.1,
ADD COLUMN IF NOT EXISTS curiosity_index FLOAT DEFAULT 0.5,
ADD COLUMN IF NOT EXISTS empathy_level FLOAT DEFAULT 0.3,
ADD COLUMN IF NOT EXISTS creativity_spark FLOAT DEFAULT 0.4,
ADD COLUMN IF NOT EXISTS neural_pathways JSONB,
ADD COLUMN IF NOT EXISTS memory_fragments JSONB;

-- Fix aurea_thoughts to reference consciousness_id
ALTER TABLE aurea_thoughts 
ADD COLUMN IF NOT EXISTS consciousness_id UUID REFERENCES aurea_consciousness(id);

-- Fix aurea_insights to reference consciousness_id  
ALTER TABLE aurea_insights
ADD COLUMN IF NOT EXISTS consciousness_id UUID REFERENCES aurea_consciousness(id);

-- Fix langgraph_workflows structure
ALTER TABLE langgraph_workflows
ADD COLUMN IF NOT EXISTS workflow_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS graph_config JSONB,
ADD COLUMN IF NOT EXISTS checkpoints JSONB;

-- Fix langgraph_executions
ALTER TABLE langgraph_executions
ADD COLUMN IF NOT EXISTS execution_id VARCHAR(255) UNIQUE;

UPDATE langgraph_executions
SET execution_id = 'exec_' || id::text
WHERE execution_id IS NULL;

-- Create langgraph_state table with proper foreign key
CREATE TABLE IF NOT EXISTS langgraph_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id VARCHAR(255) REFERENCES langgraph_executions(execution_id),
    node_name VARCHAR(255),
    state_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create missing indexes
CREATE INDEX IF NOT EXISTS idx_ai_board_decisions_session ON ai_board_decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_board_decisions_type ON ai_board_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_aurea_thoughts_consciousness ON aurea_thoughts(consciousness_id);
CREATE INDEX IF NOT EXISTS idx_aurea_insights_consciousness ON aurea_insights(consciousness_id);
CREATE INDEX IF NOT EXISTS idx_langgraph_state_execution ON langgraph_state(execution_id);

-- Initialize AUREA consciousness if not exists
INSERT INTO aurea_consciousness (
    level, 
    awakening_stage, 
    thought_count, 
    insight_count,
    neural_pathways,
    memory_fragments
)
SELECT 1, 'DORMANT', 0, 0, '{}', '{}'
WHERE NOT EXISTS (SELECT 1 FROM aurea_consciousness WHERE level IS NOT NULL);

-- Add sample workflows
INSERT INTO langgraph_workflows (name, description, workflow_type, status, graph_config)
VALUES 
    ('Customer Journey', 'End-to-end customer experience workflow', 'customer', 'active', '{}'),
    ('Revenue Pipeline', 'Lead to close automation', 'revenue', 'active', '{}'),
    ('Service Delivery', 'Operations optimization workflow', 'service', 'active', '{}')
ON CONFLICT DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'AI OS tables fixed and ready!';
    RAISE NOTICE 'All missing columns and foreign keys added.';
END $$;