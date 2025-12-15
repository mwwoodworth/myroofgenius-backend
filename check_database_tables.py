#!/usr/bin/env python3
"""
Database Table Checker
Checks existing tables and their schemas to understand current database structure.
"""

import asyncio
import asyncpg
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

async def check_database_structure():
    """Check existing database structure"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Check for customers/users table
        customers_check = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('customers', 'users', 'app_users');
        """)
        
        print("📋 EXISTING USER/CUSTOMER TABLES:")
        if customers_check:
            for row in customers_check:
                print(f"   • {row['table_name']}")
        else:
            print("   • No customer/user tables found")
        
        # Check for leads table structure to see enum
        try:
            leads_enum_check = await conn.fetch("""
                SELECT enumlabel as value
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'leadstatus';
            """)
            
            print("\n📋 LEADSTATUS ENUM VALUES:")
            if leads_enum_check:
                for row in leads_enum_check:
                    print(f"   • {row['value']}")
            else:
                print("   • No leadstatus enum found")
        except Exception as e:
            print(f"   • Error checking leadstatus enum: {e}")
        
        # List all existing tables
        all_tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        print(f"\n📋 ALL EXISTING TABLES ({len(all_tables)}):")
        for row in all_tables:
            print(f"   • {row['table_name']}")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error checking database structure: {e}")

if __name__ == "__main__":
    asyncio.run(check_database_structure())