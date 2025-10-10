-- Inventory Management Tables
-- Task 40: Inventory management implementation

-- Categories for inventory items
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id UUID REFERENCES categories(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inventory items master
CREATE TABLE IF NOT EXISTS inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    item_type VARCHAR(20) NOT NULL, -- material, product, tool, equipment, supply, consumable, spare_part
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, discontinued, out_of_stock, backordered
    category_id UUID REFERENCES categories(id),
    unit_of_measure VARCHAR(20) NOT NULL, -- each, piece, box, case, pallet, pound, etc.
    cost_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    sale_price DECIMAL(10,2),
    min_stock INT DEFAULT 0,
    max_stock INT,
    reorder_point INT,
    reorder_quantity INT,
    lead_time_days INT,
    barcode VARCHAR(100),
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    specifications JSONB,
    image_url TEXT,
    last_movement_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inventory locations
CREATE TABLE IF NOT EXISTS inventory_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_code VARCHAR(50) UNIQUE NOT NULL,
    location_name VARCHAR(100) NOT NULL,
    location_type VARCHAR(20) NOT NULL, -- warehouse, store, truck, job_site, supplier, customer, in_transit
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    country VARCHAR(50),
    manager VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stock levels by location
CREATE TABLE IF NOT EXISTS inventory_stock (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    location_id UUID NOT NULL REFERENCES inventory_locations(id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 0,
    reserved_quantity INT DEFAULT 0,
    last_counted DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(item_id, location_id)
);

-- Stock movements
CREATE TABLE IF NOT EXISTS stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    movement_type VARCHAR(20) NOT NULL, -- purchase, sale, transfer, adjustment, return, damage, theft, production, consumption
    quantity INT NOT NULL,
    from_location_id UUID REFERENCES inventory_locations(id),
    to_location_id UUID REFERENCES inventory_locations(id),
    reference_type VARCHAR(30), -- purchase_order, sales_order, job, transfer, adjustment
    reference_id UUID,
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(12,2),
    performed_by VARCHAR(100),
    notes TEXT,
    movement_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    website VARCHAR(200),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(20),
    country VARCHAR(50),
    tax_id VARCHAR(50),
    payment_terms VARCHAR(50),
    credit_limit DECIMAL(12,2),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Item suppliers
CREATE TABLE IF NOT EXISTS item_suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES inventory_items(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    supplier_sku VARCHAR(100),
    cost DECIMAL(10,2),
    lead_time_days INT,
    min_order_quantity INT,
    is_primary BOOLEAN DEFAULT false,
    last_price_update DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(item_id, supplier_id)
);

-- Purchase orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id UUID NOT NULL REFERENCES suppliers(id),
    status VARCHAR(20) DEFAULT 'draft', -- draft, pending, approved, ordered, partially_received, received, cancelled
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_date DATE,
    received_date DATE,
    subtotal DECIMAL(12,2) NOT NULL DEFAULT 0,
    shipping_cost DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    payment_terms VARCHAR(50),
    ship_to_location_id UUID REFERENCES inventory_locations(id),
    notes TEXT,
    approved_by VARCHAR(100),
    approved_date TIMESTAMPTZ,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Purchase order items
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    quantity INT NOT NULL,
    received_quantity INT DEFAULT 0,
    unit_cost DECIMAL(10,2) NOT NULL,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    tax_rate DECIMAL(5,2) DEFAULT 0,
    line_total DECIMAL(12,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stock transfers
CREATE TABLE IF NOT EXISTS stock_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_number VARCHAR(50) UNIQUE NOT NULL,
    from_location_id UUID NOT NULL REFERENCES inventory_locations(id),
    to_location_id UUID NOT NULL REFERENCES inventory_locations(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_transit, completed, cancelled
    transfer_date DATE NOT NULL,
    completed_date DATE,
    transferred_by VARCHAR(100),
    received_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Stock transfer items
CREATE TABLE IF NOT EXISTS stock_transfer_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_id UUID NOT NULL REFERENCES stock_transfers(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    quantity INT NOT NULL,
    received_quantity INT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cycle counts
CREATE TABLE IF NOT EXISTS cycle_counts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID NOT NULL REFERENCES inventory_locations(id),
    count_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, in_progress, completed, verified, cancelled
    assigned_to VARCHAR(100),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    verified_by VARCHAR(100),
    verified_at TIMESTAMPTZ,
    variance_value DECIMAL(12,2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cycle count items
CREATE TABLE IF NOT EXISTS cycle_count_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    count_id UUID NOT NULL REFERENCES cycle_counts(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    expected_quantity INT,
    counted_quantity INT,
    variance INT,
    notes TEXT,
    counted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Serial numbers tracking
CREATE TABLE IF NOT EXISTS serial_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    location_id UUID REFERENCES inventory_locations(id),
    status VARCHAR(20) DEFAULT 'available', -- available, in_use, reserved, damaged, disposed
    purchase_order_id UUID REFERENCES purchase_orders(id),
    job_id UUID REFERENCES jobs(id),
    customer_id UUID REFERENCES customers(id),
    warranty_expiry DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_inventory_items_sku ON inventory_items(sku);
CREATE INDEX IF NOT EXISTS idx_inventory_items_status ON inventory_items(status);
CREATE INDEX IF NOT EXISTS idx_inventory_items_category_id ON inventory_items(category_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_barcode ON inventory_items(barcode);
CREATE INDEX IF NOT EXISTS idx_inventory_stock_item_id ON inventory_stock(item_id);
CREATE INDEX IF NOT EXISTS idx_inventory_stock_location_id ON inventory_stock(location_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_item_id ON stock_movements(item_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_movement_date ON stock_movements(movement_date);
CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_supplier_code ON suppliers(supplier_code);
CREATE INDEX IF NOT EXISTS idx_item_suppliers_item_id ON item_suppliers(item_id);
CREATE INDEX IF NOT EXISTS idx_item_suppliers_supplier_id ON item_suppliers(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_order_number ON purchase_orders(order_number);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier_id ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_purchase_order_items_purchase_order_id ON purchase_order_items(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_stock_transfers_transfer_number ON stock_transfers(transfer_number);
CREATE INDEX IF NOT EXISTS idx_stock_transfers_status ON stock_transfers(status);
CREATE INDEX IF NOT EXISTS idx_cycle_counts_location_id ON cycle_counts(location_id);
CREATE INDEX IF NOT EXISTS idx_cycle_counts_count_date ON cycle_counts(count_date);
CREATE INDEX IF NOT EXISTS idx_serial_numbers_serial_number ON serial_numbers(serial_number);
CREATE INDEX IF NOT EXISTS idx_serial_numbers_item_id ON serial_numbers(item_id);

-- Default categories
INSERT INTO categories (name, description)
VALUES
    ('Materials', 'Construction and building materials'),
    ('Tools', 'Hand and power tools'),
    ('Equipment', 'Heavy equipment and machinery'),
    ('Supplies', 'Office and general supplies'),
    ('Safety', 'Safety equipment and gear'),
    ('Parts', 'Spare parts and components')
ON CONFLICT (name) DO NOTHING;

-- Default locations
INSERT INTO inventory_locations (location_code, location_name, location_type)
VALUES
    ('WH-001', 'Main Warehouse', 'warehouse'),
    ('TRUCK-001', 'Service Truck 1', 'truck'),
    ('TRUCK-002', 'Service Truck 2', 'truck')
ON CONFLICT (location_code) DO NOTHING;

-- Function to update item last movement date
CREATE OR REPLACE FUNCTION update_item_last_movement()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE inventory_items
    SET last_movement_date = NOW()
    WHERE id = NEW.item_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for stock movements
CREATE TRIGGER update_item_movement_date
AFTER INSERT ON stock_movements
FOR EACH ROW
EXECUTE FUNCTION update_item_last_movement();

-- Function to check stock levels
CREATE OR REPLACE FUNCTION check_stock_levels(item_uuid UUID, location_uuid UUID, required_quantity INT)
RETURNS BOOLEAN AS $$
DECLARE
    available_quantity INT;
BEGIN
    SELECT quantity - reserved_quantity INTO available_quantity
    FROM inventory_stock
    WHERE item_id = item_uuid AND location_id = location_uuid;

    RETURN COALESCE(available_quantity, 0) >= required_quantity;
END;
$$ LANGUAGE plpgsql;

-- Function to reserve stock
CREATE OR REPLACE FUNCTION reserve_stock(item_uuid UUID, location_uuid UUID, reserve_quantity INT)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE inventory_stock
    SET reserved_quantity = reserved_quantity + reserve_quantity
    WHERE item_id = item_uuid
        AND location_id = location_uuid
        AND (quantity - reserved_quantity) >= reserve_quantity;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to release reserved stock
CREATE OR REPLACE FUNCTION release_stock(item_uuid UUID, location_uuid UUID, release_quantity INT)
RETURNS VOID AS $$
BEGIN
    UPDATE inventory_stock
    SET reserved_quantity = GREATEST(0, reserved_quantity - release_quantity)
    WHERE item_id = item_uuid AND location_id = location_uuid;
END;
$$ LANGUAGE plpgsql;

-- Update triggers
CREATE TRIGGER set_inventory_items_updated_at
BEFORE UPDATE ON inventory_items
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_inventory_locations_updated_at
BEFORE UPDATE ON inventory_locations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_inventory_stock_updated_at
BEFORE UPDATE ON inventory_stock
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_suppliers_updated_at
BEFORE UPDATE ON suppliers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_item_suppliers_updated_at
BEFORE UPDATE ON item_suppliers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_purchase_orders_updated_at
BEFORE UPDATE ON purchase_orders
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_stock_transfers_updated_at
BEFORE UPDATE ON stock_transfers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_cycle_counts_updated_at
BEFORE UPDATE ON cycle_counts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_serial_numbers_updated_at
BEFORE UPDATE ON serial_numbers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_categories_updated_at
BEFORE UPDATE ON categories
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();