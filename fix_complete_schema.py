#!/usr/bin/env python3
"""
Fix Complete Schema - Ensure all tables have required columns
"""

import psycopg2
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", 
    "postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def fix_schema():
    """Fix all schema issues for complete ERP system"""
    conn = get_connection()
    cursor = conn.cursor()
    
    fixes = [
        # Fix leads table
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS company_name VARCHAR(255)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS property_type VARCHAR(100)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 50",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS estimated_value DECIMAL(15,2)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS urgency VARCHAR(50)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS source VARCHAR(100)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS notes TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_name VARCHAR(255)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS property_address TEXT",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS roof_type VARCHAR(100)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS roof_size INTEGER",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS budget_range VARCHAR(50)",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS converted_at TIMESTAMP",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS customer_id UUID",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS score_updated_at TIMESTAMP",
        
        # Fix estimates table
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS customer_id UUID",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS lead_id UUID",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS project_name VARCHAR(255)",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS estimate_number VARCHAR(50)",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS roof_size_sqft INTEGER",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS total_amount DECIMAL(15,2)",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS converted_to_job BOOLEAN DEFAULT FALSE",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS job_id UUID",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS converted_at TIMESTAMP",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255)",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255)",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS property_address TEXT",
        "ALTER TABLE estimates ADD COLUMN IF NOT EXISTS roof_type VARCHAR(100)",
        
        # Fix jobs table
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS estimate_id UUID",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS title VARCHAR(255)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS start_date DATE",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS estimated_duration_days INTEGER",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS actual_duration_days INTEGER",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS total_cost DECIMAL(15,2)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS gross_profit DECIMAL(15,2)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS gross_margin_percent DECIMAL(5,2)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS sales_rep_id UUID",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS crew_id UUID",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS actual_hours DECIMAL(10,2)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS hourly_rate DECIMAL(10,2)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS material_cost DECIMAL(15,2)",
        
        # Fix invoices table
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS job_id UUID",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(50)",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS subtotal DECIMAL(15,2)",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS tax DECIMAL(15,2)",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total DECIMAL(15,2)",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS due_date DATE",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_terms VARCHAR(50)",
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS items JSONB",
        
        # Fix schedules table
        "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS schedulable_type VARCHAR(50)",
        "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS schedulable_id UUID",
        "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS crew_id UUID",
        "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS scheduled_date TIMESTAMP",
        "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS duration_hours INTEGER",
        "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS notes TEXT",
        "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS schedule_number VARCHAR(50)",
        
        # Fix service_tickets table
        "ALTER TABLE service_tickets ADD COLUMN IF NOT EXISTS customer_id UUID",
        "ALTER TABLE service_tickets ADD COLUMN IF NOT EXISTS job_id UUID",
        "ALTER TABLE service_tickets ADD COLUMN IF NOT EXISTS title VARCHAR(255)",
        "ALTER TABLE service_tickets ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE service_tickets ADD COLUMN IF NOT EXISTS priority VARCHAR(50)",
        "ALTER TABLE service_tickets ADD COLUMN IF NOT EXISTS type VARCHAR(50)",
        "ALTER TABLE service_tickets ADD COLUMN IF NOT EXISTS ticket_number VARCHAR(50)",
        
        # Fix warranties table
        "ALTER TABLE warranties ADD COLUMN IF NOT EXISTS job_id UUID",
        "ALTER TABLE warranties ADD COLUMN IF NOT EXISTS customer_id UUID",
        "ALTER TABLE warranties ADD COLUMN IF NOT EXISTS warranty_type VARCHAR(50)",
        "ALTER TABLE warranties ADD COLUMN IF NOT EXISTS duration_years INTEGER",
        "ALTER TABLE warranties ADD COLUMN IF NOT EXISTS expiration_date DATE",
        "ALTER TABLE warranties ADD COLUMN IF NOT EXISTS warranty_number VARCHAR(50)",
        
        # Fix workflows table
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS name VARCHAR(255)",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS category VARCHAR(100)",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS trigger_type VARCHAR(100)",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS trigger_config JSONB",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS conditions JSONB",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS actions JSONB",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS created_by VARCHAR(255)",
        
        # Fix inventory table
        "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS item_name VARCHAR(255)",
        "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS sku VARCHAR(100)",
        "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS quantity_on_hand INTEGER DEFAULT 0",
        "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS reorder_point INTEGER",
        "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS reorder_quantity INTEGER",
        "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS unit_price DECIMAL(10,2)",
        "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS last_cost DECIMAL(10,2)",
        "ALTER TABLE inventory ADD COLUMN IF NOT EXISTS primary_vendor_id UUID",
        
        # Fix crews table
        "ALTER TABLE crews ADD COLUMN IF NOT EXISTS type VARCHAR(50)",
        "ALTER TABLE crews ADD COLUMN IF NOT EXISTS capacity INTEGER",
        
        # Create missing tables if needed
        """CREATE TABLE IF NOT EXISTS estimate_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            estimate_id UUID,
            description TEXT,
            quantity DECIMAL(10,2),
            unit VARCHAR(50),
            unit_price DECIMAL(10,2),
            category VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS material_orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID,
            item_description TEXT,
            quantity DECIMAL(10,2),
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS follow_ups (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID,
            customer_id UUID,
            scheduled_date TIMESTAMP,
            type VARCHAR(50),
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS purchase_orders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            vendor_id VARCHAR(255),
            job_id UUID,
            status VARCHAR(50) DEFAULT 'pending',
            items JSONB,
            total_amount DECIMAL(15,2),
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS payment_plans (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            invoice_id UUID,
            installments INTEGER,
            interval VARCHAR(50),
            first_payment DECIMAL(15,2),
            recurring_payment DECIMAL(15,2),
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS payment_reminders (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            invoice_id UUID,
            days_offset INTEGER,
            type VARCHAR(50),
            status VARCHAR(50) DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS commissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID,
            job_id UUID,
            amount DECIMAL(15,2),
            rate DECIMAL(5,4),
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS quality_checklists (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID,
            items JSONB,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS inspections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID,
            type VARCHAR(50),
            scheduled_date TIMESTAMP,
            checklist_id UUID,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_type VARCHAR(100),
            entity_id UUID,
            scheduled_date TIMESTAMP,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS job_monitors (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID,
            check_interval VARCHAR(50),
            metrics JSONB,
            alert_thresholds JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS service_tracking (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_id UUID,
            status VARCHAR(50),
            tracking_enabled BOOLEAN DEFAULT TRUE,
            update_interval VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS quality_checks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_id UUID,
            check_type VARCHAR(50),
            results JSONB,
            passed BOOLEAN,
            checked_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS process_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            process_id VARCHAR(255),
            process_type VARCHAR(100),
            stage VARCHAR(100),
            data JSONB,
            timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS workflow_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workflow_id UUID,
            status VARCHAR(50),
            details JSONB,
            executed_at TIMESTAMP,
            started_at TIMESTAMP DEFAULT NOW(),
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )""",
        
        """CREATE TABLE IF NOT EXISTS job_materials (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID,
            material_id UUID,
            vendor_id UUID,
            quantity DECIMAL(10,2),
            unit_price DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT NOW()
        )"""
    ]
    
    success_count = 0
    error_count = 0
    
    for fix in fixes:
        try:
            cursor.execute(fix)
            conn.commit()
            if cursor.rowcount > 0 or "CREATE" in fix:
                logger.info(f"✅ Applied: {fix[:100]}...")
                success_count += 1
        except Exception as e:
            conn.rollback()
            if "already exists" not in str(e):
                logger.warning(f"⚠️ Error: {str(e)[:100]}")
                error_count += 1
    
    # Test the schema
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'leads' 
        AND table_schema = 'public'
    """)
    
    lead_columns = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"SCHEMA FIX COMPLETE")
    logger.info(f"✅ Successful fixes: {success_count}")
    logger.info(f"⚠️ Errors: {error_count}")
    logger.info(f"📊 Lead columns available: {len(lead_columns)}")
    logger.info(f"Columns: {', '.join(lead_columns[:10])}...")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    logger.info("🔧 Fixing complete ERP schema...")
    fix_schema()
    logger.info("\n✅ SCHEMA FIXES APPLIED!")