-- Drop existing tables with issues and recreate properly
DROP TABLE IF EXISTS ai_board_decisions CASCADE;
DROP TABLE IF EXISTS aurea_thoughts CASCADE;
DROP TABLE IF EXISTS aurea_conversations CASCADE;
DROP TABLE IF EXISTS aurea_insights CASCADE;

-- Recreate AI Board decisions table
CREATE TABLE ai_board_decisions (
    id SERIAL PRIMARY KEY,
    decision_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255),
    decision_type VARCHAR(100),
    priority VARCHAR(50),
    description TEXT,
    context JSONB DEFAULT '{}',
    reasoning JSONB DEFAULT '{}',
    outcome JSONB DEFAULT '{}',
    confidence_score FLOAT,
    impact_score FLOAT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES ai_board_sessions(session_id) ON DELETE CASCADE
);

-- Recreate AUREA related tables
CREATE TABLE aurea_thoughts (
    id SERIAL PRIMARY KEY,
    thought_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255),
    thought_pattern VARCHAR(100),
    content TEXT,
    confidence FLOAT,
    emotional_tone FLOAT,
    associations JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES aurea_consciousness(session_id) ON DELETE CASCADE
);

CREATE TABLE aurea_conversations (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255),
    user_message TEXT,
    aurea_response TEXT,
    emotional_context JSONB DEFAULT '{}',
    decision_context JSONB DEFAULT '{}',
    learning_points JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES aurea_consciousness(session_id) ON DELETE CASCADE
);

CREATE TABLE aurea_insights (
    id SERIAL PRIMARY KEY,
    insight_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255),
    insight_type VARCHAR(100),
    content TEXT,
    confidence FLOAT,
    impact_score FLOAT,
    actionable BOOLEAN DEFAULT false,
    actions_taken JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES aurea_consciousness(session_id) ON DELETE CASCADE
);

-- Create missing indexes
CREATE INDEX IF NOT EXISTS idx_ai_board_decisions_session ON ai_board_decisions(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_board_decisions_status ON ai_board_decisions(status);
CREATE INDEX IF NOT EXISTS idx_aurea_thoughts_session ON aurea_thoughts(session_id);
CREATE INDEX IF NOT EXISTS idx_aurea_conversations_session ON aurea_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_aurea_insights_session ON aurea_insights(session_id);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;