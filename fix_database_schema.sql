-- Fix Database Schema Issues for WeatherCraft ERP
-- Date: 2025-09-14
-- Purpose: Add missing columns and fix schema issues

-- 1. Add missing unit_of_measure column to inventory_items
ALTER TABLE inventory_items
ADD COLUMN IF NOT EXISTS unit_of_measure VARCHAR(50) DEFAULT 'unit';

-- 2. Add missing columns for dashboard reports
ALTER TABLE dashboard_reports
ADD COLUMN IF NOT EXISTS data JSONB DEFAULT '{}';

-- 3. Create indexes for better performance on Jobs queries
CREATE INDEX IF NOT EXISTS idx_jobs_customer_id ON jobs(customer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- 4. Create indexes for better performance on Invoices queries
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON invoices(payment_status);
CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at DESC);

-- 5. Create indexes for inventory queries
CREATE INDEX IF NOT EXISTS idx_inventory_items_quantity ON inventory_items(quantity_on_hand);
CREATE INDEX IF NOT EXISTS idx_inventory_items_sku ON inventory_items(sku);

-- 6. Fix any timestamp columns that might be missing defaults
ALTER TABLE jobs ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE jobs ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE invoices ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE invoices ALTER COLUMN updated_at SET DEFAULT NOW();
ALTER TABLE estimates ALTER COLUMN created_at SET DEFAULT NOW();
ALTER TABLE estimates ALTER COLUMN updated_at SET DEFAULT NOW();

-- 7. Ensure proper foreign key relationships
ALTER TABLE jobs
ADD CONSTRAINT fk_jobs_customer
FOREIGN KEY (customer_id)
REFERENCES customers(id)
ON DELETE CASCADE
ON UPDATE CASCADE
DEFERRABLE INITIALLY DEFERRED;

-- 8. Add missing columns for estimates
ALTER TABLE estimates
ADD COLUMN IF NOT EXISTS tax_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS discount_percent DECIMAL(5,2) DEFAULT 0;

-- Fix estimate_items missing columns (Critical for v30.0)
ALTER TABLE estimate_items ADD COLUMN IF NOT EXISTS item_order INTEGER DEFAULT 1;
ALTER TABLE estimate_items ADD COLUMN IF NOT EXISTS item_type VARCHAR(50) DEFAULT 'standard';

-- 9. Verify and report completion
DO $$
BEGIN
    RAISE NOTICE 'Database schema fixes completed successfully';
    RAISE NOTICE 'Added unit_of_measure to inventory_items';
    RAISE NOTICE 'Added indexes for performance optimization';
    RAISE NOTICE 'Fixed timestamp defaults';
    RAISE NOTICE 'Added foreign key constraints';
END $$;