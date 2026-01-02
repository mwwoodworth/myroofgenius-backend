#!/usr/bin/env python3
"""
Final fix for all missing columns
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

def fix_final_columns():
    """Add final missing columns with proper syntax"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fixes = [
        # Add lead_number column if missing
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='leads' AND column_name='lead_number') THEN
                ALTER TABLE leads ADD COLUMN lead_number VARCHAR(20);
            END IF;
        END $$;""",
        
        # Update existing records with lead numbers
        """UPDATE leads 
           SET lead_number = 'L-' || LPAD(CAST(EXTRACT(EPOCH FROM created_at)::BIGINT % 1000000 AS VARCHAR), 6, '0')
           WHERE lead_number IS NULL;""",
        
        # Add item_number to inventory_items
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='inventory_items' AND column_name='item_number') THEN
                ALTER TABLE inventory_items ADD COLUMN item_number VARCHAR(20);
            END IF;
        END $$;""",
        
        # Update inventory items
        """UPDATE inventory_items 
           SET item_number = 'ITM-' || LPAD(id::TEXT, 6, '0')
           WHERE item_number IS NULL;""",
        
        # Add po_number to purchase_orders
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='purchase_orders' AND column_name='po_number') THEN
                ALTER TABLE purchase_orders ADD COLUMN po_number VARCHAR(20);
            END IF;
        END $$;""",
        
        # Update purchase orders
        """UPDATE purchase_orders 
           SET po_number = 'PO-' || LPAD(id::TEXT, 6, '0')
           WHERE po_number IS NULL;""",
        
        # Add vendor_number to vendors
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='vendors' AND column_name='vendor_number') THEN
                ALTER TABLE vendors ADD COLUMN vendor_number VARCHAR(20);
            END IF;
        END $$;""",
        
        # Update vendors
        """UPDATE vendors 
           SET vendor_number = 'V-' || LPAD(id::TEXT, 6, '0')
           WHERE vendor_number IS NULL;""",
        
        # Ensure all required columns in payments table
        """DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='payments' AND column_name='payment_date') THEN
                ALTER TABLE payments ADD COLUMN payment_date DATE DEFAULT CURRENT_DATE;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='payments' AND column_name='payment_method') THEN
                ALTER TABLE payments ADD COLUMN payment_method VARCHAR(50);
            END IF;
        END $$;"""
    ]
    
    for fix in fixes:
        try:
            cursor.execute(fix)
            conn.commit()
            logger.info(f"✅ Applied: {fix[:60]}...")
        except Exception as e:
            conn.rollback()
            logger.warning(f"⚠️ Error: {e}")
    
    cursor.close()
    conn.close()
    logger.info("\n✅ Final column fixes completed!")

if __name__ == "__main__":
    logger.info("Applying final column fixes...")
    fix_final_columns()
