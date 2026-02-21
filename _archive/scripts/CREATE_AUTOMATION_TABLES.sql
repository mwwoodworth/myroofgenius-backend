-- =====================================================
-- MyRoofGenius AI Automation Database Tables
-- Version: 1.0.0
-- Date: 2025-08-21
-- Description: Creates tables required for AI automation system
-- =====================================================

-- 1. SCHEDULED EMAILS TABLE
-- Manages automated email sequences and campaigns
CREATE TABLE IF NOT EXISTS scheduled_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    sequence_type VARCHAR(50) NOT NULL CHECK (sequence_type IN (
        'welcome',
        'abandoned_cart',
        'win_back',
        'trial_ending',
        'nurture_leads',
        'upsell_sequence'
    )),
    template VARCHAR(50) NOT NULL,
    subject TEXT NOT NULL,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    personalization_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for scheduled_emails
CREATE INDEX idx_scheduled_emails_user_id ON scheduled_emails(user_id);
CREATE INDEX idx_scheduled_emails_status ON scheduled_emails(status);
CREATE INDEX idx_scheduled_emails_scheduled_for ON scheduled_emails(scheduled_for);
CREATE INDEX idx_scheduled_emails_sequence_type ON scheduled_emails(sequence_type);

-- 2. EXPERIMENT ASSIGNMENTS TABLE
-- Tracks A/B test assignments for conversion optimization
CREATE TABLE IF NOT EXISTS experiment_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visitor_id VARCHAR(100) NOT NULL,
    experiment_name VARCHAR(50) NOT NULL,
    variant_id VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure each visitor gets only one variant per experiment
    UNIQUE(visitor_id, experiment_name)
);

-- Indexes for experiment_assignments
CREATE INDEX idx_experiment_assignments_visitor ON experiment_assignments(visitor_id);
CREATE INDEX idx_experiment_assignments_experiment ON experiment_assignments(experiment_name);
CREATE INDEX idx_experiment_assignments_variant ON experiment_assignments(variant_id);

-- 3. CONVERSIONS TABLE
-- Tracks conversion events for A/B testing and analytics
CREATE TABLE IF NOT EXISTS conversions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visitor_id VARCHAR(100) NOT NULL,
    experiment_name VARCHAR(50),
    variant_id VARCHAR(50),
    conversion_type VARCHAR(20) CHECK (conversion_type IN (
        'signup',
        'purchase',
        'trial',
        'demo',
        'lead',
        'upgrade'
    )),
    conversion_value DECIMAL(10, 2),
    converted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for conversions
CREATE INDEX idx_conversions_visitor ON conversions(visitor_id);
CREATE INDEX idx_conversions_experiment ON conversions(experiment_name);
CREATE INDEX idx_conversions_variant ON conversions(variant_id);
CREATE INDEX idx_conversions_type ON conversions(conversion_type);
CREATE INDEX idx_conversions_date ON conversions(converted_at);

-- 4. OPTIMIZATION EVENTS TABLE
-- Tracks visitor behavior for conversion optimization
CREATE TABLE IF NOT EXISTS optimization_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visitor_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'page_view',
        'form_interaction',
        'exit_intent',
        'scroll_depth',
        'time_on_page',
        'click',
        'hover',
        'video_play',
        'download',
        'share'
    )),
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for optimization_events
CREATE INDEX idx_optimization_events_visitor ON optimization_events(visitor_id);
CREATE INDEX idx_optimization_events_type ON optimization_events(event_type);
CREATE INDEX idx_optimization_events_date ON optimization_events(created_at);

-- 5. EMAIL CAMPAIGN METRICS TABLE
-- Tracks email campaign performance
CREATE TABLE IF NOT EXISTS email_campaign_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id VARCHAR(100) NOT NULL,
    sequence_type VARCHAR(50) NOT NULL,
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    conversion_count INTEGER DEFAULT 0,
    unsubscribe_count INTEGER DEFAULT 0,
    revenue_generated DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for email_campaign_metrics
CREATE INDEX idx_email_campaign_metrics_campaign ON email_campaign_metrics(campaign_id);
CREATE INDEX idx_email_campaign_metrics_sequence ON email_campaign_metrics(sequence_type);

