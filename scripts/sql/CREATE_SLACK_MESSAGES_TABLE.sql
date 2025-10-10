-- Create table for storing Slack messages and commands
CREATE TABLE IF NOT EXISTS slack_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50) NOT NULL,  -- Slack user ID
    channel_id VARCHAR(50) NOT NULL,  -- Slack channel ID
    text TEXT NOT NULL,  -- Message content
    timestamp VARCHAR(50),  -- Slack message timestamp
    thread_ts VARCHAR(50),  -- Thread timestamp if in thread
    raw_event JSONB,  -- Full Slack event data
    processed BOOLEAN DEFAULT FALSE,
    response JSONB,  -- ClaudeOS response
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_slack_messages_user_id ON slack_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_slack_messages_channel_id ON slack_messages(channel_id);
CREATE INDEX IF NOT EXISTS idx_slack_messages_timestamp ON slack_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_slack_messages_processed ON slack_messages(processed);
CREATE INDEX IF NOT EXISTS idx_slack_messages_created_at ON slack_messages(created_at DESC);

-- Create table for Slack command queue
CREATE TABLE IF NOT EXISTS slack_command_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    command TEXT NOT NULL,
    context JSONB NOT NULL,
    routing JSONB,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, urgent
    assigned_agents TEXT[],
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for command queue
CREATE INDEX IF NOT EXISTS idx_slack_command_queue_status ON slack_command_queue(status);
CREATE INDEX IF NOT EXISTS idx_slack_command_queue_priority ON slack_command_queue(priority);
CREATE INDEX IF NOT EXISTS idx_slack_command_queue_created_at ON slack_command_queue(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_slack_messages_updated_at BEFORE UPDATE ON slack_messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_slack_command_queue_updated_at BEFORE UPDATE ON slack_command_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();