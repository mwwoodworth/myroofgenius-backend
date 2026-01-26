-- Migration: Revenue Engine Schema
-- Date: 2026-01-21
-- Description: Adds missing tables for AI Revenue Pipeline (revenue_leads, ai_email_queue, ai_nurture_sequences)

-- 1. Revenue Leads Table
CREATE TABLE IF NOT EXISTS revenue_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID, -- Link to original lead if applicable
    tenant_id UUID, -- For multi-tenancy support
    company_name TEXT,
    contact_name TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    location TEXT,
    stage TEXT DEFAULT 'new', -- new, contacted, interested, qualified, closed
    score DECIMAL(5,2) DEFAULT 0.0,
    value_estimate DECIMAL(12,2) DEFAULT 0.0,
    source TEXT,
    metadata JSONB DEFAULT '{}',
    last_contact TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_revenue_leads_stage ON revenue_leads(stage);
CREATE INDEX IF NOT EXISTS idx_revenue_leads_email ON revenue_leads(email);
CREATE INDEX IF NOT EXISTS idx_revenue_leads_score ON revenue_leads(score DESC);

-- 2. AI Email Queue Table
CREATE TABLE IF NOT EXISTS ai_email_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'queued', -- queued, sent, failed, cancelled
    metadata JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_queue_status_scheduled ON ai_email_queue(status, scheduled_for);

-- 3. AI Nurture Sequences Table
CREATE TABLE IF NOT EXISTS ai_nurture_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    name TEXT NOT NULL,
    sequence_name TEXT,
    sequence_type TEXT, -- reengagement, upsell, referral
    target_segment TEXT,
    configuration JSONB DEFAULT '{}', -- stores touchpoints, delays, etc.
    is_active BOOLEAN DEFAULT TRUE,
    active TEXT DEFAULT 'active', -- Legacy/Dual compatibility
    status TEXT DEFAULT 'active',
    trigger_type TEXT,
    touchpoint_count INTEGER DEFAULT 0,
    days_duration INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nurture_sequences_type ON ai_nurture_sequences(sequence_type);

-- 4. Triggers for Updated At
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_revenue_leads_modtime ON revenue_leads;
CREATE TRIGGER update_revenue_leads_modtime
    BEFORE UPDATE ON revenue_leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ai_email_queue_modtime ON ai_email_queue;
CREATE TRIGGER update_ai_email_queue_modtime
    BEFORE UPDATE ON ai_email_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ai_nurture_sequences_modtime ON ai_nurture_sequences;
CREATE TRIGGER update_ai_nurture_sequences_modtime
    BEFORE UPDATE ON ai_nurture_sequences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
