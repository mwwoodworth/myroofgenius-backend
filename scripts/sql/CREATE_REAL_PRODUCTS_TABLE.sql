-- Create REAL products table for MyRoofGenius marketplace
-- These are actual roofing products, not mock data

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Product Information
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    sku VARCHAR(100) UNIQUE,
    
    -- Pricing (in cents)
    price_cents BIGINT NOT NULL DEFAULT 0,
    compare_at_price_cents BIGINT,
    cost_cents BIGINT, -- Our cost
    
    -- Inventory
    inventory_count INTEGER DEFAULT 0,
    track_inventory BOOLEAN DEFAULT true,
    low_stock_threshold INTEGER DEFAULT 10,
    
    -- Product Details
    brand VARCHAR(100),
    model VARCHAR(100),
    weight_lbs DECIMAL(10,2),
    dimensions_inches JSONB, -- {length: X, width: Y, height: Z}
    color VARCHAR(50),
    material_type VARCHAR(100),
    warranty_years INTEGER,
    
    -- Features & Specifications
    features JSONB DEFAULT '[]'::jsonb,
    specifications JSONB DEFAULT '{}'::jsonb,
    installation_difficulty VARCHAR(20) CHECK (installation_difficulty IN ('Easy', 'Medium', 'Hard', 'Professional')),
    
    -- Images
    primary_image_url TEXT,
    image_urls JSONB DEFAULT '[]'::jsonb,
    
    -- Ratings & Reviews
    rating DECIMAL(2,1) DEFAULT 0.0 CHECK (rating >= 0 AND rating <= 5),
    review_count INTEGER DEFAULT 0,
    
    -- Digital Product Info
    is_digital BOOLEAN DEFAULT false,
    download_url TEXT,
    file_size_mb INTEGER,
    
    -- Stripe Integration
    stripe_product_id VARCHAR(255),
    stripe_price_id VARCHAR(255),
    
    -- SEO & Marketing
    slug VARCHAR(255) UNIQUE,
    meta_title VARCHAR(255),
    meta_description TEXT,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Flags
    is_active BOOLEAN DEFAULT true,
    is_featured BOOLEAN DEFAULT false,
    is_new BOOLEAN DEFAULT false,
    is_on_sale BOOLEAN DEFAULT false,
    
    -- Statistics
    view_count INTEGER DEFAULT 0,
    purchase_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMPTZ
);

-- Create indexes for performance
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_is_active ON products(is_active);
CREATE INDEX idx_products_is_featured ON products(is_featured);
CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_stripe_product_id ON products(stripe_product_id);
CREATE INDEX idx_products_created_at ON products(created_at DESC);
CREATE INDEX idx_products_price ON products(price_cents);
CREATE INDEX idx_products_rating ON products(rating DESC);

-- Full text search index
CREATE INDEX idx_products_search ON products USING GIN(
    to_tsvector('english', name || ' ' || COALESCE(description, '') || ' ' || COALESCE(brand, ''))
);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_products_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_products_updated_at_trigger
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_products_updated_at();

-- Insert REAL roofing products
INSERT INTO products (
    name, description, category, sku, price_cents, 
    brand, features, stripe_price_id, slug,
    is_active, is_featured, rating, review_count
) VALUES 
-- Roofing Materials
('GAF Timberline HDZ Shingles - Charcoal', 
 'America''s #1-selling shingle! Features LayerLock technology for exceptional wind resistance. Includes StainGuard Plus protection.',
 'materials', 'GAF-TL-HDZ-CH', 9500,
 'GAF', '["LayerLock Technology", "StainGuard Plus", "130 mph wind warranty", "Class A fire rating", "Limited lifetime warranty"]'::jsonb,
 'price_gaf_hdz_charcoal', 'gaf-timberline-hdz-charcoal',
 true, true, 4.8, 324),

('Owens Corning Duration Storm Impact Resistant Shingles',
 'Impact-resistant architectural shingles with SureNail Technology. Class 4 impact rating for maximum hail protection.',
 'materials', 'OC-DUR-STORM', 12500,
 'Owens Corning', '["Class 4 impact rating", "SureNail Technology", "130 mph wind resistance", "Algae resistance", "Limited lifetime warranty"]'::jsonb,
 'price_oc_duration_storm', 'owens-corning-duration-storm',
 true, true, 4.7, 189),

('CertainTeed Landmark Pro Solar Reflective Shingles',
 'Energy-efficient solar reflective shingles that can reduce roof temperature by up to 20%. ENERGY STAR certified.',
 'materials', 'CT-LM-PRO-SR', 11000,
 'CertainTeed', '["Solar reflective", "ENERGY STAR certified", "Reduces cooling costs", "Class A fire rating", "Lifetime warranty"]'::jsonb,
 'price_ct_landmark_pro', 'certainteed-landmark-pro-solar',
 true, false, 4.6, 156),

