#!/usr/bin/env python3
"""
Database Table Creation Script
Creates missing tables and fixes existing columns for AI agent requirements.
"""

import asyncio
import asyncpg
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

class DatabaseTableCreator:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self.results = {
            'tables_created': [],
            'columns_added': [],
            'errors': [],
            'warnings': []
        }

    async def create_connection_pool(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=5,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    async def close_pool(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def execute_query(self, query: str, description: str) -> bool:
        """Execute a single query with error handling"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query)
            logger.info(f"✅ {description}")
            return True
        except asyncpg.exceptions.DuplicateTableError:
            logger.warning(f"⚠️  {description} - Table already exists")
            self.results['warnings'].append(f"{description} - Already exists")
            return True
        except asyncpg.exceptions.DuplicateColumnError:
            logger.warning(f"⚠️  {description} - Column already exists")
            self.results['warnings'].append(f"{description} - Already exists")
            return True
        except Exception as e:
            logger.error(f"❌ {description} - Error: {e}")
            self.results['errors'].append(f"{description}: {str(e)}")
            return False

    async def create_user_activity_summary_table(self):
        """Create user_activity_summary table"""
        query = """
        CREATE TABLE IF NOT EXISTS user_activity_summary (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID,
            last_active TIMESTAMP DEFAULT NOW(),
            activity_score INTEGER DEFAULT 0,
            total_sessions INTEGER DEFAULT 0,
            total_duration_seconds INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity_summary(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_activity_score ON user_activity_summary(activity_score);
        """
        success = await self.execute_query(query, "Created user_activity_summary table")
        if success:
            self.results['tables_created'].append('user_activity_summary')

    async def create_user_funnel_tracking_table(self):
        """Create user_funnel_tracking table"""
        query = """
        CREATE TABLE IF NOT EXISTS user_funnel_tracking (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID,
            funnel_stage VARCHAR(50) NOT NULL,
            entered_at TIMESTAMP DEFAULT NOW(),
            exited_at TIMESTAMP,
            time_in_stage INTEGER,
            conversion BOOLEAN DEFAULT FALSE,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_funnel_user ON user_funnel_tracking(user_id);
        CREATE INDEX IF NOT EXISTS idx_funnel_stage ON user_funnel_tracking(funnel_stage);
        CREATE INDEX IF NOT EXISTS idx_funnel_created ON user_funnel_tracking(created_at);
        """
        success = await self.execute_query(query, "Created user_funnel_tracking table")
        if success:
            self.results['tables_created'].append('user_funnel_tracking')

    async def create_materials_table(self):
        """Create materials table for inventory management"""
        query = """
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
        """
        success = await self.execute_query(query, "Created materials table")
        if success:
            self.results['tables_created'].append('materials')

    async def create_shopping_carts_table(self):
        """Create shopping_carts table for abandoned cart tracking"""
        query = """
        CREATE TABLE IF NOT EXISTS shopping_carts (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            customer_id UUID,
            status VARCHAR(50) DEFAULT 'active',
            items JSONB DEFAULT '[]',
            total_amount DECIMAL(10,2) DEFAULT 0,
            abandoned_at TIMESTAMP,
            converted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_carts_customer ON shopping_carts(customer_id);
        CREATE INDEX IF NOT EXISTS idx_carts_status ON shopping_carts(status);
        """
        success = await self.execute_query(query, "Created shopping_carts table")
        if success:
            self.results['tables_created'].append('shopping_carts')

    async def create_support_tickets_table(self):
        """Create support_tickets table for customer support"""
        query = """
        CREATE TABLE IF NOT EXISTS support_tickets (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            customer_id UUID,
            subject VARCHAR(255),
            description TEXT,
            status VARCHAR(50) DEFAULT 'open',
            priority VARCHAR(20) DEFAULT 'medium',
            assigned_to VARCHAR(255),
            resolved_at TIMESTAMP,
            resolution TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_tickets_customer ON support_tickets(customer_id);
        CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status);
        """
        success = await self.execute_query(query, "Created support_tickets table")
        if success:
            self.results['tables_created'].append('support_tickets')

    async def create_subscriptions_table(self):
        """Create subscriptions table for MRR tracking"""
        query = """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            customer_id UUID,
            plan_name VARCHAR(100),
            amount DECIMAL(10,2),
            status VARCHAR(50) DEFAULT 'active',
            billing_cycle VARCHAR(20) DEFAULT 'monthly',
            next_billing_date DATE,
            cancelled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_subscriptions_customer ON subscriptions(customer_id);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
        """
        success = await self.execute_query(query, "Created subscriptions table")
        if success:
            self.results['tables_created'].append('subscriptions')

    async def create_leads_table(self):
        """Create leads table for lead management"""
        query = """
        CREATE TABLE IF NOT EXISTS leads (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            source VARCHAR(100),
            status VARCHAR(50) DEFAULT 'new',
            score INTEGER DEFAULT 0,
            assigned_to VARCHAR(255),
            converted_at TIMESTAMP,
            customer_id UUID,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
        CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
        """
        success = await self.execute_query(query, "Created leads table")
        if success:
            self.results['tables_created'].append('leads')

    async def create_user_sessions_table(self):
        """Create user_sessions table for session tracking"""
        query = """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID,
            session_date DATE DEFAULT CURRENT_DATE,
            duration_seconds INTEGER DEFAULT 0,
            page_views INTEGER DEFAULT 0,
            actions_taken JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_date ON user_sessions(session_date);
        """
        success = await self.execute_query(query, "Created user_sessions table")
        if success:
            self.results['tables_created'].append('user_sessions')

    async def create_user_activity_table(self):
        """Create user_activity table for activity logging"""
        query = """
        CREATE TABLE IF NOT EXISTS user_activity (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID,
            activity_date DATE DEFAULT CURRENT_DATE,
            activity_type VARCHAR(100),
            details JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity(user_id);
        CREATE INDEX IF NOT EXISTS idx_activity_date ON user_activity(activity_date);
        """
        success = await self.execute_query(query, "Created user_activity table")
        if success:
            self.results['tables_created'].append('user_activity')

    async def add_centerpoint_data_columns(self):
        """Add missing columns to centerpoint_data table"""
        queries = [
            ("ADD address column", "ALTER TABLE centerpoint_data ADD COLUMN IF NOT EXISTS address VARCHAR(500);"),
            ("ADD customer_name column", "ALTER TABLE centerpoint_data ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255);"),
            ("ADD phone column", "ALTER TABLE centerpoint_data ADD COLUMN IF NOT EXISTS phone VARCHAR(50);"),
            ("ADD updated_at column", "ALTER TABLE centerpoint_data ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();")
        ]
        
        for description, query in queries:
            success = await self.execute_query(query, f"centerpoint_data table: {description}")
            if success:
                self.results['columns_added'].append(f"centerpoint_data.{description}")

    async def add_jobs_table_columns(self):
        """Add missing columns to jobs table"""
        queries = [
            ("ADD estimated_hours column", "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS estimated_hours DECIMAL(5,2) DEFAULT 0;"),
            ("ADD crew_size column", "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS crew_size INTEGER DEFAULT 2;"),
            ("ADD scheduled_date column", "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS scheduled_date DATE;"),
            ("ADD location column", "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS location VARCHAR(500);")
        ]
        
        for description, query in queries:
            success = await self.execute_query(query, f"jobs table: {description}")
            if success:
                self.results['columns_added'].append(f"jobs.{description}")

    async def add_invoices_table_columns(self):
        """Add missing columns to invoices table"""
        queries = [
            ("ADD amount column", "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS amount DECIMAL(10,2) DEFAULT 0;"),
            ("ADD paid_at column", "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP;")
        ]
        
        for description, query in queries:
            success = await self.execute_query(query, f"invoices table: {description}")
            if success:
                self.results['columns_added'].append(f"invoices.{description}")

    async def insert_sample_data(self):
        """Insert sample data for testing"""
        # Sample materials
        materials_query = """
        INSERT INTO materials (name, sku, category, quantity, reorder_point, unit_cost, supplier) VALUES
        ('Roofing Shingles - Asphalt', 'SHNG-001', 'Roofing', 500, 100, 45.00, 'ABC Supply'),
        ('Roofing Nails - 1.25"', 'NAIL-001', 'Fasteners', 10000, 2000, 0.05, 'Fastener Co'),
        ('Tar Paper - 30lb', 'TAR-001', 'Underlayment', 200, 50, 25.00, 'Paper Supply'),
        ('Ridge Vents', 'VENT-001', 'Ventilation', 100, 25, 35.00, 'Vent Masters'),
        ('Flashing - Aluminum', 'FLASH-001', 'Flashing', 300, 75, 15.00, 'Metal Works')
        ON CONFLICT (sku) DO NOTHING;
        """
        await self.execute_query(materials_query, "Inserted sample materials data")

        # Sample leads
        leads_query = """
        INSERT INTO leads (name, email, phone, source, status, score) VALUES 
        ('John Smith', 'john.smith@example.com', '512-555-0101', 'Website', 'new', 75),
        ('Jane Doe', 'jane.doe@example.com', '512-555-0102', 'Google Ads', 'qualified', 85),
        ('Bob Wilson', 'bob.wilson@example.com', '512-555-0103', 'Referral', 'contacted', 60),
        ('Alice Brown', 'alice.brown@example.com', '512-555-0104', 'Facebook', 'new', 50),
        ('Charlie Davis', 'charlie.davis@example.com', '512-555-0105', 'Direct', 'converted', 95)
        ON CONFLICT DO NOTHING;
        """
        await self.execute_query(leads_query, "Inserted sample leads data")

    async def verify_tables_exist(self) -> Dict[str, bool]:
        """Verify that all required tables exist"""
        required_tables = [
            'user_activity_summary',
            'user_funnel_tracking', 
            'materials',
            'shopping_carts',
            'support_tickets',
            'subscriptions',
            'leads',
            'user_sessions',
            'user_activity'
        ]
        
        verification_results = {}
        
        for table in required_tables:
            query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = $1
            );
            """
            try:
                async with self.pool.acquire() as conn:
                    exists = await conn.fetchval(query, table)
                    verification_results[table] = exists
            except Exception as e:
                logger.error(f"Error verifying table {table}: {e}")
                verification_results[table] = False
        
        return verification_results

    async def run_all_operations(self):
        """Run all database operations"""
        logger.info("🚀 Starting database table creation and column fixes...")
        
        await self.create_connection_pool()
        
        try:
            # Create all required tables
            await self.create_user_activity_summary_table()
            await self.create_user_funnel_tracking_table()
            await self.create_materials_table()
            await self.create_shopping_carts_table()
            await self.create_support_tickets_table()
            await self.create_subscriptions_table()
            await self.create_leads_table()
            await self.create_user_sessions_table()
            await self.create_user_activity_table()
            
            # Add missing columns to existing tables
            await self.add_centerpoint_data_columns()
            await self.add_jobs_table_columns()
            await self.add_invoices_table_columns()
            
            # Insert sample data
            await self.insert_sample_data()
            
            # Verify all tables exist
            verification_results = await self.verify_tables_exist()
            
            # Print final report
            self.print_final_report(verification_results)
            
        except Exception as e:
            logger.error(f"Critical error during operations: {e}")
            self.results['errors'].append(f"Critical error: {str(e)}")
        finally:
            await self.close_pool()

    def print_final_report(self, verification_results: Dict[str, bool]):
        """Print comprehensive final report"""
        print("\n" + "="*60)
        print("🎯 DATABASE OPERATIONS COMPLETE")
        print("="*60)
        
        print(f"\n✅ TABLES CREATED ({len(self.results['tables_created'])}):")
        for table in self.results['tables_created']:
            status = "✅ EXISTS" if verification_results.get(table, False) else "❌ MISSING"
            print(f"   • {table} - {status}")
        
        print(f"\n🔧 COLUMNS ADDED ({len(self.results['columns_added'])}):")
        for column in self.results['columns_added']:
            print(f"   • {column}")
        
        if self.results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for warning in self.results['warnings']:
                print(f"   • {warning}")
        
        if self.results['errors']:
            print(f"\n❌ ERRORS ({len(self.results['errors'])}):")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        # Summary statistics
        total_operations = len(self.results['tables_created']) + len(self.results['columns_added'])
        successful_operations = total_operations - len(self.results['errors'])
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
        
        print(f"\n📊 SUMMARY:")
        print(f"   • Total Operations: {total_operations}")
        print(f"   • Successful: {successful_operations}")
        print(f"   • Success Rate: {success_rate:.1f}%")
        
        print("\n" + "="*60)
        if len(self.results['errors']) == 0:
            print("🎉 ALL OPERATIONS COMPLETED SUCCESSFULLY!")
        else:
            print("⚠️  OPERATIONS COMPLETED WITH SOME ERRORS")
        print("="*60)

async def main():
    """Main function to run database operations"""
    creator = DatabaseTableCreator(DATABASE_URL)
    await creator.run_all_operations()

if __name__ == "__main__":
    asyncio.run(main())