-- Ensure all AI tables exist in production
-- Run this directly on production database

-- Create langgraph_executions if not exists
CREATE TABLE IF NOT EXISTS langgraph_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID,
    execution_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    context JSONB DEFAULT '{}',
    result JSONB,
    error TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_langgraph_exec_status ON langgraph_executions(status);
CREATE INDEX IF NOT EXISTS idx_langgraph_exec_workflow ON langgraph_executions(workflow_id);

-- Grant permissions
GRANT ALL ON langgraph_executions TO postgres;
GRANT ALL ON langgraph_executions TO anon;
GRANT ALL ON langgraph_executions TO authenticated;
GRANT ALL ON langgraph_executions TO service_role;

-- Check what we have
SELECT 'langgraph_executions' as table_name, COUNT(*) as count FROM langgraph_executions
UNION ALL
SELECT 'langgraph_workflows', COUNT(*) FROM langgraph_workflows
UNION ALL  
SELECT 'ai_board_sessions', COUNT(*) FROM ai_board_sessions
UNION ALL
SELECT 'aurea_consciousness', COUNT(*) FROM aurea_consciousness;