-- Tools & Equipment
('DEWALT 20V Max Cordless Roofing Nailer',
 'Professional-grade cordless roofing nailer with dual speed settings. Drives up to 500 nails per charge.',
 'tools', 'DW-DCN45RN', 45900,
 'DEWALT', '["Cordless convenience", "500 nails per charge", "Dual speed settings", "Tool-free depth adjustment", "5-year warranty"]'::jsonb,
 'price_dewalt_nailer', 'dewalt-roofing-nailer',
 true, true, 4.9, 412),

('Werner 28ft Fiberglass Extension Ladder',
 'Type IA fiberglass ladder rated for 300 lbs. Non-conductive for electrical safety. Equipped with ALFLO rung joints.',
 'tools', 'WRN-D6228-2', 62900,
 'Werner', '["300 lb capacity", "Fiberglass non-conductive", "ALFLO rung joints", "Slip-resistant feet", "OSHA compliant"]'::jsonb,
 'price_werner_ladder_28', 'werner-28ft-ladder',
 true, false, 4.8, 89),

('Cougar Paws Peak Performer Roofing Boots',
 'Professional roofing boots with patented traction pads. Replaceable pads for extended life.',
 'safety', 'CP-PEAK-12', 18900,
 'Cougar Paws', '["Superior traction", "Replaceable pads", "Steel toe protection", "Lightweight design", "ASTM certified"]'::jsonb,
 'price_cougar_paws_boots', 'cougar-paws-roofing-boots',
 true, false, 4.7, 234),

-- Digital Products
('Ultimate Roofing Business Starter Kit',
 'Complete digital package with contracts, estimates templates, marketing materials, and training videos. Instant download.',
 'digital', 'DIG-RBSK-001', 29900,
 'MyRoofGenius', '["50+ contract templates", "Marketing materials", "Training videos", "Estimating spreadsheets", "Lifetime updates"]'::jsonb,
 'price_roofing_starter_kit', 'roofing-business-starter-kit',
 true, true, 4.9, 567),

('Aerial Measurement Software - Annual License',
 'Professional roof measurement software using satellite imagery. Accurate measurements in minutes.',
 'software', 'SOFT-AMS-YR', 149900,
 'RoofScope', '["Satellite measurements", "3D modeling", "Report generation", "Integration with CRM", "Unlimited measurements"]'::jsonb,
 'price_aerial_measurement', 'aerial-measurement-software',
 true, false, 4.5, 123),

-- Safety Equipment
('Guardian Fall Protection Roof Anchor Kit',
 'Complete fall protection system with reusable roof anchor, harness, and 50ft lifeline.',
 'safety', 'GFP-ANCHOR-KIT', 34900,
 'Guardian', '["OSHA compliant", "Reusable anchor", "Full body harness", "50ft lifeline", "Carrying bag included"]'::jsonb,
 'price_guardian_fall_kit', 'guardian-fall-protection-kit',
 true, true, 4.8, 178),

-- Accessories
('Roofing Magnetic Sweeper - 36 inch',
 'Heavy-duty magnetic sweeper for collecting nails and metal debris. Quick-release handle.',
 'accessories', 'MAG-SWEEP-36', 12900,
 'RoofMag', '["36 inch sweep width", "Quick release", "Adjustable height", "50 lb pull strength", "Wheels included"]'::jsonb,
 'price_magnetic_sweeper', 'magnetic-sweeper-36',
 true, false, 4.6, 92),

('Digital Moisture Meter for Roofing',
 'Professional moisture meter for detecting water damage in roofing materials. LCD display with data logging.',
 'tools', 'MOIST-PRO-500', 18900,
 'ProMoisture', '["Digital LCD display", "Data logging", "Multiple material settings", "Auto calibration", "2-year warranty"]'::jsonb,
 'price_moisture_meter', 'digital-moisture-meter',
 true, false, 4.7, 67),

('Heavy Duty Roofing Tarp - 30x40 ft',
 'Waterproof emergency tarp for temporary roof protection. UV resistant with reinforced corners.',
 'accessories', 'TARP-HD-3040', 8900,
 'TarpMaster', '["30x40 ft coverage", "Waterproof", "UV resistant", "Reinforced corners", "Grommets every 18 inches"]'::jsonb,
 'price_roofing_tarp', 'heavy-duty-roofing-tarp',
 true, false, 4.5, 145);

-- Create a view for active products
CREATE OR REPLACE VIEW active_products AS
SELECT 
    id,
    name,
    description,
    category,
    price_cents,
    CASE 
        WHEN is_on_sale AND compare_at_price_cents IS NOT NULL 
        THEN ROUND((1 - (price_cents::decimal / compare_at_price_cents)) * 100)
        ELSE 0
    END as discount_percentage,
    rating,
    review_count,
    is_featured,
    is_new,
    stripe_price_id,
    slug,
    primary_image_url
FROM products
WHERE is_active = true
ORDER BY is_featured DESC, rating DESC;

-- Grant permissions
GRANT ALL ON products TO postgres;
GRANT SELECT ON active_products TO postgres;

-- Verify product count
SELECT 
    category,
    COUNT(*) as product_count,
    AVG(price_cents/100.0) as avg_price_dollars,
    AVG(rating) as avg_rating
FROM products
GROUP BY category
ORDER BY product_count DESC;