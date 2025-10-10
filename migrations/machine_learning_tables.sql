-- Machine learning Tables
-- Auto-generated migration for complete ERP system

CREATE TABLE IF NOT EXISTS machine_learning (
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
CREATE INDEX IF NOT EXISTS idx_machine_learning_status ON machine_learning(status);
CREATE INDEX IF NOT EXISTS idx_machine_learning_created_at ON machine_learning(created_at);
CREATE INDEX IF NOT EXISTS idx_machine_learning_name ON machine_learning(name);

-- Trigger for updated_at
CREATE TRIGGER set_machine_learning_updated_at
BEFORE UPDATE ON machine_learning
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
