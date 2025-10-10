-- Admin dashboard Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS admin_dashboard (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    data JSONB,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_admin_dashboard_status ON admin_dashboard(status);
CREATE INDEX IF NOT EXISTS idx_admin_dashboard_created_at ON admin_dashboard(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_dashboard_name ON admin_dashboard(name);

-- Trigger for updated_at
CREATE TRIGGER set_admin_dashboard_updated_at
BEFORE UPDATE ON admin_dashboard
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
