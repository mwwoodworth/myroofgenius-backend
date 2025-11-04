-- Job notifications management tables
-- Handles notification system for job-related events

-- Create job_notifications table
CREATE TABLE IF NOT EXISTS job_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    channels JSONB DEFAULT '["in_app"]',
    recipient_ids JSONB DEFAULT '[]',
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    read_at TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create user notification preferences table
CREATE TABLE IF NOT EXISTS user_notification_preferences (
    user_id UUID PRIMARY KEY,
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT TRUE,
    slack_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start VARCHAR(5), -- HH:MM format
    quiet_hours_end VARCHAR(5),   -- HH:MM format
    notification_types JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create notification rules table for automated notifications
CREATE TABLE IF NOT EXISTS job_notification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    template TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    channels JSONB DEFAULT '["in_app"]',
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(job_id, event_type)
);

-- Create notification delivery log
CREATE TABLE IF NOT EXISTS notification_delivery_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL,
    channel VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL, -- pending, sent, failed, bounced
    error_message TEXT,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (notification_id) REFERENCES job_notifications(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_notifications_job_id ON job_notifications(job_id);
CREATE INDEX IF NOT EXISTS idx_job_notifications_type ON job_notifications(type);
CREATE INDEX IF NOT EXISTS idx_job_notifications_priority ON job_notifications(priority);
CREATE INDEX IF NOT EXISTS idx_job_notifications_is_read ON job_notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_job_notifications_created_at ON job_notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_notifications_created_by ON job_notifications(created_by);

CREATE INDEX IF NOT EXISTS idx_notification_rules_job_id ON job_notification_rules(job_id);
CREATE INDEX IF NOT EXISTS idx_notification_rules_event_type ON job_notification_rules(event_type);
CREATE INDEX IF NOT EXISTS idx_notification_rules_is_active ON job_notification_rules(is_active);

CREATE INDEX IF NOT EXISTS idx_delivery_log_notification_id ON notification_delivery_log(notification_id);
CREATE INDEX IF NOT EXISTS idx_delivery_log_status ON notification_delivery_log(status);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON job_notifications TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_notification_preferences TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON job_notification_rules TO authenticated;
GRANT SELECT, INSERT ON notification_delivery_log TO authenticated;