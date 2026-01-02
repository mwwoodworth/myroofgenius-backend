#!/usr/bin/env python3
"""
Add all missing columns to database tables
"""

import psycopg2
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set")
    return psycopg2.connect(database_url)

def add_missing_columns():
    """Add all missing columns identified during testing"""
    conn = get_connection()
    cursor = conn.cursor()
    
    columns_to_add = [
        # Leads table
        ("leads", "lead_number", "VARCHAR(20)"),
        
        # Estimates table  
        ("estimates", "estimate_number", "VARCHAR(20)"),
        ("estimates", "project_address", "TEXT"),
        
        # Jobs table
        ("jobs", "job_number", "VARCHAR(20)"),
        
        # Invoices table
        ("invoices", "invoice_number", "VARCHAR(20)"),
        
        # Inventory items table
        ("inventory_items", "item_number", "VARCHAR(20)"),
        ("inventory_items", "reorder_point", "INTEGER DEFAULT 10"),
        ("inventory_items", "reorder_quantity", "INTEGER DEFAULT 50"),
        
        # Purchase orders table
        ("purchase_orders", "po_number", "VARCHAR(20)"),
        
        # Vendors table
        ("vendors", "vendor_number", "VARCHAR(20)")
    ]
    
    for table, column, datatype in columns_to_add:
        try:
            # Check if column exists
            cursor.execute(f"""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, (table, column))
            
            if not cursor.fetchone():
                # Add column
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {datatype}")
                
                # Generate values for existing records if it's a number column
                if "_number" in column:
                    prefix = table[:3].upper()
                    cursor.execute(f"""
                        UPDATE {table} 
                        SET {column} = '{prefix}-' || LPAD(CAST(ROW_NUMBER() OVER (ORDER BY created_at) AS VARCHAR), 6, '0')
                        WHERE {column} IS NULL
                    """)
                
                conn.commit()
                logger.info(f"✅ Added column {table}.{column}")
            else:
                logger.info(f"ℹ️ Column {table}.{column} already exists")
                
        except Exception as e:
            conn.rollback()
            logger.warning(f"⚠️ Error adding {table}.{column}: {e}")
    
    # Also ensure all tables have created_at and updated_at
    tables = ['leads', 'estimates', 'jobs', 'invoices', 'payments', 'service_tickets', 
              'warranties', 'schedules', 'inventory_items', 'purchase_orders', 'vendors']
    
    for table in tables:
        try:
            cursor.execute(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                  WHERE table_name='{table}' AND column_name='created_at') THEN
                        ALTER TABLE {table} ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                  WHERE table_name='{table}' AND column_name='updated_at') THEN
                        ALTER TABLE {table} ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
                    END IF;
                END $$;
            """)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.warning(f"Error adding timestamps to {table}: {e}")
    
    cursor.close()
    conn.close()
    logger.info("\n✅ All missing columns added!")

if __name__ == "__main__":
    logger.info("Adding missing columns...")
    add_missing_columns()
