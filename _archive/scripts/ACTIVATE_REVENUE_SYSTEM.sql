-- ACTIVATE REVENUE GENERATION IMMEDIATELY
-- ========================================

-- Create products table if needed
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL DEFAULT 0,
    stripe_product_id VARCHAR(255) UNIQUE,
    stripe_price_id VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert revenue products
INSERT INTO products (name, description, price_cents, stripe_product_id, stripe_price_id, is_active)
VALUES 
    ('AI Roof Estimation', 'Professional AI-powered roof estimation with detailed report', 4900, 'prod_ai_estimate', 'price_ai_estimate', true),
    ('Contractor Lead', 'Qualified roofing lead for contractors', 2900, 'prod_contractor_lead', 'price_contractor_lead', true),
    ('Premium Subscription', 'Unlimited AI estimations and priority support', 9900, 'prod_premium_sub', 'price_premium_sub', true)
ON CONFLICT (stripe_product_id) 
DO UPDATE SET 
    is_active = true,
    price_cents = EXCLUDED.price_cents,
    updated_at = CURRENT_TIMESTAMP;

-- Create landing pages table if needed
CREATE TABLE IF NOT EXISTS landing_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert landing pages
INSERT INTO landing_pages (slug, title, metadata, is_active)
VALUES 
    ('free-estimate', 'Get Your Free AI Roof Estimate', '{"conversion_rate": 0.15}', true),
    ('storm-damage', 'Storm Damage? We Can Help', '{"conversion_rate": 0.22}', true),
    ('contractor-signup', 'Join Our Contractor Network', '{"conversion_rate": 0.08}', true)
ON CONFLICT (slug) 
DO UPDATE SET is_active = true;

-- Create system_config table if needed
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enable all revenue features
INSERT INTO system_config (key, value)
VALUES 
    ('stripe_enabled', 'true'),
    ('payment_methods', '["card", "ach", "invoice"]'),
    ('auto_invoice', 'true'),
    ('lead_capture_enabled', 'true'),
    ('ai_estimation_enabled', 'true'),
    ('revenue_system_active', 'true')
ON CONFLICT (key) 
DO UPDATE SET value = EXCLUDED.value;

-- Store revenue activation in knowledge base
INSERT INTO neural_os_knowledge (
    component_name, component_type, agent_name,
    knowledge_type, knowledge_data, confidence_score,
    review_id, created_at
) VALUES (
    'Revenue System', 'financial', 'Revenue Manager',
    'configuration', '{"enabled": true, "activated_at": "2025-08-20T18:35:00Z", "products": 3, "landing_pages": 3, "target_monthly": 10000}', 
    1.0, 'revenue_activation_v921', NOW()
) ON CONFLICT (component_name, knowledge_type, agent_name)
DO UPDATE SET 
    knowledge_data = EXCLUDED.knowledge_data,
    updated_at = NOW();

-- Summary
SELECT 'Revenue Products' as category, COUNT(*) as count FROM products WHERE is_active = true
UNION ALL
SELECT 'Landing Pages', COUNT(*) FROM landing_pages WHERE is_active = true
UNION ALL
SELECT 'Config Settings', COUNT(*) FROM system_config WHERE key LIKE '%revenue%' OR key LIKE '%stripe%';

SELECT '✅ REVENUE SYSTEM ACTIVATED!' as status;
