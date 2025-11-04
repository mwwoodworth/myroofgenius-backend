-- Fix all missing tables and columns for v9.7
-- This will create all missing database objects

-- Fix vercel_logs table (for devops monitoring)
CREATE TABLE IF NOT EXISTS vercel_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(50),
    message TEXT,
    source VARCHAR(100),
    deployment_id VARCHAR(255),
    request_id VARCHAR(255),
    path VARCHAR(500),
    status_code INTEGER,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fix deployment_events table
CREATE TABLE IF NOT EXISTS deployment_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100),
    service VARCHAR(100),
    deployment_id VARCHAR(255),
    status VARCHAR(50),
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fix langgraph_executions table
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

-- Fix ai_board_sessions table - add missing context column
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'ai_board_sessions' 
                   AND column_name = 'context') THEN
        ALTER TABLE ai_board_sessions ADD COLUMN context JSONB DEFAULT '{}';
    END IF;
END $$;

-- Create ai_board_sessions if it doesn't exist
CREATE TABLE IF NOT EXISTS ai_board_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_type VARCHAR(100),
    context JSONB DEFAULT '{}',
    decisions JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fix invoices table - add missing paid_amount column
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'invoices' 
                   AND column_name = 'paid_amount') THEN
        ALTER TABLE invoices ADD COLUMN paid_amount DECIMAL(12,2) DEFAULT 0;
    END IF;
END $$;

-- Create langgraph_workflows if missing
CREATE TABLE IF NOT EXISTS langgraph_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    definition JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default workflows
INSERT INTO langgraph_workflows (name, status, definition)
VALUES 
    ('Customer Journey', 'active', '{"type": "customer"}'),
    ('Revenue Pipeline', 'active', '{"type": "revenue"}'),
    ('Service Delivery', 'active', '{"type": "service"}')
ON CONFLICT (name) DO NOTHING;

-- Create aurea_consciousness if missing
CREATE TABLE IF NOT EXISTS aurea_consciousness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(50) DEFAULT 'ADAPTIVE',
    state JSONB DEFAULT '{}',
    memories JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions to all roles
GRANT ALL ON vercel_logs TO postgres, anon, authenticated, service_role;
GRANT ALL ON deployment_events TO postgres, anon, authenticated, service_role;
GRANT ALL ON langgraph_executions TO postgres, anon, authenticated, service_role;
GRANT ALL ON langgraph_workflows TO postgres, anon, authenticated, service_role;
GRANT ALL ON ai_board_sessions TO postgres, anon, authenticated, service_role;
GRANT ALL ON aurea_consciousness TO postgres, anon, authenticated, service_role;

-- Show what we have
SELECT 'Tables created/fixed:' as status;
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN (
    'vercel_logs', 
    'deployment_events', 
    'langgraph_executions',
    'langgraph_workflows',
    'ai_board_sessions',
    'aurea_consciousness',
    'invoices'
)
ORDER BY table_name;