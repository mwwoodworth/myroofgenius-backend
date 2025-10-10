-- Fix revenue tables with proper PostgreSQL syntax

-- AI Estimates table
CREATE TABLE IF NOT EXISTS ai_estimates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estimate_id VARCHAR(50) UNIQUE NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    property_address TEXT,
    total_cost_cents INTEGER NOT NULL,
    material_cost_cents INTEGER,
    labor_cost_cents INTEGER,
    timeline_days INTEGER,
    confidence_score DECIMAL(3,2),
    details JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    converted_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_estimate_email ON ai_estimates(customer_email);
CREATE INDEX IF NOT EXISTS idx_estimate_status ON ai_estimates(status);

-- Roof analyses from photo AI
CREATE TABLE IF NOT EXISTS roof_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_email VARCHAR(255),
    photo_data TEXT,
    ai_analysis JSONB,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analysis_email ON roof_analyses(customer_email);

-- Checkout sessions
CREATE TABLE IF NOT EXISTS checkout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    price_id VARCHAR(255),
    amount_cents INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_checkout_status ON checkout_sessions(status);
CREATE INDEX IF NOT EXISTS idx_checkout_email ON checkout_sessions(customer_email);

-- Enhanced leads table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id VARCHAR(50) UNIQUE,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    company VARCHAR(255),
    score INTEGER DEFAULT 50,
    segment VARCHAR(20),
    urgency VARCHAR(50),
    source VARCHAR(100),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    nurture_sequence VARCHAR(50),
    nurture_started_at TIMESTAMP,
    converted BOOLEAN DEFAULT false,
    converted_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lead_score ON leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_lead_segment ON leads(segment);
CREATE INDEX IF NOT EXISTS idx_lead_email ON leads(email);

-- Email queue
CREATE TABLE IF NOT EXISTS email_queue (
    id SERIAL PRIMARY KEY,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    template VARCHAR(100),
    data JSONB,
    scheduled_for TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_scheduled ON email_queue(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_email_status ON email_queue(status);

-- Customer LTV
CREATE TABLE IF NOT EXISTS customer_ltv (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_email VARCHAR(255) UNIQUE NOT NULL,
    total_revenue_cents INTEGER DEFAULT 0,
    order_count INTEGER DEFAULT 0,
    subscription_months INTEGER DEFAULT 0,
    avg_order_value_cents INTEGER DEFAULT 0,
    predicted_ltv_cents INTEGER DEFAULT 0,
    churn_risk_score DECIMAL(3,2),
    last_purchase_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ltv_email ON customer_ltv(customer_email);
CREATE INDEX IF NOT EXISTS idx_ltv_value ON customer_ltv(total_revenue_cents DESC);

-- A/B Tests
CREATE TABLE IF NOT EXISTS ab_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_name VARCHAR(100) NOT NULL,
    variant VARCHAR(10),
    customer_email VARCHAR(255),
    converted BOOLEAN DEFAULT false,
    value_cents INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ab_test ON ab_tests(test_name, variant);

-- Add missing columns to revenue_tracking
ALTER TABLE revenue_tracking ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255);
ALTER TABLE revenue_tracking ADD COLUMN IF NOT EXISTS customer_id VARCHAR(255);
ALTER TABLE revenue_tracking ADD COLUMN IF NOT EXISTS product_name VARCHAR(255);

-- Summary
SELECT 
    'Revenue Pipeline Ready' as status,
    (SELECT COUNT(*) FROM ai_estimates) as estimates,
    (SELECT COUNT(*) FROM leads) as leads,
    (SELECT COUNT(*) FROM products WHERE stripe_price_id IS NOT NULL) as products_ready;