-- 6. VISITOR PROFILES TABLE
-- Stores visitor behavior profiles for personalization
CREATE TABLE IF NOT EXISTS visitor_profiles (
    visitor_id VARCHAR(100) PRIMARY KEY,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_visits INTEGER DEFAULT 1,
    total_page_views INTEGER DEFAULT 0,
    average_session_duration INTEGER DEFAULT 0, -- in seconds
    behavior_score DECIMAL(5, 2) DEFAULT 0,
    intent_score DECIMAL(5, 2) DEFAULT 0,
    engagement_score DECIMAL(5, 2) DEFAULT 0,
    persona_type VARCHAR(50),
    preferences JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for visitor_profiles
CREATE INDEX idx_visitor_profiles_last_seen ON visitor_profiles(last_seen);
CREATE INDEX idx_visitor_profiles_persona ON visitor_profiles(persona_type);
CREATE INDEX idx_visitor_profiles_behavior_score ON visitor_profiles(behavior_score);

-- 7. REVENUE METRICS TABLE
-- Tracks real-time revenue metrics
CREATE TABLE IF NOT EXISTS revenue_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL,
    daily_revenue DECIMAL(10, 2) DEFAULT 0,
    monthly_revenue DECIMAL(10, 2) DEFAULT 0,
    yearly_revenue DECIMAL(10, 2) DEFAULT 0,
    mrr DECIMAL(10, 2) DEFAULT 0,
    arr DECIMAL(10, 2) DEFAULT 0,
    active_subscriptions INTEGER DEFAULT 0,
    new_customers INTEGER DEFAULT 0,
    churned_customers INTEGER DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0,
    average_order_value DECIMAL(10, 2) DEFAULT 0,
    customer_lifetime_value DECIMAL(10, 2) DEFAULT 0,
    churn_rate DECIMAL(5, 2) DEFAULT 0,
    growth_rate DECIMAL(5, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(metric_date)
);

-- Indexes for revenue_metrics
CREATE INDEX idx_revenue_metrics_date ON revenue_metrics(metric_date);

-- 8. AI RECOMMENDATIONS TABLE
-- Stores AI-generated optimization recommendations
CREATE TABLE IF NOT EXISTS ai_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    impact_score DECIMAL(5, 2) DEFAULT 0,
    confidence_score DECIMAL(5, 2) DEFAULT 0,
    estimated_revenue_impact DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending',
        'approved',
        'implemented',
        'rejected',
        'archived'
    )),
    auto_implement BOOLEAN DEFAULT FALSE,
    implemented_at TIMESTAMP WITH TIME ZONE,
    results JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for ai_recommendations
CREATE INDEX idx_ai_recommendations_type ON ai_recommendations(recommendation_type);
CREATE INDEX idx_ai_recommendations_status ON ai_recommendations(status);
CREATE INDEX idx_ai_recommendations_impact ON ai_recommendations(impact_score);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE scheduled_emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE experiment_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversions ENABLE ROW LEVEL SECURITY;
ALTER TABLE optimization_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_campaign_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE visitor_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE revenue_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_recommendations ENABLE ROW LEVEL SECURITY;

-- Create policies for scheduled_emails
CREATE POLICY "Users can view their own scheduled emails"
    ON scheduled_emails FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all scheduled emails"
    ON scheduled_emails FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Create policies for public tables (accessible by service role only)
CREATE POLICY "Service role full access to experiments"
    ON experiment_assignments FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to conversions"
    ON conversions FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to optimization events"
    ON optimization_events FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to email metrics"
    ON email_campaign_metrics FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to visitor profiles"
    ON visitor_profiles FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to revenue metrics"
    ON revenue_metrics FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to AI recommendations"
    ON ai_recommendations FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_scheduled_emails_updated_at
    BEFORE UPDATE ON scheduled_emails
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_campaign_metrics_updated_at
    BEFORE UPDATE ON email_campaign_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_visitor_profiles_updated_at
    BEFORE UPDATE ON visitor_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_recommendations_updated_at
    BEFORE UPDATE ON ai_recommendations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- INITIAL DATA SEEDING
-- =====================================================

-- Insert initial revenue metrics for today
INSERT INTO revenue_metrics (
    metric_date,
    daily_revenue,
    monthly_revenue,
    yearly_revenue,
    mrr,
    arr,
    active_subscriptions,
    conversion_rate,
    average_order_value,
    customer_lifetime_value,
    churn_rate,
    growth_rate
) VALUES (
    CURRENT_DATE,
    0,
    0,
    0,
    0,
    0,
    0,
    2.0,  -- 2% baseline conversion rate
    97.00,  -- $97 baseline AOV
    500.00,  -- $500 baseline CLV
    5.0,  -- 5% baseline churn
    0.0   -- 0% initial growth
) ON CONFLICT (metric_date) DO NOTHING;

-- =====================================================
-- GRANTS
-- =====================================================

-- Grant usage on all tables to authenticated users (with RLS)
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Grant full access to service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- =====================================================
-- VERIFICATION
-- =====================================================

-- List all created tables
SELECT table_name, 
       pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) as size
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'scheduled_emails',
    'experiment_assignments',
    'conversions',
    'optimization_events',
    'email_campaign_metrics',
    'visitor_profiles',
    'revenue_metrics',
    'ai_recommendations'
)
ORDER BY table_name;

-- Count policies
SELECT COUNT(*) as total_policies 
FROM pg_policies 
WHERE tablename IN (
    'scheduled_emails',
    'experiment_assignments',
    'conversions',
    'optimization_events',
    'email_campaign_metrics',
    'visitor_profiles',
    'revenue_metrics',
    'ai_recommendations'
);

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ All automation tables created successfully!';
    RAISE NOTICE '📊 8 tables created with indexes and RLS policies';
    RAISE NOTICE '🚀 System ready for AI automation deployment';
END $$;