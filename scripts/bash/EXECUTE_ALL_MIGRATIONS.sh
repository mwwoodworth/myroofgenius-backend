#!/bin/bash
# Execute all database migrations for production

set -euo pipefail

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found. Please create one based on .env.example."
    exit 1
fi

echo "🚀 EXECUTING ALL DATABASE MIGRATIONS"
echo "===================================="
echo ""

# Database credentials
export PGPASSWORD="${PGPASSWORD}"
DB_HOST="${DB_HOST}"
DB_USER="${DB_USER}"
DB_NAME="${DB_NAME}"

# Using pooler connection for better reliability
POOLER_URL="postgresql://${DB_USER}:<DB_PASSWORD_REDACTED>@${DB_HOST}:6543/${DB_NAME}?sslmode=require"

echo "📊 Step 1: Creating env_master table and loading environment variables..."
psql "$POOLER_URL" -f CREATE_ENV_MASTER_PRODUCTION.sql

if [ $? -eq 0 ]; then
    echo "✅ Environment master table created successfully"
else
    echo "❌ Failed to create env_master table"
fi

echo ""
echo "📊 Step 2: Verifying table creation..."
psql "$POOLER_URL" -c "SELECT COUNT(*) as env_vars FROM env_master WHERE is_active = true;"

echo ""
echo "📊 Step 3: Checking Stripe product tables..."
psql "$POOLER_URL" -c "
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'usd',
    interval VARCHAR(20),
    stripe_product_id VARCHAR(255),
    stripe_price_id VARCHAR(255),
    features JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    product_id UUID REFERENCES products(id),
    status VARCHAR(50),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_payment_intent_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255),
    subscription_id UUID REFERENCES subscriptions(id),
    amount_cents INTEGER,
    currency VARCHAR(3),
    status VARCHAR(50),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id VARCHAR(255) UNIQUE,
    event_type VARCHAR(100),
    payload JSONB,
    processed BOOLEAN DEFAULT false,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);"

echo "✅ Stripe tables created/verified"

echo ""
echo "📊 Step 4: Inserting default products..."
psql "$POOLER_URL" -c "
INSERT INTO products (name, description, price_cents, interval, features)
VALUES 
    ('MyRoofGenius Pro', 'Professional roofing business management', 9900, 'monthly', 
     '[\"Unlimited estimates\", \"AI-powered analysis\", \"Customer management\", \"Job tracking\", \"Basic reporting\"]'::jsonb),
    ('WeatherCraft ERP Access', 'Complete ERP system for roofing companies', 29900, 'monthly',
     '[\"Everything in Pro\", \"Advanced analytics\", \"Team management\", \"Inventory tracking\", \"Financial reporting\", \"API access\"]'::jsonb),
    ('AI Assistant Add-on', 'Advanced AI capabilities', 4900, 'monthly',
     '[\"AUREA AI assistant\", \"Voice commands\", \"Automated workflows\", \"Predictive analytics\"]'::jsonb)
ON CONFLICT DO NOTHING;"

echo ""
echo "📊 Step 5: Verifying all tables..."
psql "$POOLER_URL" -c "
SELECT 
    'env_master' as table_name, COUNT(*) as records FROM env_master
UNION ALL
SELECT 
    'products', COUNT(*) FROM products
UNION ALL
SELECT 
    'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 
    'payments', COUNT(*) FROM payments
UNION ALL
SELECT 
    'webhook_events', COUNT(*) FROM webhook_events;"

echo ""
echo "✨ DATABASE MIGRATIONS COMPLETE!"
echo "================================"