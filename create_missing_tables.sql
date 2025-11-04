-- Create Missing Business Tables for AI OS
-- These tables are required by the AI agents to function properly

-- User Activity Tracking
CREATE TABLE IF NOT EXISTS user_activity_summary (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES customers(id),
    last_active TIMESTAMP DEFAULT NOW(),
    activity_score INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    total_duration_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity_summary(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_score ON user_activity_summary(activity_score);

-- User Funnel Tracking
CREATE TABLE IF NOT EXISTS user_funnel_tracking (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES customers(id),
    funnel_stage VARCHAR(50) NOT NULL,
    entered_at TIMESTAMP DEFAULT NOW(),
    exited_at TIMESTAMP,
    time_in_stage INTEGER, -- seconds
    conversion BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_funnel_user ON user_funnel_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_funnel_stage ON user_funnel_tracking(funnel_stage);
CREATE INDEX IF NOT EXISTS idx_funnel_created ON user_funnel_tracking(created_at);

-- Materials/Inventory
CREATE TABLE IF NOT EXISTS materials (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE,
    category VARCHAR(100),
    quantity INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 10,
    unit_cost DECIMAL(10,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    supplier VARCHAR(255),
    lead_time_days INTEGER DEFAULT 7,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_materials_sku ON materials(sku);
CREATE INDEX IF NOT EXISTS idx_materials_category ON materials(category);

-- Shopping Carts for Revenue Tracking
CREATE TABLE IF NOT EXISTS shopping_carts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    status VARCHAR(50) DEFAULT 'active', -- active, abandoned, converted
    items JSONB DEFAULT '[]',
    total_amount DECIMAL(10,2) DEFAULT 0,
    abandoned_at TIMESTAMP,
    converted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_carts_customer ON shopping_carts(customer_id);
CREATE INDEX IF NOT EXISTS idx_carts_status ON shopping_carts(status);

-- Support Tickets
CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    subject VARCHAR(255),
    description TEXT,
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, resolved, closed
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    assigned_to VARCHAR(255),
    resolved_at TIMESTAMP,
    resolution TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tickets_customer ON support_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status);

-- Subscriptions for MRR Tracking
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    plan_name VARCHAR(100),
    amount DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'active', -- active, paused, cancelled, expired
    billing_cycle VARCHAR(20) DEFAULT 'monthly', -- monthly, yearly
    next_billing_date DATE,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_customer ON subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

-- Leads for Conversion Tracking
CREATE TABLE IF NOT EXISTS leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new', -- new, contacted, qualified, converted, lost
    score INTEGER DEFAULT 0,
    assigned_to VARCHAR(255),
    converted_at TIMESTAMP,
    customer_id UUID REFERENCES customers(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);

-- User Sessions for Engagement Tracking
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES customers(id),
    session_date DATE DEFAULT CURRENT_DATE,
    duration_seconds INTEGER DEFAULT 0,
    page_views INTEGER DEFAULT 0,
    actions_taken JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON user_sessions(session_date);

-- User Activity Log
CREATE TABLE IF NOT EXISTS user_activity (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES customers(id),
    activity_date DATE DEFAULT CURRENT_DATE,
    activity_type VARCHAR(100),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_date ON user_activity(activity_date);

-- Fix CenterPoint Data Table
ALTER TABLE centerpoint_data 
ADD COLUMN IF NOT EXISTS address VARCHAR(500);

ALTER TABLE centerpoint_data
ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255);

ALTER TABLE centerpoint_data
ADD COLUMN IF NOT EXISTS phone VARCHAR(50);

ALTER TABLE centerpoint_data
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Fix Jobs Table for Scheduling
ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS estimated_hours DECIMAL(5,2) DEFAULT 0;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS crew_size INTEGER DEFAULT 2;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS scheduled_date DATE;

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS location GEOGRAPHY(POINT);

-- Fix Invoices Table for Revenue
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS amount DECIMAL(10,2) DEFAULT 0;

ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP;

-- Add sample data for testing
INSERT INTO materials (name, sku, category, quantity, reorder_point, unit_cost) VALUES
('Roofing Shingles - Asphalt', 'SHNG-001', 'Roofing', 500, 100, 45.00),
('Roofing Nails - 1.25"', 'NAIL-001', 'Fasteners', 10000, 2000, 0.05),
('Tar Paper - 30lb', 'TAR-001', 'Underlayment', 200, 50, 25.00),
('Ridge Vents', 'VENT-001', 'Ventilation', 100, 25, 35.00),
('Flashing - Aluminum', 'FLASH-001', 'Flashing', 300, 75, 15.00)
ON CONFLICT (sku) DO NOTHING;

-- Create sample subscriptions for MRR
INSERT INTO subscriptions (customer_id, plan_name, amount, status, billing_cycle, next_billing_date)
SELECT 
    id,
    CASE (RANDOM() * 3)::INT
        WHEN 0 THEN 'Basic'
        WHEN 1 THEN 'Professional'
        ELSE 'Enterprise'
    END,
    CASE (RANDOM() * 3)::INT
        WHEN 0 THEN 97.00
        WHEN 1 THEN 197.00
        ELSE 497.00
    END,
    'active',
    'monthly',
    CURRENT_DATE + INTERVAL '30 days'
FROM customers
LIMIT 10
ON CONFLICT DO NOTHING;

-- Create sample leads
INSERT INTO leads (name, email, phone, source, status, score)
VALUES 
('John Smith', 'john.smith@example.com', '512-555-0101', 'Website', 'new', 75),
('Jane Doe', 'jane.doe@example.com', '512-555-0102', 'Google Ads', 'qualified', 85),
('Bob Wilson', 'bob.wilson@example.com', '512-555-0103', 'Referral', 'contacted', 60),
('Alice Brown', 'alice.brown@example.com', '512-555-0104', 'Facebook', 'new', 50),
('Charlie Davis', 'charlie.davis@example.com', '512-555-0105', 'Direct', 'converted', 95)
ON CONFLICT DO NOTHING;

-- Update invoice amounts
UPDATE invoices 
SET amount = (total * 100)::DECIMAL(10,2)
WHERE amount IS NULL OR amount = 0;

-- Update job scheduling data
UPDATE jobs
SET 
    estimated_hours = CASE 
        WHEN estimated_costs > 10000 THEN 16
        WHEN estimated_costs > 5000 THEN 8
        ELSE 4
    END,
    scheduled_date = created_at::DATE + INTERVAL '7 days',
    crew_size = CASE 
        WHEN estimated_costs > 10000 THEN 4
        WHEN estimated_costs > 5000 THEN 3
        ELSE 2
    END
WHERE estimated_hours IS NULL OR estimated_hours = 0;

-- Success message
SELECT 'All missing tables created and sample data inserted!' as status;