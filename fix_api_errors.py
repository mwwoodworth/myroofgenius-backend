#!/usr/bin/env python3
"""
Fix API errors found during testing
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_connection():
    # Use Supabase connection from .env
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    else:
        # Fallback to manual connection
        return psycopg2.connect(
            host="aws-0-us-east-2.pooler.supabase.com",
            database="postgres",
            user="postgres.yomagoqdmxszqtdwuhab",
            password="<DB_PASSWORD_REDACTED>",
            port=5432
        )

def fix_database_columns():
    """Fix column name mismatches and missing columns"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fixes = [
        # Fix invoices table - rename 'terms' to 'payment_terms'
        """DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='invoices' AND column_name='terms') THEN
                ALTER TABLE invoices RENAME COLUMN terms TO payment_terms;
            END IF;
        END $$;""",
        
        # Add missing ticket_number to service_tickets
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='service_tickets' AND column_name='ticket_number') THEN
                ALTER TABLE service_tickets ADD COLUMN ticket_number VARCHAR(20);
                -- Generate ticket numbers for existing records
                UPDATE service_tickets 
                SET ticket_number = 'TKT-' || LPAD(CAST(EXTRACT(EPOCH FROM NOW())::BIGINT % 1000000 AS VARCHAR), 6, '0')
                WHERE ticket_number IS NULL;
                -- Make it NOT NULL for future inserts
                ALTER TABLE service_tickets ALTER COLUMN ticket_number SET NOT NULL;
            END IF;
        END $$;""",
        
        # Add missing warranty_number to warranties
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='warranties' AND column_name='warranty_number') THEN
                ALTER TABLE warranties ADD COLUMN warranty_number VARCHAR(20);
                UPDATE warranties 
                SET warranty_number = 'WAR-' || LPAD(CAST(EXTRACT(EPOCH FROM NOW())::BIGINT % 1000000 AS VARCHAR), 6, '0')
                WHERE warranty_number IS NULL;
                ALTER TABLE warranties ALTER COLUMN warranty_number SET NOT NULL;
            END IF;
        END $$;""",
        
        # Fix leads table - ensure all required columns exist
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='leads' AND column_name='customer_id') THEN
                ALTER TABLE leads ADD COLUMN customer_id UUID REFERENCES customers(id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='leads' AND column_name='property_id') THEN
                ALTER TABLE leads ADD COLUMN property_id UUID REFERENCES properties(id);
            END IF;
        END $$;""",
        
        # Fix schedules table
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='schedules' AND column_name='schedule_number') THEN
                ALTER TABLE schedules ADD COLUMN schedule_number VARCHAR(20);
                UPDATE schedules 
                SET schedule_number = 'SCH-' || LPAD(CAST(EXTRACT(EPOCH FROM NOW())::BIGINT % 1000000 AS VARCHAR), 6, '0')
                WHERE schedule_number IS NULL;
                ALTER TABLE schedules ALTER COLUMN schedule_number SET NOT NULL;
            END IF;
        END $$;""",
        
        # Fix payments table
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='payments' AND column_name='payment_number') THEN
                ALTER TABLE payments ADD COLUMN payment_number VARCHAR(20);
                UPDATE payments 
                SET payment_number = 'PAY-' || LPAD(CAST(EXTRACT(EPOCH FROM NOW())::BIGINT % 1000000 AS VARCHAR), 6, '0')
                WHERE payment_number IS NULL;
                ALTER TABLE payments ALTER COLUMN payment_number SET NOT NULL;
            END IF;
        END $$;""",
        
        # Fix jobs table - ensure estimate_id column exists
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='jobs' AND column_name='estimate_id') THEN
                ALTER TABLE jobs ADD COLUMN estimate_id UUID REFERENCES estimates(id);
            END IF;
        END $$;""",
        
        # Create missing indexes for better performance
        """CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);""",
        """CREATE INDEX IF NOT EXISTS idx_estimates_status ON estimates(status);""",
        """CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);""",
        """CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);""",
        """CREATE INDEX IF NOT EXISTS idx_service_tickets_status ON service_tickets(status);"""
    ]
    
    for fix in fixes:
        try:
            cursor.execute(fix)
            conn.commit()
            logger.info(f"✅ Applied fix: {fix[:50]}...")
        except Exception as e:
            conn.rollback()
            logger.warning(f"⚠️ Fix already applied or error: {e}")
    
    cursor.close()
    conn.close()
    logger.info("\n✅ Database fixes completed!")

def create_test_data():
    """Create some test data with proper UUIDs"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create a test customer
        cursor.execute("""
            INSERT INTO customers (name, email, phone, company_name)
            VALUES ('Test Customer', 'test@example.com', '555-0100', 'Test Company')
            ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name
            RETURNING id;
        """)
        customer_id = cursor.fetchone()[0]
        logger.info(f"Created test customer: {customer_id}")
        
        # Create a test property
        cursor.execute("""
            INSERT INTO properties (customer_id, address, city, state, zip_code)
            VALUES (%s, '123 Test St', 'Denver', 'CO', '80202')
            ON CONFLICT DO NOTHING
            RETURNING id;
        """, (customer_id,))
        result = cursor.fetchone()
        if result:
            property_id = result[0]
            logger.info(f"Created test property: {property_id}")
        
        conn.commit()
        
        # Save IDs to file for test script
        with open('test_ids.txt', 'w') as f:
            f.write(f"customer_id={customer_id}\n")
            if result:
                f.write(f"property_id={property_id}\n")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating test data: {e}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    logger.info("Starting database fixes...")
    fix_database_columns()
    create_test_data()
    logger.info("\n✅ All fixes applied successfully!")
