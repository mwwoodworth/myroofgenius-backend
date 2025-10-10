-- Warehouse Management Tables
-- Task 42: Warehouse management implementation

-- Warehouses table
CREATE TABLE IF NOT EXISTS warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    warehouse_type VARCHAR(30) NOT NULL, -- main, distribution, cold_storage, bonded, cross_dock, fulfillment_center, dropship, other
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, maintenance, closed
    address VARCHAR(500) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(100) DEFAULT 'USA',
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    total_area_sqft DECIMAL(12,2),
    storage_area_sqft DECIMAL(12,2),
    office_area_sqft DECIMAL(12,2),
    dock_doors INT DEFAULT 0,
    floor_levels INT DEFAULT 1,
    ceiling_height_ft DECIMAL(5,2),
    temperature_controlled BOOLEAN DEFAULT false,
    min_temperature DECIMAL(5,2),
    max_temperature DECIMAL(5,2),
    humidity_controlled BOOLEAN DEFAULT false,
    min_humidity DECIMAL(5,2),
    max_humidity DECIMAL(5,2),
    security_level VARCHAR(20), -- basic, standard, high, maximum
    operating_hours JSONB, -- {monday: {open: "08:00", close: "17:00"}, ...}
    manager_name VARCHAR(100),
    manager_email VARCHAR(255),
    manager_phone VARCHAR(30),
    features JSONB, -- ["24/7 access", "CCTV", "sprinkler system", etc]
    certifications JSONB, -- ["ISO 9001", "HAZMAT certified", etc]
    insurance_policy VARCHAR(100),
    insurance_expiry DATE,
    lease_expiry DATE,
    monthly_cost DECIMAL(12,2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Warehouse zones
CREATE TABLE IF NOT EXISTS warehouse_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    zone_code VARCHAR(50) NOT NULL,
    zone_name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(30) NOT NULL, -- receiving, storage, picking, packing, shipping, returns, quarantine, hazmat, cold, other
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, maintenance
    area_sqft DECIMAL(10,2),
    height_ft DECIMAL(5,2),
    temperature_zone VARCHAR(20), -- ambient, cold, frozen, heated
    target_temperature DECIMAL(5,2),
    humidity_controlled BOOLEAN DEFAULT false,
    target_humidity DECIMAL(5,2),
    max_weight_capacity_lbs DECIMAL(12,2),
    current_weight_lbs DECIMAL(12,2),
    storage_type VARCHAR(30), -- pallet_rack, shelving, floor_stack, mezzanine, cantilever, flow_rack, other
    pick_strategy VARCHAR(20), -- FIFO, LIFO, FEFO, zone, batch
    restricted_access BOOLEAN DEFAULT false,
    access_requirements TEXT,
    location_prefix VARCHAR(20), -- Prefix for locations in this zone
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(warehouse_id, zone_code)
);

-- Storage locations
CREATE TABLE IF NOT EXISTS warehouse_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    zone_id UUID REFERENCES warehouse_zones(id) ON DELETE CASCADE,
    location_code VARCHAR(50) NOT NULL,
    location_type VARCHAR(30) NOT NULL, -- bin, pallet, shelf, floor, bulk, dock, staging, other
    status VARCHAR(20) DEFAULT 'available', -- available, occupied, reserved, blocked, maintenance
    aisle VARCHAR(10),
    bay VARCHAR(10),
    level VARCHAR(10),
    position VARCHAR(10),
    width_inches DECIMAL(8,2),
    depth_inches DECIMAL(8,2),
    height_inches DECIMAL(8,2),
    max_weight_lbs DECIMAL(10,2),
    current_weight_lbs DECIMAL(10,2) DEFAULT 0,
    volume_cubic_ft DECIMAL(10,3),
    occupied_volume_cubic_ft DECIMAL(10,3) DEFAULT 0,
    is_pickface BOOLEAN DEFAULT false,
    pick_sequence INT,
    replenishment_min INT,
    replenishment_max INT,
    abc_classification CHAR(1), -- A, B, C, D
    velocity_class VARCHAR(10), -- fast, medium, slow
    last_count_date DATE,
    last_movement_date DATE,
    restricted_items JSONB, -- List of restricted item categories
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(warehouse_id, location_code)
);

