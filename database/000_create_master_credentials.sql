-- Create the master_credentials table
CREATE TABLE IF NOT EXISTS master_credentials (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'GENERAL',
    service VARCHAR(100) DEFAULT 'SYSTEM',
    is_sensitive BOOLEAN DEFAULT TRUE,
    is_valid BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_rotated TIMESTAMPTZ,
    last_validated TIMESTAMPTZ
);

-- Create a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_master_credentials_updated_at
    BEFORE UPDATE ON master_credentials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
