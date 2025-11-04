-- Customer feedback Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS customer_feedback (
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
CREATE INDEX IF NOT EXISTS idx_customer_feedback_status ON customer_feedback(status);
CREATE INDEX IF NOT EXISTS idx_customer_feedback_created_at ON customer_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_customer_feedback_name ON customer_feedback(name);

-- Trigger for updated_at
CREATE TRIGGER set_customer_feedback_updated_at
BEFORE UPDATE ON customer_feedback
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