-- Inventory in warehouse
CREATE TABLE IF NOT EXISTS warehouse_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    location_id UUID REFERENCES warehouse_locations(id),
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    quantity DECIMAL(12,3) NOT NULL DEFAULT 0,
    reserved_quantity DECIMAL(12,3) DEFAULT 0,
    available_quantity DECIMAL(12,3) GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    unit_of_measure VARCHAR(20) NOT NULL,
    lot_number VARCHAR(50),
    serial_numbers JSONB, -- Array of serial numbers if tracked
    expiry_date DATE,
    manufacture_date DATE,
    received_date DATE,
    cost_per_unit DECIMAL(12,4),
    total_value DECIMAL(12,2) GENERATED ALWAYS AS (quantity * cost_per_unit) STORED,
    condition VARCHAR(20) DEFAULT 'good', -- new, good, damaged, expired, quarantine
    quality_status VARCHAR(20) DEFAULT 'passed', -- passed, failed, pending, na
    hold_status VARCHAR(20), -- quality_hold, customer_hold, finance_hold, null
    hold_reason TEXT,
    owner_type VARCHAR(20) DEFAULT 'owned', -- owned, consigned, customer_owned
    owner_reference VARCHAR(100),
    last_cycle_count DATE,
    cycle_count_variance DECIMAL(12,3),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(warehouse_id, location_id, item_id, lot_number)
);

-- Receiving orders
CREATE TABLE IF NOT EXISTS receiving_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    supplier_name VARCHAR(200) NOT NULL,
    supplier_id VARCHAR(100),
    purchase_order_number VARCHAR(100),
    expected_date DATE,
    actual_date TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, cancelled, partial
    priority VARCHAR(10) DEFAULT 'normal', -- low, normal, high, urgent
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    freight_cost DECIMAL(10,2),
    total_units_expected INT,
    total_units_received INT,
    total_pallets INT,
    total_weight_lbs DECIMAL(12,2),
    receiving_type VARCHAR(20), -- standard, cross_dock, blind, direct_putaway
    inspection_required BOOLEAN DEFAULT false,
    inspection_status VARCHAR(20), -- not_required, pending, passed, failed, partial
    documents JSONB, -- Array of document references
    receiving_notes TEXT,
    quality_notes TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    received_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Receiving order items
