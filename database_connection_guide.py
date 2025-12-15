#!/usr/bin/env python3
"""
Database Connection Guide and Usage Examples
Provides connection examples and sample queries for the AI agent database infrastructure.
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta

# Database connection string (keep secure in production)
DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

class DatabaseGuide:
    """Guide for using the AI agent database infrastructure"""
    
    def print_connection_info(self):
        """Print database connection information"""
        print("="*70)
        print("🔗 DATABASE CONNECTION INFORMATION")
        print("="*70)
        print(f"Database URL: {DATABASE_URL}")
        print()
        print("Connection Components:")
        print("  • Host: aws-0-us-east-2.pooler.supabase.com")
        print("  • Port: 5432")
        print("  • Database: postgres")
        print("  • Username: postgres.yomagoqdmxszqtdwuhab")
        print("  • Password: <DB_PASSWORD_REDACTED>")
        print()
        print("⚠️  Security Note: Store connection details in environment variables in production")

    def print_table_reference(self):
        """Print complete table reference guide"""
        print("\n📚 AI AGENT TABLE REFERENCE GUIDE")
        print("="*70)
        
        tables = {
            'user_activity_summary': {
                'purpose': 'Track user engagement metrics and activity scores',
                'key_columns': ['user_id', 'last_active', 'activity_score', 'total_sessions'],
                'use_cases': ['User engagement analysis', 'Churn prediction', 'Activity scoring']
            },
            'user_funnel_tracking': {
                'purpose': 'Analyze conversion funnels and user journey stages',
                'key_columns': ['user_id', 'funnel_stage', 'entered_at', 'conversion'],
                'use_cases': ['Conversion optimization', 'Funnel analysis', 'Stage duration tracking']
            },
            'materials': {
                'purpose': 'Manage inventory, track stock levels, and automate reordering',
                'key_columns': ['name', 'sku', 'quantity', 'reorder_point', 'unit_cost'],
                'use_cases': ['Inventory management', 'Reorder automation', 'Cost tracking']
            },
            'shopping_carts': {
                'purpose': 'Track shopping carts for abandoned cart recovery',
                'key_columns': ['customer_id', 'status', 'items', 'total_amount', 'abandoned_at'],
                'use_cases': ['Abandoned cart recovery', 'Sales optimization', 'Revenue tracking']
            },
            'support_tickets': {
                'purpose': 'Manage customer support tickets and resolution tracking',
                'key_columns': ['customer_id', 'subject', 'status', 'priority', 'resolved_at'],
                'use_cases': ['Customer support automation', 'Ticket routing', 'Resolution tracking']
            },
            'subscriptions': {
                'purpose': 'Track Monthly Recurring Revenue (MRR) and subscription metrics',
                'key_columns': ['customer_id', 'plan_name', 'amount', 'status', 'billing_cycle'],
                'use_cases': ['MRR calculation', 'Churn analysis', 'Revenue forecasting']
            },
            'leads': {
                'purpose': 'Manage leads, track conversion, and score prospects',
                'key_columns': ['name', 'email', 'source', 'status', 'score'],
                'use_cases': ['Lead scoring', 'Conversion tracking', 'Source analysis']
            },
            'user_sessions': {
                'purpose': 'Track user sessions for behavior analysis',
                'key_columns': ['user_id', 'started_at', 'duration_seconds', 'page_views'],
                'use_cases': ['Session analysis', 'User behavior tracking', 'Engagement metrics']
            },
            'user_activity': {
                'purpose': 'Log detailed user activities for pattern recognition',
                'key_columns': ['user_id', 'activity_type', 'details', 'activity_date'],
                'use_cases': ['Activity logging', 'Pattern recognition', 'User journey mapping']
            }
        }
        
        for table, info in tables.items():
            print(f"\n📋 {table.upper()}")
            print(f"   Purpose: {info['purpose']}")
            print(f"   Key Columns: {', '.join(info['key_columns'])}")
            print(f"   Use Cases:")
            for use_case in info['use_cases']:
                print(f"     • {use_case}")

    def print_sample_queries(self):
        """Print sample queries for common AI agent tasks"""
        print("\n🔍 SAMPLE QUERIES FOR AI AGENTS")
        print("="*70)
        
        queries = {
            "User Engagement Analysis": """
            -- Get top engaged users by activity score
            SELECT user_id, activity_score, total_sessions, last_active
            FROM user_activity_summary
            WHERE activity_score > 50
            ORDER BY activity_score DESC
            LIMIT 10;
            """,
            
            "Abandoned Cart Recovery": """
            -- Find abandoned carts in the last 7 days
            SELECT customer_id, total_amount, abandoned_at, items
            FROM shopping_carts
            WHERE status = 'abandoned' 
            AND abandoned_at > NOW() - INTERVAL '7 days'
            ORDER BY total_amount DESC;
            """,
            
            "MRR Calculation": """
            -- Calculate Monthly Recurring Revenue
            SELECT 
                plan_name,
                COUNT(*) as subscribers,
                SUM(amount) as monthly_revenue
            FROM subscriptions
            WHERE status = 'active' AND billing_cycle = 'monthly'
            GROUP BY plan_name
            ORDER BY monthly_revenue DESC;
            """,
            
            "Lead Conversion Analysis": """
            -- Analyze lead conversion by source
            SELECT 
                source,
                COUNT(*) as total_leads,
                COUNT(CASE WHEN status = 'CONVERTED' THEN 1 END) as converted,
                ROUND(COUNT(CASE WHEN status = 'CONVERTED' THEN 1 END) * 100.0 / COUNT(*), 2) as conversion_rate
            FROM leads
            GROUP BY source
            ORDER BY conversion_rate DESC;
            """,
            
            "Inventory Reorder Alert": """
            -- Find materials that need reordering
            SELECT name, sku, quantity, reorder_point, supplier
            FROM materials
            WHERE quantity <= reorder_point AND is_active = true
            ORDER BY (reorder_point - quantity) DESC;
            """,
            
            "Session Analysis": """
            -- Analyze user session patterns
            SELECT 
                DATE(started_at) as session_date,
                COUNT(*) as total_sessions,
                AVG(duration_seconds) as avg_duration,
                SUM(page_views) as total_page_views
            FROM user_sessions
            WHERE started_at > NOW() - INTERVAL '30 days'
            GROUP BY DATE(started_at)
            ORDER BY session_date DESC;
            """
        }
        
        for query_name, query in queries.items():
            print(f"\n📊 {query_name}:")
            print(query)

    def print_asyncpg_examples(self):
        """Print asyncpg usage examples"""
        print("\n💻 ASYNCPG USAGE EXAMPLES")
        print("="*70)
        
        example_code = '''
import asyncio
import asyncpg

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

async def get_engaged_users():
    """Get highly engaged users"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        users = await conn.fetch("""
            SELECT user_id, activity_score, total_sessions
            FROM user_activity_summary
            WHERE activity_score > 75
            ORDER BY activity_score DESC;
        """)
        return users
    finally:
        await conn.close()

async def create_new_lead(name, email, source):
    """Create a new lead"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        lead_id = await conn.fetchval("""
            INSERT INTO leads (name, email, source, status, score)
            VALUES ($1, $2, $3, 'NEW', 0)
            RETURNING id;
        """, name, email, source)
        return lead_id
    finally:
        await conn.close()

async def update_material_quantity(sku, new_quantity):
    """Update material inventory"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        await conn.execute("""
            UPDATE materials 
            SET quantity = $2, updated_at = NOW()
            WHERE sku = $1;
        """, sku, new_quantity)
    finally:
        await conn.close()

async def get_mrr_metrics():
    """Calculate MRR metrics"""
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        mrr_data = await conn.fetch("""
            SELECT 
                plan_name,
                COUNT(*) as subscribers,
                SUM(amount) as monthly_revenue
            FROM subscriptions
            WHERE status = 'active'
            GROUP BY plan_name;
        """)
        return mrr_data
    finally:
        await conn.close()

# Usage examples
async def main():
    users = await get_engaged_users()
    lead_id = await create_new_lead("John Doe", "john@example.com", "Website")
    await update_material_quantity("SHNG-001", 450)
    mrr_metrics = await get_mrr_metrics()

if __name__ == "__main__":
    asyncio.run(main())
        '''
        
        print(example_code)

    def print_column_fixes_reference(self):
        """Print reference for applied column fixes"""
        print("\n🔧 APPLIED COLUMN FIXES REFERENCE")
        print("="*70)
        
        fixes = {
            'centerpoint_data': [
                ('address', 'VARCHAR(500)', 'Store property addresses for job locations'),
                ('customer_name', 'VARCHAR(255)', 'Store customer names for easy reference'),
                ('phone', 'VARCHAR(50)', 'Store customer phone numbers'),
                ('updated_at', 'TIMESTAMP', 'Track when records are modified')
            ],
            'jobs': [
                ('estimated_hours', 'DECIMAL(5,2)', 'Estimate job duration for scheduling'),
                ('crew_size', 'INTEGER', 'Plan crew resource allocation'),
                ('scheduled_date', 'DATE', 'Schedule job dates'),
                ('location', 'VARCHAR(500)', 'Store job location details')
            ],
            'invoices': [
                ('amount', 'DECIMAL(10,2)', 'Store invoice amounts for revenue tracking'),
                ('paid_at', 'TIMESTAMP', 'Track payment dates')
            ]
        }
        
        for table, columns in fixes.items():
            print(f"\n📋 {table.upper()} Table Fixes:")
            for column, data_type, purpose in columns:
                print(f"   • {column:<20} ({data_type:<15}) → {purpose}")

    async def test_connection(self):
        """Test database connection"""
        print("\n🔍 TESTING DATABASE CONNECTION")
        print("="*70)
        
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            
            # Test basic connection
            version = await conn.fetchval("SELECT version();")
            print(f"✅ Connection successful!")
            print(f"   Database version: {version[:50]}...")
            
            # Test table access
            table_count = await conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            print(f"   Total tables: {table_count}")
            
            # Test AI agent tables
            ai_tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN (
                    'user_activity_summary', 'user_funnel_tracking', 'materials',
                    'shopping_carts', 'support_tickets', 'subscriptions',
                    'leads', 'user_sessions', 'user_activity'
                );
            """)
            print(f"   AI agent tables: {len(ai_tables)}/9 available")
            
            await conn.close()
            print("✅ All tests passed!")
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")

def main():
    """Main function to display all guides"""
    guide = DatabaseGuide()
    
    guide.print_connection_info()
    guide.print_table_reference()
    guide.print_sample_queries()
    guide.print_asyncpg_examples()
    guide.print_column_fixes_reference()
    
    # Test connection
    asyncio.run(guide.test_connection())
    
    print("\n" + "="*70)
    print("📚 DATABASE SETUP COMPLETE - READY FOR AI AGENTS!")
    print("="*70)

if __name__ == "__main__":
    main()