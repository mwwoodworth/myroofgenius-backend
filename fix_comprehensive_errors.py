#!/usr/bin/env python3
"""
Comprehensive fix for all ERP API errors
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging
import uuid

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

def fix_all_database_issues():
    """Fix all database schema issues comprehensively"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fixes = [
        # Fix invoices table - ensure payment_terms column exists
        """DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='invoices' AND column_name='terms') THEN
                ALTER TABLE invoices RENAME COLUMN terms TO payment_terms;
            ELSIF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name='invoices' AND column_name='payment_terms') THEN
                ALTER TABLE invoices ADD COLUMN payment_terms VARCHAR(50);
            END IF;
        END $$;""",
        
        # Fix payments table - ensure amount column exists
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='payments' AND column_name='amount') THEN
                ALTER TABLE payments ADD COLUMN amount DECIMAL(12,2) NOT NULL DEFAULT 0;
            END IF;
        END $$;""",
        
        # Fix service_tickets table - ensure ticket_number exists
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='service_tickets' AND column_name='ticket_number') THEN
                ALTER TABLE service_tickets ADD COLUMN ticket_number VARCHAR(20);
                -- Generate ticket numbers for existing records
                UPDATE service_tickets 
                SET ticket_number = 'TKT-' || LPAD(CAST(ROW_NUMBER() OVER (ORDER BY created_at) AS VARCHAR), 6, '0')
                WHERE ticket_number IS NULL;
            END IF;
        END $$;""",
        
        # Fix warranties table - ensure warranty_number exists
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='warranties' AND column_name='warranty_number') THEN
                ALTER TABLE warranties ADD COLUMN warranty_number VARCHAR(20);
                UPDATE warranties 
                SET warranty_number = 'WAR-' || LPAD(CAST(ROW_NUMBER() OVER (ORDER BY created_at) AS VARCHAR), 6, '0')
                WHERE warranty_number IS NULL;
            END IF;
        END $$;""",
        
        # Fix leads table - ensure all required columns exist
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='leads' AND column_name='contact_name') THEN
                ALTER TABLE leads ADD COLUMN contact_name VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='leads' AND column_name='contact_email') THEN
                ALTER TABLE leads ADD COLUMN contact_email VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='leads' AND column_name='contact_phone') THEN
                ALTER TABLE leads ADD COLUMN contact_phone VARCHAR(50);
            END IF;
        END $$;""",
        
        # Fix schedules table
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='schedules' AND column_name='schedule_number') THEN
                ALTER TABLE schedules ADD COLUMN schedule_number VARCHAR(20);
                UPDATE schedules 
                SET schedule_number = 'SCH-' || LPAD(CAST(ROW_NUMBER() OVER (ORDER BY created_at) AS VARCHAR), 6, '0')
                WHERE schedule_number IS NULL;
            END IF;
        END $$;""",
        
        # Fix jobs table - ensure all required columns exist
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='jobs' AND column_name='customer_name') THEN
                ALTER TABLE jobs ADD COLUMN customer_name VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='jobs' AND column_name='customer_email') THEN
                ALTER TABLE jobs ADD COLUMN customer_email VARCHAR(255);
            END IF;
        END $$;""",
        
        # Fix estimates table - ensure all required columns exist
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='estimates' AND column_name='customer_name') THEN
                ALTER TABLE estimates ADD COLUMN customer_name VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='estimates' AND column_name='customer_email') THEN
                ALTER TABLE estimates ADD COLUMN customer_email VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='estimates' AND column_name='customer_phone') THEN
                ALTER TABLE estimates ADD COLUMN customer_phone VARCHAR(50);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='estimates' AND column_name='property_address') THEN
                ALTER TABLE estimates ADD COLUMN property_address TEXT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='estimates' AND column_name='roof_type') THEN
                ALTER TABLE estimates ADD COLUMN roof_type VARCHAR(50);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='estimates' AND column_name='roof_size_sqft') THEN
                ALTER TABLE estimates ADD COLUMN roof_size_sqft INTEGER;
            END IF;
        END $$;""",
        
        # Fix invoices table - ensure all required columns exist
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='invoices' AND column_name='customer_name') THEN
                ALTER TABLE invoices ADD COLUMN customer_name VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='invoices' AND column_name='customer_email') THEN
                ALTER TABLE invoices ADD COLUMN customer_email VARCHAR(255);
            END IF;
        END $$;""",
        
        # Fix service_tickets table - ensure all required columns exist
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='service_tickets' AND column_name='customer_name') THEN
                ALTER TABLE service_tickets ADD COLUMN customer_name VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='service_tickets' AND column_name='customer_email') THEN
                ALTER TABLE service_tickets ADD COLUMN customer_email VARCHAR(255);
            END IF;
        END $$;""",
        
        # Fix warranties table - ensure all required columns exist  
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='warranties' AND column_name='customer_name') THEN
                ALTER TABLE warranties ADD COLUMN customer_name VARCHAR(255);
            END IF;
        END $$;""",
        
        # Fix payments table - ensure all required columns exist
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='payments' AND column_name='customer_name') THEN
                ALTER TABLE payments ADD COLUMN customer_name VARCHAR(255);
            END IF;
        END $$;""",
        
        # Create missing indexes for better performance
        """CREATE INDEX IF NOT EXISTS idx_leads_contact_email ON leads(contact_email);""",
        """CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);""",
        """CREATE INDEX IF NOT EXISTS idx_estimates_customer_id ON estimates(customer_id);""",
        """CREATE INDEX IF NOT EXISTS idx_jobs_customer_id ON jobs(customer_id);""",
        """CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);"""
    ]
    
    for fix in fixes:
        try:
            cursor.execute(fix)
            conn.commit()
            logger.info(f"✅ Applied fix: {fix[:50]}...")
        except Exception as e:
            conn.rollback()
            logger.warning(f"⚠️ Error or already applied: {e}")
    
    cursor.close()
    conn.close()
    logger.info("\n✅ Database fixes completed!")

def create_test_data():
    """Create comprehensive test data with proper UUIDs"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Create a test customer with proper UUID
        customer_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO customers (id, name, email, phone, company_name, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (email) DO UPDATE 
            SET name = EXCLUDED.name
            RETURNING id;
        """, (customer_id, 'Test Customer', 'test@example.com', '555-0100', 'Test Company'))
        
        result = cursor.fetchone()
        if result:
            customer_id = result[0]
        logger.info(f"Created test customer: {customer_id}")
        
        # Create a test property
        property_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO properties (id, customer_id, address, city, state, zip_code, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
            RETURNING id;
        """, (property_id, customer_id, '123 Test St', 'Denver', 'CO', '80202'))
        
        result = cursor.fetchone()
        if result:
            property_id = result[0]
            logger.info(f"Created test property: {property_id}")
        
        # Create a test crew
        crew_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO crews (id, name, type, capacity, status, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
            RETURNING id;
        """, (crew_id, 'Test Crew', 'installation', 4, 'available'))
        
        result = cursor.fetchone()
        if result:
            crew_id = result[0]
            logger.info(f"Created test crew: {crew_id}")
        
        conn.commit()
        
        # Save IDs to file for test script
        with open('test_ids.json', 'w') as f:
            import json
            json.dump({
                "customer_id": str(customer_id),
                "property_id": str(property_id) if property_id else None,
                "crew_id": str(crew_id) if crew_id else None
            }, f, indent=2)
        
        logger.info("Test data created and saved to test_ids.json")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating test data: {e}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    logger.info("Starting comprehensive database fixes...")
    fix_all_database_issues()
    create_test_data()
    logger.info("\n✅ All comprehensive fixes applied successfully!")
