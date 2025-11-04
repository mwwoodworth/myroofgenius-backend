-- Marketing Automation Database Schema
-- Tasks 71-80: Complete Marketing System

-- Task 71: Campaign Management
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(50) DEFAULT 'email',
    target_audience TEXT,
    budget DECIMAL(10,2),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    objectives JSONB DEFAULT '[]'::jsonb,
    channels JSONB DEFAULT '["email"]'::jsonb,
    content JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'draft',
    performance_metrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Task 72: Email Marketing
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    html_content TEXT NOT NULL,
    text_content TEXT,
    template_type VARCHAR(50) DEFAULT 'marketing',
    variables JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    template_id UUID REFERENCES email_templates(id),
    recipient_list_id UUID,
    recipients JSONB,
    subject_override VARCHAR(500),
    send_time TIMESTAMP,
    personalization JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES email_campaigns(id),
    recipient VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'sent',
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    bounced BOOLEAN DEFAULT false,
    bounce_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Task 73: Social Media Management
CREATE TABLE IF NOT EXISTS social_media_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    platforms JSONB DEFAULT '["twitter"]'::jsonb,
    media_urls JSONB DEFAULT '[]'::jsonb,
    scheduled_time TIMESTAMP,
    hashtags JSONB DEFAULT '[]'::jsonb,
    campaign_id UUID REFERENCES marketing_campaigns(id),
    status VARCHAR(50) DEFAULT 'draft',
    engagement_metrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Task 74: Lead Nurturing
CREATE TABLE IF NOT EXISTS nurture_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    trigger_event VARCHAR(100) NOT NULL,
    steps JSONB NOT NULL,
    target_segment VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nurture_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES nurture_workflows(id),
    lead_id UUID,
    current_step INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Task 75: Content Marketing
CREATE TABLE IF NOT EXISTS content_marketing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) DEFAULT 'blog',
    content_body TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    seo_keywords JSONB DEFAULT '[]'::jsonb,
    publish_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft',
    views INTEGER DEFAULT 0,
    engagement_metrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Task 76: Marketing Analytics (uses views on existing tables)
CREATE VIEW IF NOT EXISTS marketing_performance AS
SELECT
    mc.id as campaign_id,
    mc.name as campaign_name,
    mc.campaign_type,
    mc.budget,
    COUNT(DISTINCT et.recipient) as total_reach,
    COUNT(CASE WHEN et.opened_at IS NOT NULL THEN 1 END) as opens,
    COUNT(CASE WHEN et.clicked_at IS NOT NULL THEN 1 END) as clicks,
    mc.created_at
FROM marketing_campaigns mc
LEFT JOIN email_tracking et ON et.campaign_id = mc.id
GROUP BY mc.id;

-- Task 77: Customer Segmentation
CREATE TABLE IF NOT EXISTS customer_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    criteria JSONB NOT NULL,
    segment_type VARCHAR(50) DEFAULT 'behavioral',
    is_dynamic BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS segment_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_id UUID REFERENCES customer_segments(id),
    customer_id UUID,
    added_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Task 78: A/B Testing
CREATE TABLE IF NOT EXISTS ab_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    test_type VARCHAR(50) DEFAULT 'email',
    control_variant JSONB NOT NULL,
    test_variants JSONB NOT NULL,
    success_metric VARCHAR(100) NOT NULL,
    sample_size INTEGER,
    duration_days INTEGER DEFAULT 14,
    status VARCHAR(50) DEFAULT 'draft',
    results JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ab_test_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID REFERENCES ab_tests(id),
    user_id VARCHAR(255) NOT NULL,
    variant_name VARCHAR(100) NOT NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    converted BOOLEAN DEFAULT false,
    converted_at TIMESTAMP
);

-- Task 79: Marketing Automation
CREATE TABLE IF NOT EXISTS marketing_automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(100) NOT NULL,
    trigger_config JSONB NOT NULL,
    actions JSONB NOT NULL,
    conditions JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS automation_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    automation_id UUID REFERENCES marketing_automations(id),
    trigger_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Task 80: Landing Pages
CREATE TABLE IF NOT EXISTS landing_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    template_id UUID,
    content_blocks JSONB DEFAULT '[]'::jsonb,
    meta_tags JSONB DEFAULT '{}'::jsonb,
    conversion_goal VARCHAR(100) DEFAULT 'form_submission',
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS landing_page_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID REFERENCES landing_pages(id),
    visitor_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    referrer TEXT,
    device_type VARCHAR(50),
    browser VARCHAR(100),
    time_on_page INTEGER,
    converted BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_marketing_campaigns_status ON marketing_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_email_tracking_campaign ON email_tracking(campaign_id);
CREATE INDEX IF NOT EXISTS idx_social_posts_scheduled ON social_media_posts(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_content_publish_date ON content_marketing(publish_date);
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_automations_active ON marketing_automations(is_active);
CREATE INDEX IF NOT EXISTS idx_landing_pages_slug ON landing_pages(slug);

COMMENT ON TABLE marketing_campaigns IS 'Task 71: Campaign Management';
COMMENT ON TABLE email_templates IS 'Task 72: Email Marketing Templates';
COMMENT ON TABLE email_campaigns IS 'Task 72: Email Marketing Campaigns';
COMMENT ON TABLE social_media_posts IS 'Task 73: Social Media Management';
COMMENT ON TABLE nurture_workflows IS 'Task 74: Lead Nurturing Workflows';
COMMENT ON TABLE content_marketing IS 'Task 75: Content Marketing';
COMMENT ON TABLE customer_segments IS 'Task 77: Customer Segmentation';
COMMENT ON TABLE ab_tests IS 'Task 78: A/B Testing';
COMMENT ON TABLE marketing_automations IS 'Task 79: Marketing Automation';
COMMENT ON TABLE landing_pages IS 'Task 80: Landing Pages';