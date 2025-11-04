-- WeatherCraft ERP Inventory & Procurement Schema
-- Phase 3: Inventory & Procurement

-- ============================================================================
-- WAREHOUSE & LOCATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_code VARCHAR(20) UNIQUE NOT NULL,
    location_name VARCHAR(100) NOT NULL,
    location_type VARCHAR(50), -- warehouse, yard, truck, job-site
    
    -- Address
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    location GEOMETRY(POINT, 4326),
    
    -- Capacity
    storage_capacity_sqft INTEGER,
    
    -- Management
    manager_id UUID REFERENCES users(id),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INVENTORY MANAGEMENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Item Identification
    item_code VARCHAR(50) UNIQUE NOT NULL,
    barcode VARCHAR(100),
    
    -- Description
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    
    -- Specifications
    manufacturer VARCHAR(100),
    manufacturer_part_number VARCHAR(100),
    model VARCHAR(100),
    color VARCHAR(50),
    size VARCHAR(50),
    
    -- Units
    unit_of_measure VARCHAR(20) NOT NULL, -- each, box, bundle, square, roll, gallon
    units_per_package INTEGER DEFAULT 1,
    
    -- Inventory Tracking
    track_inventory BOOLEAN DEFAULT TRUE,
    is_serialized BOOLEAN DEFAULT FALSE,
    is_lot_tracked BOOLEAN DEFAULT FALSE,
    
    -- Costing
    cost_method VARCHAR(20) DEFAULT 'average', -- average, fifo, lifo, specific
    standard_cost DECIMAL(12,4),
    last_cost DECIMAL(12,4),
    average_cost DECIMAL(12,4),
    
    -- Pricing
    list_price DECIMAL(12,4),
    
    -- Reorder
    reorder_point DECIMAL(12,3),
    reorder_quantity DECIMAL(12,3),
    lead_time_days INTEGER,
    safety_stock DECIMAL(12,3),
    
    -- Classification
    item_type VARCHAR(50), -- material, tool, consumable, equipment
    is_active BOOLEAN DEFAULT TRUE,
    is_purchasable BOOLEAN DEFAULT TRUE,
    is_sellable BOOLEAN DEFAULT TRUE,
    
    -- Accounting
    expense_account VARCHAR(50),
    revenue_account VARCHAR(50),
    
    -- Weight & Dimensions
    weight_lbs DECIMAL(10,3),
    length_inches DECIMAL(10,2),
    width_inches DECIMAL(10,2),
    height_inches DECIMAL(10,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inventory Levels by Location
CREATE TABLE IF NOT EXISTS inventory_levels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    location_id UUID NOT NULL REFERENCES locations(id),
    
    -- Quantities
    quantity_on_hand DECIMAL(12,3) DEFAULT 0,
    quantity_available DECIMAL(12,3) DEFAULT 0, -- on_hand - committed
    quantity_committed DECIMAL(12,3) DEFAULT 0,
    quantity_on_order DECIMAL(12,3) DEFAULT 0,
    
    -- Reorder for this location
    location_reorder_point DECIMAL(12,3),
    location_reorder_qty DECIMAL(12,3),
    
    -- Bin Location
    bin_location VARCHAR(50),
    
    -- Last Activity
    last_received_date DATE,
    last_counted_date DATE,
    last_sold_date DATE,
    
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(item_id, location_id)
);

-- Inventory Transactions
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Item & Location
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    location_id UUID NOT NULL REFERENCES locations(id),
    from_location_id UUID REFERENCES locations(id), -- For transfers
    to_location_id UUID REFERENCES locations(id), -- For transfers
    
    -- Transaction Details
    transaction_type VARCHAR(50) NOT NULL, -- receipt, issue, transfer, adjustment, count
    transaction_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Quantities
    quantity DECIMAL(12,3) NOT NULL,
    unit_cost DECIMAL(12,4),
    total_cost DECIMAL(12,2),
    
    -- Reference
    reference_type VARCHAR(50), -- purchase_order, job, transfer, adjustment
    reference_id UUID,
    
    -- Lot/Serial
    lot_number VARCHAR(50),
    serial_number VARCHAR(100),
    expiration_date DATE,
    
    -- Notes
    notes TEXT,
    reason VARCHAR(100), -- For adjustments
    
    -- User
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- VENDORS
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    dba_name VARCHAR(255),
    
    -- Contact
    primary_contact VARCHAR(100),
    phone VARCHAR(20),
    fax VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    country VARCHAR(2) DEFAULT 'US',
    
    -- Payment
    payment_terms VARCHAR(50), -- net30, net60, 2/10net30, cod
    credit_limit DECIMAL(12,2),
    account_number VARCHAR(50), -- Our account with them
    
    -- Tax
    tax_id VARCHAR(50),
    is_1099_vendor BOOLEAN DEFAULT FALSE,
    
    -- Categorization
    vendor_type VARCHAR(50), -- supplier, subcontractor, service
    categories TEXT[], -- roofing, tools, safety, etc.
    
    -- Performance
    rating DECIMAL(3,2), -- 1-5 scale
    on_time_delivery_rate DECIMAL(5,2),
    quality_rating DECIMAL(3,2),
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, suspended, blacklisted
    
    -- Insurance
    insurance_expiry DATE,
    license_expiry DATE,
    
    -- Notes
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vendor Contacts
CREATE TABLE IF NOT EXISTS vendor_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_id UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    department VARCHAR(50),
    
    phone VARCHAR(20),
    mobile VARCHAR(20),
    email VARCHAR(255),
    
    is_primary BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vendor Products (Their Catalog)
