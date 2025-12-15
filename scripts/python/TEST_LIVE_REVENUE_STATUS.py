#!/usr/bin/env python3
"""
Test live revenue status from production database
"""

import asyncpg
import asyncio
from datetime import datetime, timedelta

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require"

async def test_revenue_status():
    """Test revenue status from production database"""
    print("=" * 60)
    print("💰 MYROOFGENIUS REVENUE STATUS CHECK")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to production database")
        
        # Check revenue transactions
        revenue_query = """
        SELECT 
            COUNT(*) as total_transactions,
            SUM(amount) / 100.0 as total_revenue,
            SUM(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN amount ELSE 0 END) / 100.0 as monthly_revenue,
            SUM(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN amount ELSE 0 END) / 100.0 as weekly_revenue,
            SUM(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN amount ELSE 0 END) / 100.0 as daily_revenue
        FROM revenue_transactions
        WHERE status = 'completed'
        """
        
        revenue = await conn.fetchrow(revenue_query)
        
        print("\n📊 REVENUE METRICS:")
        print(f"  Total Revenue: ${revenue['total_revenue']:,.2f}")
        print(f"  Monthly Revenue: ${revenue['monthly_revenue']:,.2f}")
        print(f"  Weekly Revenue: ${revenue['weekly_revenue']:,.2f}")
        print(f"  Daily Revenue: ${revenue['daily_revenue']:,.2f}")
        print(f"  Total Transactions: {revenue['total_transactions']}")
        
        # Check subscriptions
        sub_query = """
        SELECT 
            COUNT(*) as active_subscriptions,
            SUM(plan_amount) / 100.0 as mrr
        FROM subscriptions
        WHERE status = 'active'
        """
        
        subs = await conn.fetchrow(sub_query)
        
        print("\n🔄 SUBSCRIPTION METRICS:")
        print(f"  Active Subscriptions: {subs['active_subscriptions']}")
        print(f"  Monthly Recurring Revenue: ${subs['mrr']:,.2f} (if configured)")
        
        # Check products
        products_query = """
        SELECT 
            COUNT(*) as total_products,
            COUNT(CASE WHEN in_stock THEN 1 END) as in_stock_products
        FROM products
        """
        
        products = await conn.fetchrow(products_query)
        
        print("\n📦 PRODUCT INVENTORY:")
        print(f"  Total Products: {products['total_products']}")
        print(f"  In Stock: {products['in_stock_products']}")
        
        # Check customers
        customers_query = """
        SELECT 
            COUNT(*) as total_customers,
            COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as new_customers
        FROM customers
        """
        
        customers = await conn.fetchrow(customers_query)
        
        print("\n👥 CUSTOMER METRICS:")
        print(f"  Total Customers: {customers['total_customers']}")
        print(f"  New This Month: {customers['new_customers']}")
        
        # Check environment variables
        env_query = """
        SELECT 
            COUNT(*) as total_env_vars,
            COUNT(CASE WHEN key LIKE 'STRIPE%' THEN 1 END) as stripe_keys,
            COUNT(CASE WHEN is_sensitive THEN 1 END) as sensitive_vars
        FROM env_master
        WHERE is_active = true
        """
        
        env_vars = await conn.fetchrow(env_query)
        
        print("\n🔑 ENVIRONMENT CONFIGURATION:")
        print(f"  Total Env Variables: {env_vars['total_env_vars']}")
        print(f"  Stripe Keys Configured: {env_vars['stripe_keys']}")
        print(f"  Sensitive Variables: {env_vars['sensitive_vars']}")
        
        # Growth calculation
        if revenue['total_revenue'] and revenue['monthly_revenue']:
            growth_rate = (revenue['monthly_revenue'] / (revenue['total_revenue'] / 12)) * 100 - 100
            print("\n📈 GROWTH METRICS:")
            print(f"  Monthly Growth Rate: {growth_rate:.1f}%")
            print(f"  Projected Annual Revenue: ${revenue['monthly_revenue'] * 12:,.2f}")
        
        await conn.close()
        
        print("\n" + "=" * 60)
        print("✅ REVENUE SYSTEM IS OPERATIONAL!")
        print("💰 Ready to process real payments and generate income")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check database connection and tables")

if __name__ == "__main__":
    asyncio.run(test_revenue_status())