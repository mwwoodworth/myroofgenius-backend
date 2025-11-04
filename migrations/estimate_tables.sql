-- Estimate management tables
-- Handles estimates, line items, and activity tracking

-- Create estimates table
CREATE TABLE IF NOT EXISTS estimates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estimate_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID NOT NULL,
    job_site_id UUID,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    valid_until DATE,
    subtotal DECIMAL(10, 2) DEFAULT 0,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    tax_rate DECIMAL(5, 2) DEFAULT 0,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) DEFAULT 0,
    notes TEXT,
    terms TEXT,
    is_template BOOLEAN DEFAULT FALSE,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    viewed_at TIMESTAMP,
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    converted_at TIMESTAMP,
    converted_to_job_id UUID,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (converted_to_job_id) REFERENCES jobs(id) ON DELETE SET NULL
);

-- Create estimate line items table
CREATE TABLE IF NOT EXISTS estimate_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estimate_id UUID NOT NULL,
    description TEXT NOT NULL,
    quantity DECIMAL(10, 2) DEFAULT 1,
    unit VARCHAR(50) DEFAULT 'each',
    unit_price DECIMAL(10, 2) NOT NULL,
    discount_percent DECIMAL(5, 2) DEFAULT 0,
    tax_rate DECIMAL(5, 2) DEFAULT 0,
    line_total DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    notes TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE
);

-- Create estimate activity log
CREATE TABLE IF NOT EXISTS estimate_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estimate_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    user_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create estimate templates table
CREATE TABLE IF NOT EXISTS estimate_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    base_estimate_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    use_count INTEGER DEFAULT 0,
    created_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_estimate_id) REFERENCES estimates(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create estimate template items (predefined line items)
CREATE TABLE IF NOT EXISTS estimate_template_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL,
    description TEXT NOT NULL,
    default_quantity DECIMAL(10, 2) DEFAULT 1,
    unit VARCHAR(50) DEFAULT 'each',
    default_price DECIMAL(10, 2),
    category VARCHAR(100),
    is_optional BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES estimate_templates(id) ON DELETE CASCADE
);

-- Create estimate approvals table
CREATE TABLE IF NOT EXISTS estimate_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    estimate_id UUID NOT NULL,
    approved_by_name VARCHAR(255),
    approved_by_email VARCHAR(255),
    approval_token VARCHAR(255) UNIQUE,
    approval_date TIMESTAMP,
    ip_address VARCHAR(45),
    signature_data TEXT,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_estimates_customer_id ON estimates(customer_id);
CREATE INDEX IF NOT EXISTS idx_estimates_status ON estimates(status);
CREATE INDEX IF NOT EXISTS idx_estimates_estimate_number ON estimates(estimate_number);
CREATE INDEX IF NOT EXISTS idx_estimates_created_at ON estimates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_estimates_valid_until ON estimates(valid_until);
CREATE INDEX IF NOT EXISTS idx_estimates_is_template ON estimates(is_template);

CREATE INDEX IF NOT EXISTS idx_estimate_line_items_estimate_id ON estimate_line_items(estimate_id);
CREATE INDEX IF NOT EXISTS idx_estimate_activity_estimate_id ON estimate_activity(estimate_id);
CREATE INDEX IF NOT EXISTS idx_estimate_activity_created_at ON estimate_activity(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_estimate_templates_is_active ON estimate_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_estimate_template_items_template_id ON estimate_template_items(template_id);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON estimates TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON estimate_line_items TO authenticated;
GRANT SELECT, INSERT ON estimate_activity TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON estimate_templates TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON estimate_template_items TO authenticated;
GRANT SELECT, INSERT, UPDATE ON estimate_approvals TO authenticated;