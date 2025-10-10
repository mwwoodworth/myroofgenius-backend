-- Create REAL chat system tables for AI conversations
-- Store actual conversation history, not mock responses

-- Chat conversations table
CREATE TABLE IF NOT EXISTS chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    session_id VARCHAR(255),
    
    -- Conversation metadata
    title VARCHAR(255),
    summary TEXT,
    context JSONB DEFAULT '{}'::jsonb,
    
    -- AI settings for this conversation
    ai_provider VARCHAR(50) DEFAULT 'claude-3',
    model VARCHAR(100) DEFAULT 'claude-3-opus-20240229',
    temperature DECIMAL(2,1) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1024,
    
    -- Statistics
    message_count INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    total_cost_cents INTEGER DEFAULT 0,
    
    -- Flags
    is_active BOOLEAN DEFAULT true,
    is_archived BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'error')),
    content TEXT NOT NULL,
    
    -- For structured responses
    structured_content JSONB,
    attachments JSONB DEFAULT '[]'::jsonb,
    
    -- AI metadata
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_cents INTEGER,
    completion_time_ms INTEGER,
    
    -- Message metadata
    message_type VARCHAR(50) DEFAULT 'text', -- text, code, image, file
    language VARCHAR(20), -- for code blocks
    
    -- Feedback
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    is_helpful BOOLEAN,
    
    -- Flags
    is_edited BOOLEAN DEFAULT false,
    is_deleted BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMPTZ
);

-- Chat templates/prompts table
CREATE TABLE IF NOT EXISTS chat_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    
    -- Template content
    system_prompt TEXT,
    initial_message TEXT,
    suggested_questions JSONB DEFAULT '[]'::jsonb,
    
    -- Settings
    default_model VARCHAR(100),
    default_temperature DECIMAL(2,1),
    context_variables JSONB DEFAULT '{}'::jsonb,
    
    -- Usage
    use_count INTEGER DEFAULT 0,
    avg_rating DECIMAL(2,1) DEFAULT 0.0,
    
    -- Flags
    is_public BOOLEAN DEFAULT false,
    is_featured BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Conversation context/memory table
CREATE TABLE IF NOT EXISTS chat_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
    
    -- Context data
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    context_type VARCHAR(50), -- user_info, project, preference, history
    
    -- Metadata
    importance INTEGER DEFAULT 5, -- 1-10 scale
    expires_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(conversation_id, key)
);

-- Token usage tracking
CREATE TABLE IF NOT EXISTS chat_token_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    
    -- Usage data
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    
    -- Counts
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    request_count INTEGER DEFAULT 0,
    
    -- Costs (in cents)
    prompt_cost_cents INTEGER DEFAULT 0,
    completion_cost_cents INTEGER DEFAULT 0,
    total_cost_cents INTEGER DEFAULT 0,
    
    -- Limits
    daily_limit INTEGER,
    monthly_limit INTEGER,
    
    UNIQUE(user_id, date, provider, model)
);

-- Create indexes for performance
CREATE INDEX idx_chat_conversations_user_id ON chat_conversations(user_id);
CREATE INDEX idx_chat_conversations_created_at ON chat_conversations(created_at DESC);
CREATE INDEX idx_chat_conversations_last_message ON chat_conversations(last_message_at DESC);

CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at DESC);
CREATE INDEX idx_chat_messages_role ON chat_messages(role);

CREATE INDEX idx_chat_context_conversation_id ON chat_context(conversation_id);
CREATE INDEX idx_chat_context_key ON chat_context(key);

CREATE INDEX idx_chat_token_usage_user_date ON chat_token_usage(user_id, date DESC);

-- Full text search on messages
CREATE INDEX idx_chat_messages_content_search ON chat_messages 
    USING GIN(to_tsvector('english', content));

-- Update triggers
CREATE OR REPLACE FUNCTION update_chat_conversation_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update conversation stats when new message added
    UPDATE chat_conversations
    SET 
        message_count = message_count + 1,
        last_message_at = NEW.created_at,
        total_tokens_used = total_tokens_used + COALESCE(NEW.tokens_used, 0),
        total_cost_cents = total_cost_cents + COALESCE(NEW.cost_cents, 0),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversation_on_message
    AFTER INSERT ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_conversation_stats();

-- Insert sample templates for roofing business
INSERT INTO chat_templates (name, description, category, system_prompt, initial_message, suggested_questions)
VALUES 
('Roofing Estimate Assistant', 
 'AI assistant specialized in creating roofing estimates',
 'business',
 'You are an expert roofing contractor assistant. Help create accurate estimates based on the information provided. Always ask for square footage, material type, and location. Provide detailed breakdowns.',
 'Hello! I''m your roofing estimate assistant. I can help you create professional estimates for your roofing projects. What type of roof are we estimating today?',
 '["What''s the square footage of the roof?", "What type of material do you recommend?", "How do I measure a roof?", "What''s included in a typical estimate?"]'::jsonb),

('Customer Service Bot',
 'Handle customer inquiries about roofing services',
 'support',
 'You are a friendly customer service representative for a roofing company. Answer questions about services, scheduling, warranties, and general roofing information. Be helpful and professional.',
 'Welcome! How can I help you with your roofing needs today?',
 '["Do you offer free estimates?", "What types of roofs do you install?", "How long does installation take?", "What warranty do you provide?"]'::jsonb),

('Technical Roofing Expert',
 'Deep technical knowledge about roofing materials and techniques',
 'technical',
 'You are a master roofer with 20+ years of experience. Provide detailed technical information about roofing materials, installation techniques, building codes, and best practices. Use industry terminology when appropriate.',
 'Hello! I''m here to help with any technical roofing questions. Whether it''s about materials, installation techniques, or building codes, I''ve got you covered.',
 '["What''s the difference between architectural and 3-tab shingles?", "How do you properly flash a chimney?", "What''s the best underlayment for my climate?", "How do I calculate ventilation requirements?"]'::jsonb);

-- Grant permissions
GRANT ALL ON chat_conversations TO postgres;
GRANT ALL ON chat_messages TO postgres;
GRANT ALL ON chat_templates TO postgres;
GRANT ALL ON chat_context TO postgres;
GRANT ALL ON chat_token_usage TO postgres;

-- Verify tables
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name LIKE 'chat_%'
AND table_schema = 'public'
ORDER BY table_name;