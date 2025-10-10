-- Run all pending migrations and ensure database is fully synced
-- This ensures all tables exist and are properly configured

-- Ensure all core tables exist
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL,
    category VARCHAR(100),
    stripe_product_id VARCHAR(255),
    stripe_price_id VARCHAR(255),
    image_url TEXT,
    is_featured BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID,
    plan_name VARCHAR(100),
    price_cents INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    stripe_subscription_id VARCHAR(255),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE,
    customer_id UUID,
    status VARCHAR(50) DEFAULT 'pending',
    subtotal_cents INTEGER DEFAULT 0,
    tax_cents INTEGER DEFAULT 0,
    shipping_cents INTEGER DEFAULT 0,
    total_cents INTEGER NOT NULL,
    stripe_payment_intent_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shopping_carts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    customer_id UUID,
    status VARCHAR(50) DEFAULT 'active',
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '7 days',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id UUID REFERENCES shopping_carts(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    quantity INTEGER DEFAULT 1,
    price_cents INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    company VARCHAR(255),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    score INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS automations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_type VARCHAR(100),
    action_type VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    schedule VARCHAR(100),
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    total_runs INTEGER DEFAULT 0,
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS automation_runs (
    id SERIAL PRIMARY KEY,
    automation_id INTEGER REFERENCES automations(id),
    status VARCHAR(50),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error TEXT,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS ai_agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    capabilities JSONB,
    config JSONB,
    last_active_at TIMESTAMP,
    total_tasks_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE,
    agent_id INTEGER REFERENCES ai_agents(id),
    type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS centerpoint_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(100),
    status VARCHAR(50),
    records_processed INTEGER DEFAULT 0,
    errors JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_featured ON products(is_featured);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source);
CREATE INDEX IF NOT EXISTS idx_automations_active ON automations(is_active);
CREATE INDEX IF NOT EXISTS idx_ai_agents_status ON ai_agents(status);

-- Insert sample products for revenue generation
INSERT INTO products (name, description, price_cents, category, is_featured)
SELECT * FROM (VALUES
    ('AI Roof Estimator - Basic', 'Generate accurate estimates with AI', 4999, 'software', true),
    ('AI Roof Estimator - Pro', 'Advanced estimation with photo analysis', 9999, 'software', true),
    ('Contractor Dashboard', 'Complete business management system', 14999, 'software', true),
    ('Lead Generation Pack', '100 qualified roofing leads', 2500, 'leads', false),
    ('Marketing Automation', 'Automated marketing campaigns', 7999, 'marketing', false)
) AS v(name, description, price_cents, category, is_featured)
WHERE NOT EXISTS (
    SELECT 1 FROM products WHERE name = v.name
);

-- Insert sample automations
INSERT INTO automations (name, description, trigger_type, action_type, is_active)
SELECT * FROM (VALUES
    ('Lead Follow-up', 'Automatically follow up with new leads', 'new_lead', 'send_email', true),
    ('Invoice Reminder', 'Send payment reminders', 'invoice_overdue', 'send_reminder', true),
    ('Customer Welcome', 'Welcome new customers', 'new_customer', 'send_welcome', true)
) AS v(name, description, trigger_type, action_type, is_active)
WHERE NOT EXISTS (
    SELECT 1 FROM automations WHERE name = v.name
);

-- Insert AI agents
INSERT INTO ai_agents (name, type, status, capabilities)
SELECT * FROM (VALUES
    ('Revenue Optimizer', 'revenue', 'active', '["pricing", "upsell", "retention"]'::jsonb),
    ('Lead Qualifier', 'sales', 'active', '["scoring", "routing", "nurture"]'::jsonb),
    ('Customer Service', 'support', 'active', '["chat", "tickets", "escalation"]'::jsonb),
    ('Marketing Assistant', 'marketing', 'active', '["content", "campaigns", "analytics"]'::jsonb),
    ('Operations Manager', 'operations', 'active', '["scheduling", "dispatch", "inventory"]'::jsonb)
) AS v(name, type, status, capabilities)
WHERE NOT EXISTS (
    SELECT 1 FROM ai_agents WHERE name = v.name
);

-- Create revenue analytics view
CREATE OR REPLACE VIEW revenue_analytics AS
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(DISTINCT CASE WHEN status = 'completed' THEN id END) as completed_orders,
    SUM(CASE WHEN status = 'completed' THEN total_cents END) / 100.0 as revenue,
    COUNT(DISTINCT CASE WHEN status = 'pending' THEN id END) as pending_orders,
    SUM(CASE WHEN status = 'pending' THEN total_cents END) / 100.0 as potential_revenue
FROM orders
GROUP BY DATE_TRUNC('month', created_at);

-- Create customer analytics view
CREATE OR REPLACE VIEW customer_analytics AS
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as new_customers,
    COUNT(CASE WHEN external_id LIKE 'CP-%' THEN 1 END) as centerpoint_customers,
    AVG(CASE WHEN total_value_cents > 0 THEN total_value_cents END) / 100.0 as avg_customer_value
FROM customers
GROUP BY DATE_TRUNC('month', created_at);

-- Summary of migration
SELECT 
    'Database Migration Complete' as status,
    (SELECT COUNT(*) FROM products) as products_count,
    (SELECT COUNT(*) FROM automations) as automations_count,
    (SELECT COUNT(*) FROM ai_agents) as agents_count,
    (SELECT COUNT(*) FROM customers WHERE external_id LIKE 'CP-%') as centerpoint_customers;
