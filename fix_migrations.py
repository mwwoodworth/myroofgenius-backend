#!/usr/bin/env python3
"""
Fix and run all migrations properly
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

def fix_missing_tables(conn):
    """Create any missing tables that had errors"""
    
    with conn.cursor() as cursor:
        # Fix missing tables from migration errors
        
        # Locations table (needed by many others)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            location_code VARCHAR(20) UNIQUE NOT NULL,
            location_name VARCHAR(100) NOT NULL,
            location_type VARCHAR(50),
            address VARCHAR(500),
            city VARCHAR(100),
            state VARCHAR(2),
            zipcode VARCHAR(10),
            storage_capacity_sqft INTEGER,
            manager_id UUID REFERENCES users(id),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Properties table (referenced but may not exist)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            customer_id UUID REFERENCES customers(id),
            address VARCHAR(500),
            city VARCHAR(100),
            state VARCHAR(2),
            zipcode VARCHAR(10),
            property_type VARCHAR(50),
            roof_type VARCHAR(50),
            roof_age_years INTEGER,
            square_footage INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Job phases table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_phases (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            job_id UUID REFERENCES jobs(id),
            phase_code VARCHAR(20),
            phase_name VARCHAR(100),
            sequence_number INTEGER,
            status VARCHAR(50) DEFAULT 'pending',
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Job tasks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_tasks (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            job_id UUID REFERENCES jobs(id),
            phase_id UUID REFERENCES job_phases(id),
            task_name VARCHAR(255),
            description TEXT,
            assigned_to UUID REFERENCES users(id),
            status VARCHAR(50) DEFAULT 'pending',
            priority VARCHAR(20) DEFAULT 'normal',
            due_date DATE,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Job documents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_documents (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            job_id UUID REFERENCES jobs(id),
            document_type VARCHAR(50),
            document_name VARCHAR(255),
            file_path VARCHAR(500),
            uploaded_by UUID REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Job costs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_costs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            job_id UUID REFERENCES jobs(id),
            cost_type VARCHAR(50),
            description VARCHAR(255),
            quantity DECIMAL(12,3),
            unit_cost DECIMAL(12,4),
            total_cost DECIMAL(12,2),
            cost_date DATE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Estimate items table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS estimate_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            estimate_id UUID REFERENCES estimates(id),
            line_number INTEGER,
            description TEXT,
            quantity DECIMAL(12,3),
            unit VARCHAR(50),
            unit_price DECIMAL(12,4),
            total_price DECIMAL(12,2),
            category VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Change orders table (referenced in migrations)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS change_orders (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            job_id UUID REFERENCES jobs(id),
            change_order_number VARCHAR(50),
            description TEXT,
            amount DECIMAL(12,2),
            status VARCHAR(50) DEFAULT 'pending',
            requested_by UUID REFERENCES users(id),
            approved_by UUID REFERENCES users(id),
            approved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Crews table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crews (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            crew_name VARCHAR(100) NOT NULL,
            crew_type VARCHAR(50),
            crew_code VARCHAR(20) UNIQUE,
            foreman_id UUID REFERENCES users(id),
            max_jobs_per_day INTEGER DEFAULT 1,
            specialties TEXT[],
            certifications TEXT[],
            home_location_id UUID REFERENCES locations(id),
            is_active BOOLEAN DEFAULT TRUE,
            status VARCHAR(50) DEFAULT 'available',
            efficiency_rating DECIMAL(3,2),
            safety_rating DECIMAL(3,2),
            quality_rating DECIMAL(3,2),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Crew members table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crew_members (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            crew_id UUID REFERENCES crews(id) ON DELETE SET NULL,
            user_id UUID NOT NULL REFERENCES users(id),
            role VARCHAR(50),
            employee_id VARCHAR(50),
            hire_date DATE,
            pay_type VARCHAR(20),
            pay_rate DECIMAL(10,2),
            overtime_rate DECIMAL(10,2),
            skills TEXT[],
            certifications JSONB,
            license_number VARCHAR(50),
            license_expiry DATE,
            safety_training_date DATE,
            drug_test_date DATE,
            background_check_date DATE,
            is_active BOOLEAN DEFAULT TRUE,
            available_days INTEGER DEFAULT 63,
            total_hours_worked DECIMAL(10,2) DEFAULT 0,
            jobs_completed INTEGER DEFAULT 0,
            performance_score DECIMAL(3,2),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Schedules table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            schedulable_type VARCHAR(50) NOT NULL,
            schedulable_id UUID NOT NULL,
            crew_id UUID REFERENCES crews(id),
            assigned_users UUID[],
            scheduled_date DATE NOT NULL,
            start_time TIME,
            end_time TIME,
            duration_hours DECIMAL(5,2),
            is_recurring BOOLEAN DEFAULT FALSE,
            recurrence_rule JSONB,
            recurrence_end_date DATE,
            parent_schedule_id UUID REFERENCES schedules(id),
            status VARCHAR(50) DEFAULT 'scheduled',
            priority VARCHAR(20) DEFAULT 'normal',
            location_name VARCHAR(255),
            address VARCHAR(500),
            route_order INTEGER,
            travel_time_minutes INTEGER,
            distance_miles DECIMAL(6,2),
            weather_dependent BOOLEAN DEFAULT TRUE,
            weather_status VARCHAR(50),
            dispatch_notes TEXT,
            crew_notes TEXT,
            actual_start TIMESTAMPTZ,
            actual_end TIMESTAMPTZ,
            completed_by UUID REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            created_by UUID REFERENCES users(id),
            CONSTRAINT valid_schedule_times CHECK (end_time > start_time)
        )
        """)
        
        # Daily field reports
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_field_reports (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            report_date DATE NOT NULL,
            job_id UUID NOT NULL REFERENCES jobs(id),
            crew_id UUID REFERENCES crews(id),
            weather_conditions VARCHAR(100),
            temperature_high INTEGER,
            temperature_low INTEGER,
            precipitation BOOLEAN DEFAULT FALSE,
            wind_speed INTEGER,
            work_description TEXT,
            areas_completed TEXT,
            percent_complete DECIMAL(5,2),
            materials_used JSONB,
            equipment_used JSONB,
            equipment_issues TEXT,
            safety_incidents INTEGER DEFAULT 0,
            safety_notes TEXT,
            toolbox_talk_topic VARCHAR(255),
            quality_issues TEXT,
            inspections_completed BOOLEAN DEFAULT FALSE,
            photo_count INTEGER DEFAULT 0,
            foreman_signature TEXT,
            signed_at TIMESTAMPTZ,
            status VARCHAR(50) DEFAULT 'draft',
            submitted_at TIMESTAMPTZ,
            approved_by UUID REFERENCES users(id),
            approved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            created_by UUID REFERENCES users(id)
        )
        """)
        
        # Time entries
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_entries (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id),
            crew_id UUID REFERENCES crews(id),
            job_id UUID REFERENCES jobs(id),
            task_id UUID REFERENCES job_tasks(id),
            entry_date DATE NOT NULL,
            start_time TIMESTAMPTZ NOT NULL,
            end_time TIMESTAMPTZ,
            break_minutes INTEGER DEFAULT 0,
            total_hours DECIMAL(5,2),
            work_type VARCHAR(50),
            billable BOOLEAN DEFAULT TRUE,
            description TEXT,
            status VARCHAR(50) DEFAULT 'pending',
            approved_by UUID REFERENCES users(id),
            approved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Equipment table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            equipment_number VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(100),
            make VARCHAR(100),
            model VARCHAR(100),
            serial_number VARCHAR(100),
            year INTEGER,
            ownership_type VARCHAR(50),
            purchase_date DATE,
            purchase_price DECIMAL(12,2),
            current_location VARCHAR(255),
            assigned_to_crew UUID REFERENCES crews(id),
            assigned_to_user UUID REFERENCES users(id),
            last_service_date DATE,
            next_service_date DATE,
            service_interval_days INTEGER,
            service_interval_hours DECIMAL(10,2),
            current_hours DECIMAL(10,2),
            status VARCHAR(50) DEFAULT 'available',
            condition VARCHAR(50) DEFAULT 'good',
            insurance_policy VARCHAR(100),
            insurance_expiry DATE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Equipment usage
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_usage (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            equipment_id UUID NOT NULL REFERENCES equipment(id),
            job_id UUID REFERENCES jobs(id),
            used_by UUID REFERENCES users(id),
            crew_id UUID REFERENCES crews(id),
            checkout_time TIMESTAMPTZ NOT NULL,
            checkin_time TIMESTAMPTZ,
            usage_hours DECIMAL(8,2),
            start_hours DECIMAL(10,2),
            end_hours DECIMAL(10,2),
            checkout_condition VARCHAR(50),
            checkin_condition VARCHAR(50),
            damage_noted TEXT,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Quality checklists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_checklists (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            job_id UUID NOT NULL REFERENCES jobs(id),
            phase_id UUID REFERENCES job_phases(id),
            checklist_type VARCHAR(50),
            checklist_date DATE NOT NULL,
            inspector_id UUID NOT NULL REFERENCES users(id),
            checklist_items JSONB NOT NULL,
            passed_items INTEGER DEFAULT 0,
            failed_items INTEGER DEFAULT 0,
            total_items INTEGER DEFAULT 0,
            overall_status VARCHAR(20),
            overall_score DECIMAL(5,2),
            requires_reinspection BOOLEAN DEFAULT FALSE,
            reinspection_date DATE,
            corrective_actions TEXT,
            customer_signature TEXT,
            customer_signed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Missing inventory tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_levels (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            item_id UUID NOT NULL REFERENCES inventory_items(id),
            location_id UUID NOT NULL REFERENCES locations(id),
            quantity_on_hand DECIMAL(12,3) DEFAULT 0,
            quantity_available DECIMAL(12,3) DEFAULT 0,
            quantity_committed DECIMAL(12,3) DEFAULT 0,
            quantity_on_order DECIMAL(12,3) DEFAULT 0,
            location_reorder_point DECIMAL(12,3),
            location_reorder_qty DECIMAL(12,3),
            bin_location VARCHAR(50),
            last_received_date DATE,
            last_counted_date DATE,
            last_sold_date DATE,
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(item_id, location_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendor_products (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            vendor_id UUID NOT NULL REFERENCES vendors(id),
            inventory_item_id UUID REFERENCES inventory_items(id),
            vendor_part_number VARCHAR(100),
            vendor_description VARCHAR(500),
            list_price DECIMAL(12,4),
            our_cost DECIMAL(12,4),
            vendor_uom VARCHAR(20),
            uom_conversion_factor DECIMAL(10,4) DEFAULT 1,
            minimum_order_qty DECIMAL(12,3),
            order_multiple DECIMAL(12,3),
            lead_time_days INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            last_updated TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(vendor_id, vendor_part_number)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            po_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
            line_number INTEGER NOT NULL,
            inventory_item_id UUID REFERENCES inventory_items(id),
            item_code VARCHAR(50),
            description VARCHAR(500) NOT NULL,
            quantity_ordered DECIMAL(12,3) NOT NULL,
            quantity_received DECIMAL(12,3) DEFAULT 0,
            quantity_invoiced DECIMAL(12,3) DEFAULT 0,
            unit_of_measure VARCHAR(20),
            unit_cost DECIMAL(12,4) NOT NULL,
            total_cost DECIMAL(12,2),
            expected_date DATE,
            job_id UUID REFERENCES jobs(id),
            cost_code VARCHAR(50),
            status VARCHAR(50) DEFAULT 'open',
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Missing financial tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            line_number INTEGER NOT NULL,
            item_type VARCHAR(50),
            item_code VARCHAR(50),
            description TEXT NOT NULL,
            quantity DECIMAL(12,3) DEFAULT 1,
            unit_of_measure VARCHAR(20),
            unit_price DECIMAL(12,4) NOT NULL,
            total_price DECIMAL(12,2),
            taxable BOOLEAN DEFAULT TRUE,
            tax_amount DECIMAL(12,2) DEFAULT 0,
            cost_code VARCHAR(50),
            phase_code VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_applications (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
            invoice_id UUID NOT NULL REFERENCES invoices(id),
            amount_applied DECIMAL(12,2) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(payment_id, invoice_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ar_aging (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            aging_date DATE NOT NULL DEFAULT CURRENT_DATE,
            customer_id UUID NOT NULL REFERENCES customers(id),
            current_amount DECIMAL(12,2) DEFAULT 0,
            days_30 DECIMAL(12,2) DEFAULT 0,
            days_60 DECIMAL(12,2) DEFAULT 0,
            days_90 DECIMAL(12,2) DEFAULT 0,
            days_120_plus DECIMAL(12,2) DEFAULT 0,
            total_due DECIMAL(12,2) DEFAULT 0,
            oldest_invoice_date DATE,
            invoice_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(aging_date, customer_id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS commissions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id),
            source_type VARCHAR(50),
            source_id UUID,
            commission_date DATE NOT NULL,
            base_amount DECIMAL(12,2) NOT NULL,
            commission_rate DECIMAL(5,2) NOT NULL,
            commission_amount DECIMAL(12,2) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            paid_date DATE,
            payment_method VARCHAR(50),
            check_number VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS warranties (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            warranty_number VARCHAR(20) UNIQUE NOT NULL,
            job_id UUID REFERENCES jobs(id),
            customer_id UUID NOT NULL REFERENCES customers(id),
            property_id UUID REFERENCES properties(id),
            warranty_type VARCHAR(50),
            coverage_description TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            duration_years INTEGER,
            terms_conditions TEXT,
            exclusions TEXT,
            is_transferable BOOLEAN DEFAULT FALSE,
            transfer_fee DECIMAL(12,2),
            registration_date DATE,
            registered_by UUID REFERENCES users(id),
            manufacturer_name VARCHAR(100),
            manufacturer_warranty_id VARCHAR(100),
            status VARCHAR(50) DEFAULT 'active',
            claims_count INTEGER DEFAULT 0,
            total_claim_amount DECIMAL(12,2) DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS warranty_claims (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            claim_number VARCHAR(20) UNIQUE NOT NULL,
            warranty_id UUID NOT NULL REFERENCES warranties(id),
            claim_date DATE NOT NULL DEFAULT CURRENT_DATE,
            issue_description TEXT NOT NULL,
            inspection_date DATE,
            inspector_id UUID REFERENCES users(id),
            inspection_notes TEXT,
            status VARCHAR(50) DEFAULT 'submitted',
            decision_date DATE,
            decision_by UUID REFERENCES users(id),
            denial_reason TEXT,
            resolution_type VARCHAR(50),
            estimated_cost DECIMAL(12,2),
            actual_cost DECIMAL(12,2),
            service_ticket_id UUID REFERENCES service_tickets(id),
            documentation JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            created_by UUID REFERENCES users(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_schedules (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            property_id UUID NOT NULL REFERENCES properties(id),
            customer_id UUID NOT NULL REFERENCES customers(id),
            maintenance_type VARCHAR(100),
            frequency VARCHAR(50),
            last_service_date DATE,
            next_service_date DATE,
            contract_start DATE,
            contract_end DATE,
            contract_value DECIMAL(12,2),
            auto_schedule BOOLEAN DEFAULT TRUE,
            days_advance_notice INTEGER DEFAULT 7,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        # Automation tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS automation_rules (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            rule_type VARCHAR(50),
            entity_type VARCHAR(50),
            conditions JSONB NOT NULL,
            actions JSONB NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            priority INTEGER DEFAULT 100,
            execution_count INTEGER DEFAULT 0,
            last_executed TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_queue (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            recipient_type VARCHAR(50),
            recipient_id UUID,
            recipient_email VARCHAR(255),
            recipient_phone VARCHAR(20),
            notification_type VARCHAR(50),
            template_id UUID REFERENCES email_templates(id),
            subject VARCHAR(500),
            message TEXT,
            data JSONB,
            scheduled_for TIMESTAMPTZ DEFAULT NOW(),
            status VARCHAR(50) DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            sent_at TIMESTAMPTZ,
            error_message TEXT,
            provider_response JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            contract_number VARCHAR(50) UNIQUE NOT NULL,
            customer_id UUID NOT NULL REFERENCES customers(id),
            job_id UUID REFERENCES jobs(id),
            estimate_id UUID REFERENCES estimates(id),
            contract_type VARCHAR(50),
            title VARCHAR(255),
            effective_date DATE,
            expiration_date DATE,
            contract_value DECIMAL(12,2),
            payment_terms TEXT,
            scope_of_work TEXT,
            exclusions TEXT,
            terms_conditions TEXT,
            customer_signature_status VARCHAR(50) DEFAULT 'pending',
            customer_signed_at TIMESTAMPTZ,
            customer_signature_ip VARCHAR(50),
            company_signature_status VARCHAR(50) DEFAULT 'pending',
            company_signed_at TIMESTAMPTZ,
            company_signed_by UUID REFERENCES users(id),
            docusign_envelope_id VARCHAR(100),
            docusign_status VARCHAR(50),
            status VARCHAR(50) DEFAULT 'draft',
            is_renewable BOOLEAN DEFAULT FALSE,
            renewal_terms TEXT,
            renewal_notice_days INTEGER,
            document_id UUID REFERENCES documents(id),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            created_by UUID REFERENCES users(id)
        )
        """)
        
        logger.info("✅ All missing tables created")

def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        # Ensure extensions
        with conn.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        
        # Fix all missing tables
        fix_missing_tables(conn)
        
        # Verify table count
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            count = cursor.fetchone()[0]
            logger.info(f"\nTotal tables: {count}")
        
        logger.info("✅ All database structures complete!")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()