CREATE TABLE IF NOT EXISTS receiving_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receiving_order_id UUID NOT NULL REFERENCES receiving_orders(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    expected_quantity DECIMAL(12,3) NOT NULL,
    received_quantity DECIMAL(12,3) DEFAULT 0,
    unit_of_measure VARCHAR(20) NOT NULL,
    lot_number VARCHAR(50),
    expiry_date DATE,
    serial_numbers JSONB,
    putaway_location_id UUID REFERENCES warehouse_locations(id),
    condition VARCHAR(20) DEFAULT 'good',
    quality_status VARCHAR(20),
    damage_notes TEXT,
    discrepancy_notes TEXT,
    unit_cost DECIMAL(12,4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Picking orders
CREATE TABLE IF NOT EXISTS picking_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    customer_name VARCHAR(200),
    customer_id VARCHAR(100),
    sales_order_number VARCHAR(100),
    order_type VARCHAR(20) NOT NULL, -- sales, transfer, sample, replacement
    priority VARCHAR(10) DEFAULT 'normal', -- low, normal, high, urgent
    status VARCHAR(20) DEFAULT 'pending', -- pending, assigned, in_progress, completed, cancelled, on_hold
    pick_method VARCHAR(20) DEFAULT 'single', -- single, batch, wave, zone, cluster
    wave_number VARCHAR(50),
    batch_number VARCHAR(50),
    zone_id UUID REFERENCES warehouse_zones(id),
    requested_date DATE,
    due_date DATE,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    picker_id VARCHAR(100),
    picker_name VARCHAR(100),
    total_items INT,
    total_units DECIMAL(12,3),
    picked_items INT DEFAULT 0,
    picked_units DECIMAL(12,3) DEFAULT 0,
    pick_list_printed BOOLEAN DEFAULT false,
    labels_printed BOOLEAN DEFAULT false,
    special_instructions TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Picking order items
CREATE TABLE IF NOT EXISTS picking_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    picking_order_id UUID NOT NULL REFERENCES picking_orders(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    location_id UUID REFERENCES warehouse_locations(id),
    requested_quantity DECIMAL(12,3) NOT NULL,
    picked_quantity DECIMAL(12,3) DEFAULT 0,
    unit_of_measure VARCHAR(20) NOT NULL,
    lot_number VARCHAR(50),
    serial_numbers JSONB,
    pick_sequence INT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, picked, short, substituted, cancelled
    shortage_reason TEXT,
    substitution_item_id UUID REFERENCES inventory_items(id),
    picked_at TIMESTAMPTZ,
    picked_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Shipping orders
CREATE TABLE IF NOT EXISTS shipping_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    picking_order_id UUID REFERENCES picking_orders(id),
    customer_name VARCHAR(200),
    customer_id VARCHAR(100),
    ship_to_name VARCHAR(200),
    ship_to_address VARCHAR(500),
    ship_to_city VARCHAR(100),
    ship_to_state VARCHAR(50),
    ship_to_postal_code VARCHAR(20),
    ship_to_country VARCHAR(100),
    ship_to_phone VARCHAR(30),
    ship_to_email VARCHAR(255),
    carrier VARCHAR(100),
    service_level VARCHAR(50), -- standard, express, overnight, freight
    tracking_number VARCHAR(100),
    freight_cost DECIMAL(10,2),
    insurance_value DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending', -- pending, ready, shipped, delivered, returned, lost
    ship_date DATE,
    expected_delivery DATE,
    actual_delivery TIMESTAMPTZ,
    total_packages INT,
    total_weight_lbs DECIMAL(12,2),
    total_volume_cubic_ft DECIMAL(10,3),
    packing_list_printed BOOLEAN DEFAULT false,
    labels_printed BOOLEAN DEFAULT false,
    customs_docs JSONB,
    special_instructions TEXT,
    delivery_confirmation VARCHAR(100),
    signature_required BOOLEAN DEFAULT false,
    notes TEXT,
    packed_by VARCHAR(100),
    shipped_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inventory transfers
CREATE TABLE IF NOT EXISTS inventory_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_number VARCHAR(50) UNIQUE NOT NULL,
    from_warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    to_warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_transit, completed, cancelled, partial
    transfer_type VARCHAR(20) NOT NULL, -- internal, intercompany, customer, return
    priority VARCHAR(10) DEFAULT 'normal',
    requested_date DATE,
    ship_date DATE,
    receive_date DATE,
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    freight_cost DECIMAL(10,2),
    total_items INT,
    total_units DECIMAL(12,3),
    total_value DECIMAL(12,2),
    reason TEXT,
    approval_status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    initiated_by VARCHAR(100),
    received_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transfer items
CREATE TABLE IF NOT EXISTS transfer_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transfer_id UUID NOT NULL REFERENCES inventory_transfers(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    from_location_id UUID REFERENCES warehouse_locations(id),
    to_location_id UUID REFERENCES warehouse_locations(id),
    requested_quantity DECIMAL(12,3) NOT NULL,
    shipped_quantity DECIMAL(12,3) DEFAULT 0,
    received_quantity DECIMAL(12,3) DEFAULT 0,
    unit_of_measure VARCHAR(20) NOT NULL,
    lot_number VARCHAR(50),
    serial_numbers JSONB,
    unit_cost DECIMAL(12,4),
    total_value DECIMAL(12,2),
    condition VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inventory adjustments
CREATE TABLE IF NOT EXISTS inventory_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adjustment_number VARCHAR(50) UNIQUE NOT NULL,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    adjustment_type VARCHAR(30) NOT NULL, -- cycle_count, physical_count, damage, expiry, theft, correction, other
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, completed, rejected
    reason_code VARCHAR(50),
    reason_description TEXT NOT NULL,
    total_items INT,
    total_value_change DECIMAL(12,2),
    initiated_by VARCHAR(100) NOT NULL,
    initiated_at TIMESTAMPTZ DEFAULT NOW(),
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    completed_by VARCHAR(100),
    completed_at TIMESTAMPTZ,
    approval_notes TEXT,
    supporting_docs JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Adjustment items
CREATE TABLE IF NOT EXISTS adjustment_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adjustment_id UUID NOT NULL REFERENCES inventory_adjustments(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    location_id UUID REFERENCES warehouse_locations(id),
    lot_number VARCHAR(50),
    previous_quantity DECIMAL(12,3) NOT NULL,
    new_quantity DECIMAL(12,3) NOT NULL,
    quantity_change DECIMAL(12,3) GENERATED ALWAYS AS (new_quantity - previous_quantity) STORED,
    unit_of_measure VARCHAR(20) NOT NULL,
    unit_cost DECIMAL(12,4),
    value_change DECIMAL(12,2),
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cycle counts
CREATE TABLE IF NOT EXISTS cycle_counts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    count_number VARCHAR(50) UNIQUE NOT NULL,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    count_type VARCHAR(20) NOT NULL, -- cycle, physical, spot, annual
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, in_progress, completed, cancelled
    scheduled_date DATE NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    zone_id UUID REFERENCES warehouse_zones(id),
    abc_class CHAR(1), -- Count specific ABC class
    location_range_start VARCHAR(50),
    location_range_end VARCHAR(50),
    total_locations INT,
    counted_locations INT DEFAULT 0,
    total_items INT,
    counted_items INT DEFAULT 0,
    variance_count INT DEFAULT 0,
    variance_value DECIMAL(12,2) DEFAULT 0,
    accuracy_percentage DECIMAL(5,2),
    counter_name VARCHAR(100),
    verifier_name VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cycle count items
CREATE TABLE IF NOT EXISTS cycle_count_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_count_id UUID NOT NULL REFERENCES cycle_counts(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    location_id UUID REFERENCES warehouse_locations(id),
    system_quantity DECIMAL(12,3) NOT NULL,
    counted_quantity DECIMAL(12,3),
    variance_quantity DECIMAL(12,3),
    unit_of_measure VARCHAR(20) NOT NULL,
    lot_number VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending', -- pending, counted, verified, adjusted
    counted_at TIMESTAMPTZ,
    counted_by VARCHAR(100),
    verified_at TIMESTAMPTZ,
    verified_by VARCHAR(100),
    adjustment_id UUID REFERENCES inventory_adjustments(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Putaway tasks
CREATE TABLE IF NOT EXISTS putaway_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_number VARCHAR(50) UNIQUE NOT NULL,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    receiving_order_id UUID REFERENCES receiving_orders(id),
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    quantity DECIMAL(12,3) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    from_location_id UUID REFERENCES warehouse_locations(id),
    to_location_id UUID REFERENCES warehouse_locations(id),
    lot_number VARCHAR(50),
    priority VARCHAR(10) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending', -- pending, assigned, in_progress, completed, cancelled
    assigned_to VARCHAR(100),
    assigned_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    completion_time_seconds INT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Replenishment tasks
CREATE TABLE IF NOT EXISTS replenishment_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_number VARCHAR(50) UNIQUE NOT NULL,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    item_id UUID NOT NULL REFERENCES inventory_items(id),
    from_location_id UUID REFERENCES warehouse_locations(id),
    to_location_id UUID REFERENCES warehouse_locations(id),
    quantity DECIMAL(12,3) NOT NULL,
    unit_of_measure VARCHAR(20) NOT NULL,
    trigger_type VARCHAR(20) NOT NULL, -- min_level, empty, scheduled, manual
    priority VARCHAR(10) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to VARCHAR(100),
    assigned_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Warehouse performance metrics
CREATE TABLE IF NOT EXISTS warehouse_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    metric_date DATE NOT NULL,
    orders_received INT DEFAULT 0,
    orders_shipped INT DEFAULT 0,
    units_received DECIMAL(12,3) DEFAULT 0,
    units_shipped DECIMAL(12,3) DEFAULT 0,
    picking_accuracy DECIMAL(5,2),
    inventory_accuracy DECIMAL(5,2),
    order_fulfillment_rate DECIMAL(5,2),
    on_time_shipping_rate DECIMAL(5,2),
    space_utilization DECIMAL(5,2),
    labor_hours DECIMAL(10,2),
    labor_productivity DECIMAL(10,2),
    damage_rate DECIMAL(5,2),
    return_rate DECIMAL(5,2),
    cycle_time_hours DECIMAL(8,2),
    dwell_time_days DECIMAL(8,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(warehouse_id, metric_date)
);

-- Activity log
CREATE TABLE IF NOT EXISTS warehouse_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    activity_type VARCHAR(50) NOT NULL, -- receiving, picking, shipping, transfer, adjustment, cycle_count
    reference_type VARCHAR(50), -- order, item, location
    reference_id UUID,
    description TEXT NOT NULL,
    performed_by VARCHAR(100),
    quantity DECIMAL(12,3),
    from_location VARCHAR(50),
    to_location VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_warehouses_status ON warehouses(status);
CREATE INDEX IF NOT EXISTS idx_warehouses_type ON warehouses(warehouse_type);
CREATE INDEX IF NOT EXISTS idx_warehouse_zones_warehouse_id ON warehouse_zones(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_zones_type ON warehouse_zones(zone_type);
CREATE INDEX IF NOT EXISTS idx_warehouse_locations_warehouse_id ON warehouse_locations(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_locations_zone_id ON warehouse_locations(zone_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_locations_status ON warehouse_locations(status);
CREATE INDEX IF NOT EXISTS idx_warehouse_locations_code ON warehouse_locations(location_code);
CREATE INDEX IF NOT EXISTS idx_warehouse_inventory_warehouse_id ON warehouse_inventory(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_inventory_location_id ON warehouse_inventory(location_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_inventory_item_id ON warehouse_inventory(item_id);
CREATE INDEX IF NOT EXISTS idx_warehouse_inventory_lot ON warehouse_inventory(lot_number);
CREATE INDEX IF NOT EXISTS idx_receiving_orders_warehouse_id ON receiving_orders(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_receiving_orders_status ON receiving_orders(status);
CREATE INDEX IF NOT EXISTS idx_receiving_orders_expected_date ON receiving_orders(expected_date);
CREATE INDEX IF NOT EXISTS idx_picking_orders_warehouse_id ON picking_orders(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_picking_orders_status ON picking_orders(status);
CREATE INDEX IF NOT EXISTS idx_picking_orders_due_date ON picking_orders(due_date);
CREATE INDEX IF NOT EXISTS idx_shipping_orders_warehouse_id ON shipping_orders(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_shipping_orders_status ON shipping_orders(status);
CREATE INDEX IF NOT EXISTS idx_transfers_from_warehouse ON inventory_transfers(from_warehouse_id);
CREATE INDEX IF NOT EXISTS idx_transfers_to_warehouse ON inventory_transfers(to_warehouse_id);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON inventory_transfers(status);
CREATE INDEX IF NOT EXISTS idx_adjustments_warehouse_id ON inventory_adjustments(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_adjustments_status ON inventory_adjustments(status);
CREATE INDEX IF NOT EXISTS idx_cycle_counts_warehouse_id ON cycle_counts(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_cycle_counts_status ON cycle_counts(status);
CREATE INDEX IF NOT EXISTS idx_putaway_tasks_warehouse_id ON putaway_tasks(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_putaway_tasks_status ON putaway_tasks(status);
CREATE INDEX IF NOT EXISTS idx_replenishment_tasks_warehouse_id ON replenishment_tasks(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_replenishment_tasks_status ON replenishment_tasks(status);
CREATE INDEX IF NOT EXISTS idx_activity_log_warehouse_id ON warehouse_activity_log(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON warehouse_activity_log(created_at);

-- Functions for warehouse operations
CREATE OR REPLACE FUNCTION calculate_location_utilization(location_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    location_record RECORD;
    utilization DECIMAL;
BEGIN
    SELECT * INTO location_record FROM warehouse_locations WHERE id = location_id;

    IF location_record.volume_cubic_ft > 0 THEN
        utilization := (location_record.occupied_volume_cubic_ft / location_record.volume_cubic_ft) * 100;
    ELSE
        utilization := 0;
    END IF;

    RETURN ROUND(utilization, 2);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_warehouse_utilization(warehouse_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    total_locations INT;
    occupied_locations INT;
    utilization DECIMAL;
BEGIN
    SELECT COUNT(*) INTO total_locations
    FROM warehouse_locations
    WHERE warehouse_id = warehouse_id;

    SELECT COUNT(*) INTO occupied_locations
    FROM warehouse_locations
    WHERE warehouse_id = warehouse_id AND status = 'occupied';

    IF total_locations > 0 THEN
        utilization := (occupied_locations::DECIMAL / total_locations) * 100;
    ELSE
        utilization := 0;
    END IF;

    RETURN ROUND(utilization, 2);
END;
$$ LANGUAGE plpgsql;

-- Trigger to update warehouse activity log
CREATE OR REPLACE FUNCTION log_warehouse_activity()
RETURNS TRIGGER AS $$
BEGIN
    -- Log different activities based on the table
    IF TG_TABLE_NAME = 'receiving_orders' AND TG_OP = 'UPDATE' THEN
        IF OLD.status != NEW.status AND NEW.status = 'completed' THEN
            INSERT INTO warehouse_activity_log (
                warehouse_id, activity_type, reference_type, reference_id,
                description, performed_by
            ) VALUES (
                NEW.warehouse_id, 'receiving', 'order', NEW.id,
                'Receiving order ' || NEW.order_number || ' completed',
                NEW.received_by
            );
        END IF;
    END IF;

    IF TG_TABLE_NAME = 'shipping_orders' AND TG_OP = 'UPDATE' THEN
        IF OLD.status != NEW.status AND NEW.status = 'shipped' THEN
            INSERT INTO warehouse_activity_log (
                warehouse_id, activity_type, reference_type, reference_id,
                description, performed_by
            ) VALUES (
                NEW.warehouse_id, 'shipping', 'order', NEW.id,
                'Shipping order ' || NEW.order_number || ' shipped',
                NEW.shipped_by
            );
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER log_receiving_activity
AFTER UPDATE ON receiving_orders
FOR EACH ROW
EXECUTE FUNCTION log_warehouse_activity();

CREATE TRIGGER log_shipping_activity
AFTER UPDATE ON shipping_orders
FOR EACH ROW
EXECUTE FUNCTION log_warehouse_activity();

-- Update triggers for updated_at
CREATE TRIGGER set_warehouses_updated_at
BEFORE UPDATE ON warehouses
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_warehouse_zones_updated_at
BEFORE UPDATE ON warehouse_zones
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_warehouse_locations_updated_at
BEFORE UPDATE ON warehouse_locations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_warehouse_inventory_updated_at
BEFORE UPDATE ON warehouse_inventory
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_receiving_orders_updated_at
BEFORE UPDATE ON receiving_orders
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_picking_orders_updated_at
BEFORE UPDATE ON picking_orders
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_shipping_orders_updated_at
BEFORE UPDATE ON shipping_orders
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_transfers_updated_at
BEFORE UPDATE ON inventory_transfers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_adjustments_updated_at
BEFORE UPDATE ON inventory_adjustments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_cycle_counts_updated_at
BEFORE UPDATE ON cycle_counts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();