CREATE TABLE IF NOT EXISTS vendor_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    inventory_item_id UUID REFERENCES inventory_items(id),
    
    -- Vendor's Info
    vendor_part_number VARCHAR(100),
    vendor_description VARCHAR(500),
    
    -- Pricing
    list_price DECIMAL(12,4),
    our_cost DECIMAL(12,4),
    
    -- Units
    vendor_uom VARCHAR(20),
    uom_conversion_factor DECIMAL(10,4) DEFAULT 1,
    
    -- Ordering
    minimum_order_qty DECIMAL(12,3),
    order_multiple DECIMAL(12,3),
    lead_time_days INTEGER,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(vendor_id, vendor_part_number)
);

-- ============================================================================
-- PURCHASE ORDERS
-- ============================================================================

CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_number VARCHAR(20) UNIQUE NOT NULL,
    
    -- Vendor
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    
    -- Dates
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_date DATE,
    
    -- Ship To
    ship_to_location_id UUID REFERENCES locations(id),
    ship_to_address VARCHAR(500),
    ship_to_job_id UUID REFERENCES jobs(id),
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft', -- draft, submitted, confirmed, partial, received, cancelled
    
    -- Amounts
    subtotal DECIMAL(12,2) DEFAULT 0,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    shipping_amount DECIMAL(12,2) DEFAULT 0,
    other_amount DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(12,2) DEFAULT 0,
    
    -- Terms
    payment_terms VARCHAR(50),
    shipping_terms VARCHAR(50),
    
    -- Approval
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    approval_notes TEXT,
    
    -- Submission
    submitted_at TIMESTAMPTZ,
    submitted_by UUID REFERENCES users(id),
    confirmation_number VARCHAR(50),
    
    -- Notes
    notes TEXT,
    internal_notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Purchase Order Line Items
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    po_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    
    -- Item
    line_number INTEGER NOT NULL,
    inventory_item_id UUID REFERENCES inventory_items(id),
    
    -- Description
    item_code VARCHAR(50),
    description VARCHAR(500) NOT NULL,
    
    -- Quantities
    quantity_ordered DECIMAL(12,3) NOT NULL,
    quantity_received DECIMAL(12,3) DEFAULT 0,
    quantity_invoiced DECIMAL(12,3) DEFAULT 0,
    unit_of_measure VARCHAR(20),
    
    -- Pricing
    unit_cost DECIMAL(12,4) NOT NULL,
    total_cost DECIMAL(12,2),
    
    -- Delivery
    expected_date DATE,
    
    -- Job Costing
    job_id UUID REFERENCES jobs(id),
    cost_code VARCHAR(50),
    
    -- Status
    status VARCHAR(50) DEFAULT 'open', -- open, partial, received, cancelled
    
    -- Notes
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Purchase Order Receipts
CREATE TABLE IF NOT EXISTS purchase_receipts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_number VARCHAR(20) UNIQUE NOT NULL,
    po_id UUID REFERENCES purchase_orders(id),
    
    -- Receipt Info
    receipt_date DATE NOT NULL DEFAULT CURRENT_DATE,
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    
    -- Reference
    packing_slip_number VARCHAR(50),
    vendor_invoice_number VARCHAR(50),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, posted, cancelled
    
    -- Totals
    total_items INTEGER DEFAULT 0,
    total_quantity DECIMAL(12,3) DEFAULT 0,
    
    -- User
    received_by UUID REFERENCES users(id),
    posted_at TIMESTAMPTZ,
    
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Receipt Line Items
CREATE TABLE IF NOT EXISTS purchase_receipt_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL REFERENCES purchase_receipts(id) ON DELETE CASCADE,
    po_item_id UUID REFERENCES purchase_order_items(id),
    
    -- Item
    inventory_item_id UUID REFERENCES inventory_items(id),
    description VARCHAR(500),
    
    -- Quantities
    quantity_received DECIMAL(12,3) NOT NULL,
    quantity_accepted DECIMAL(12,3),
    quantity_rejected DECIMAL(12,3) DEFAULT 0,
    
    -- Location
    location_id UUID REFERENCES locations(id),
    bin_location VARCHAR(50),
    
    -- Lot/Serial
    lot_number VARCHAR(50),
    serial_number VARCHAR(100),
    expiration_date DATE,
    
    -- Quality
    inspection_status VARCHAR(50), -- pending, passed, failed
    rejection_reason VARCHAR(255),
    
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vendor Invoices
CREATE TABLE IF NOT EXISTS vendor_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number VARCHAR(50) NOT NULL,
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    
    -- Dates
    invoice_date DATE NOT NULL,
    due_date DATE,
    
    -- Reference
    po_id UUID REFERENCES purchase_orders(id),
    receipt_id UUID REFERENCES purchase_receipts(id),
    
    -- Amounts
    subtotal DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(12,2) DEFAULT 0,
    shipping_amount DECIMAL(12,2) DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL,
    amount_paid DECIMAL(12,2) DEFAULT 0,
    balance_due DECIMAL(12,2),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, paid, cancelled
    
    -- Approval
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    
    -- Payment
    payment_terms VARCHAR(50),
    paid_date DATE,
    payment_method VARCHAR(50),
    check_number VARCHAR(50),
    
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(vendor_id, invoice_number)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Inventory Indexes
CREATE INDEX idx_inventory_items_code ON inventory_items(item_code);
CREATE INDEX idx_inventory_items_category ON inventory_items(category);
CREATE INDEX idx_inventory_levels_item ON inventory_levels(item_id);
CREATE INDEX idx_inventory_levels_location ON inventory_levels(location_id);
CREATE INDEX idx_inventory_transactions_item ON inventory_transactions(item_id);
CREATE INDEX idx_inventory_transactions_date ON inventory_transactions(transaction_date DESC);

