-- Create tables for CenterPoint data storage
-- These tables store REAL CenterPoint data only

-- Table for raw CenterPoint estimates (complex structure)
CREATE TABLE IF NOT EXISTS centerpoint_estimates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for CenterPoint sync status
CREATE TABLE IF NOT EXISTS centerpoint_sync_status (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    last_sync_at TIMESTAMP NOT NULL,
    records_synced INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for CenterPoint files/attachments
CREATE TABLE IF NOT EXISTS centerpoint_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(255),
    file_name VARCHAR(255),
    file_url TEXT,
    file_size BIGINT,
    mime_type VARCHAR(100),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for CenterPoint users/technicians
CREATE TABLE IF NOT EXISTS centerpoint_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(100),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for CenterPoint products/services
CREATE TABLE IF NOT EXISTS centerpoint_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    description TEXT,
    price_cents BIGINT,
    category VARCHAR(100),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for CenterPoint notes/communications
CREATE TABLE IF NOT EXISTS centerpoint_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(255),
    note_text TEXT,
    author VARCHAR(255),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for CenterPoint tickets/service requests
CREATE TABLE IF NOT EXISTS centerpoint_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    ticket_number VARCHAR(100),
    customer_id VARCHAR(255),
    subject VARCHAR(500),
    description TEXT,
    status VARCHAR(50),
    priority VARCHAR(50),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for CenterPoint photos
CREATE TABLE IF NOT EXISTS centerpoint_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(255),
    photo_url TEXT,
    caption TEXT,
    taken_at TIMESTAMP,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_centerpoint_estimates_external_id ON centerpoint_estimates(external_id);
CREATE INDEX IF NOT EXISTS idx_centerpoint_files_entity ON centerpoint_files(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_centerpoint_notes_entity ON centerpoint_notes(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_centerpoint_tickets_customer ON centerpoint_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_centerpoint_photos_entity ON centerpoint_photos(entity_type, entity_id);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Summary
SELECT 
    'CenterPoint Tables Created' as status,
    COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'centerpoint_%';