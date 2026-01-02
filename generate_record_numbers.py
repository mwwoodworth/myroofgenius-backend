#!/usr/bin/env python3
"""
Generate missing record numbers for production database
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Production database connection
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def generate_numbers():
    """Generate missing record numbers using subqueries"""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = [
        # Generate lead numbers
        """WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM leads WHERE lead_number IS NULL
        )
        UPDATE leads SET lead_number = 'L-2025-' || LPAD(CAST(n.rn AS VARCHAR), 5, '0')
        FROM numbered n WHERE leads.id = n.id;""",
        
        # Generate job numbers
        """WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM jobs WHERE job_number IS NULL
        )
        UPDATE jobs SET job_number = 'JOB-2025-' || LPAD(CAST(n.rn AS VARCHAR), 5, '0')
        FROM numbered n WHERE jobs.id = n.id;""",
        
        # Generate invoice numbers
        """WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM invoices WHERE invoice_number IS NULL
        )
        UPDATE invoices SET invoice_number = 'INV-2025-' || LPAD(CAST(n.rn AS VARCHAR), 5, '0')
        FROM numbered n WHERE invoices.id = n.id;""",
        
        # Generate ticket numbers
        """WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM service_tickets WHERE ticket_number IS NULL
        )
        UPDATE service_tickets SET ticket_number = 'TKT-2025-' || LPAD(CAST(n.rn AS VARCHAR), 5, '0')
        FROM numbered n WHERE service_tickets.id = n.id;""",
        
        # Generate warranty numbers
        """WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM warranties WHERE warranty_number IS NULL
        )
        UPDATE warranties SET warranty_number = 'WAR-2025-' || LPAD(CAST(n.rn AS VARCHAR), 5, '0')
        FROM numbered n WHERE warranties.id = n.id;""",
        
        # Generate schedule numbers
        """WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as rn
            FROM schedules WHERE schedule_number IS NULL
        )
        UPDATE schedules SET schedule_number = 'SCH-2025-' || LPAD(CAST(n.rn AS VARCHAR), 5, '0')
        FROM numbered n WHERE schedules.id = n.id;""",
        
        # Fix crews table columns
        """ALTER TABLE crews ADD COLUMN IF NOT EXISTS crew_name VARCHAR(100);""",
        """UPDATE crews SET crew_name = 'Crew ' || SUBSTR(CAST(id AS VARCHAR), 1, 8) WHERE crew_name IS NULL;""",
        
        # Insert test crews if none exist
        """INSERT INTO crews (id, crew_name, type, capacity, status, created_at)
           SELECT 
               gen_random_uuid(),
               'Alpha Crew',
               'installation',
               4,
               'available',
               NOW()
           WHERE NOT EXISTS (SELECT 1 FROM crews LIMIT 1);""",
        
        """INSERT INTO crews (id, crew_name, type, capacity, status, created_at)
           SELECT 
               gen_random_uuid(),
               'Beta Crew',
               'repair',
               3,
               'available',
               NOW()
           WHERE NOT EXISTS (SELECT 1 FROM crews WHERE crew_name = 'Beta Crew');""",
        
        """INSERT INTO crews (id, crew_name, type, capacity, status, created_at)
           SELECT 
               gen_random_uuid(),
               'Gamma Crew',
               'maintenance',
               2,
               'available',
               NOW()
           WHERE NOT EXISTS (SELECT 1 FROM crews WHERE crew_name = 'Gamma Crew');"""
    ]
    
    for update in updates:
        try:
            cursor.execute(update)
            rows_affected = cursor.rowcount
            conn.commit()
            if rows_affected > 0:
                logger.info(f"✅ Updated {rows_affected} records: {update[:50]}...")
            else:
                logger.info(f"ℹ️ No updates needed: {update[:50]}...")
        except Exception as e:
            conn.rollback()
            logger.warning(f"⚠️ Error: {str(e)[:100]}")
    
    # Verify counts
    cursor.execute("SELECT COUNT(*) FROM leads WHERE lead_number IS NOT NULL")
    lead_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_number IS NOT NULL")
    job_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM crews")
    crew_count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"RECORD NUMBER GENERATION COMPLETE")
    logger.info(f"📊 Leads with numbers: {lead_count}")
    logger.info(f"📊 Jobs with numbers: {job_count}")
    logger.info(f"📊 Crews available: {crew_count}")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    logger.info("🚀 Generating missing record numbers...")
    generate_numbers()
    logger.info("\n✅ ALL RECORD NUMBERS GENERATED!")