-- Vendor Indexes
CREATE INDEX idx_vendors_status ON vendors(status);
CREATE INDEX idx_vendor_products_vendor ON vendor_products(vendor_id);
CREATE INDEX idx_vendor_products_item ON vendor_products(inventory_item_id);

-- Purchase Order Indexes
CREATE INDEX idx_purchase_orders_vendor ON purchase_orders(vendor_id);
CREATE INDEX idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX idx_purchase_orders_date ON purchase_orders(order_date DESC);
CREATE INDEX idx_po_items_po ON purchase_order_items(po_id);
CREATE INDEX idx_po_items_job ON purchase_order_items(job_id);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Update inventory levels on transaction
CREATE OR REPLACE FUNCTION update_inventory_levels() RETURNS trigger AS $$
DECLARE
    v_multiplier INTEGER;
BEGIN
    -- Determine multiplier based on transaction type
    CASE NEW.transaction_type
        WHEN 'receipt' THEN v_multiplier := 1;
        WHEN 'issue' THEN v_multiplier := -1;
        WHEN 'adjustment' THEN 
            IF NEW.quantity > 0 THEN 
                v_multiplier := 1;
            ELSE 
                v_multiplier := -1;
            END IF;
        ELSE v_multiplier := 0;
    END CASE;
    
    -- Update inventory level
    INSERT INTO inventory_levels (item_id, location_id, quantity_on_hand, quantity_available)
    VALUES (NEW.item_id, NEW.location_id, NEW.quantity * v_multiplier, NEW.quantity * v_multiplier)
    ON CONFLICT (item_id, location_id)
    DO UPDATE SET
        quantity_on_hand = inventory_levels.quantity_on_hand + (NEW.quantity * v_multiplier),
        quantity_available = inventory_levels.quantity_available + (NEW.quantity * v_multiplier),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_inventory_levels_trigger
    AFTER INSERT ON inventory_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_inventory_levels();

-- Calculate PO totals
CREATE OR REPLACE FUNCTION calculate_po_totals() RETURNS trigger AS $$
DECLARE
    v_subtotal DECIMAL(12,2);
BEGIN
    -- Calculate subtotal from line items
    SELECT COALESCE(SUM(total_cost), 0)
    INTO v_subtotal
    FROM purchase_order_items
    WHERE po_id = COALESCE(NEW.po_id, OLD.po_id);
    
    -- Update PO totals
    UPDATE purchase_orders
    SET 
        subtotal = v_subtotal,
        total_amount = v_subtotal + tax_amount + shipping_amount + other_amount,
        updated_at = NOW()
    WHERE id = COALESCE(NEW.po_id, OLD.po_id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_po_totals_trigger
    AFTER INSERT OR UPDATE OR DELETE ON purchase_order_items
    FOR EACH ROW
    EXECUTE FUNCTION calculate_po_totals();

-- Generate PO numbers
CREATE OR REPLACE FUNCTION generate_po_number() RETURNS trigger AS $$
BEGIN
    IF NEW.po_number IS NULL THEN
        NEW.po_number := 'PO-' || TO_CHAR(NOW(), 'YYYY') || '-' || LPAD(nextval('po_number_seq')::text, 5, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE IF NOT EXISTS po_number_seq START 1;

CREATE TRIGGER generate_po_number_trigger
    BEFORE INSERT ON purchase_orders
    FOR EACH ROW
    EXECUTE FUNCTION generate_po_number();